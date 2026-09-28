/**
 * Portable AQI Recorder — V3 main board (Rev B) firmware
 * ESP32-C3-MINI-1 + SEN5x or SEN6x + optional SCD4x + 2.4" ST7789 TFT
 *
 * - Detects the particulate sensor at boot: SEN50/54/55 on J3 or SEN63C/65/66/68 on J4,
 *   plus an SCD40/SCD41/SCD43 on the CO2 island if one has been fitted.
 * - Home screen with AQI, PM, CO2, VOC, NOx, temperature and humidity; full-screen charts.
 * - Three buttons: LEFT/RIGHT move the selection, OK opens/closes a chart,
 *   holding OK starts/stops recording. OK on the gear cycles the backlight brightness.
 * - Streams samples over BLE (same service as V2, so the V2 web app works).
 * - Reads battery % from the battery board (PWM on J2 -> GPIO21).
 * - Logs over native USB (the same USB-C port used for programming).
 */

#include <Arduino.h>
#include <NimBLEDevice.h>
#include <Preferences.h>
#include <Wire.h>

#include "BatteryPwmReader.h"
#include "buttons.h"
#include "data_buffer.h"
#include "display.h"
#include "sensors.h"

// ---------------------------------------------------------------------------
//  Board pins (main board Rev B; see hardware/rev-b/main/README.md)
// ---------------------------------------------------------------------------

static constexpr uint8_t PIN_I2C_SDA = 0;
static constexpr uint8_t PIN_I2C_SCL = 1;
static constexpr uint8_t PIN_BAT_PWM = 21;   // through R34; R33 pull-up. Never start UART0 TX here.
// Display (DC 10, CS 4, SCK 5, MOSI 6, RST 7) is set in platformio.ini; backlight GPIO3 in display.cpp.
// GPIO20 is the e-paper BUSY input on J6 (e-paper builds only; not used by this TFT firmware).

// ---------------------------------------------------------------------------
//  State
// ---------------------------------------------------------------------------

static const unsigned long MEASUREMENT_INTERVAL_MS = 1000;
static const unsigned long DISPLAY_UPDATE_INTERVAL_MS = 33;
static unsigned long lastMeasurementMs = 0;
static unsigned long lastDisplayUpdateMs = 0;

static ScreenMode screenMode = ScreenMode::HOME;
static DataField cursorField = DataField::AQI;
static const DataField navSequence[] = {
  DataField::AQI, DataField::PM2_5, DataField::CO2, DataField::VOC_INDEX,
  DataField::NOX_INDEX, DataField::TEMPERATURE, DataField::HUMIDITY, DataField::SETTINGS
};
static constexpr int NAV_COUNT = sizeof(navSequence) / sizeof(navSequence[0]);
static int navIndex = 0;

static SensorSample latestSample = {};
static unsigned long recordingStartMs = 0;
static DataBuffer dataBuffer;

static const uint8_t BRIGHTNESS_LEVELS[] = {100, 70, 40, 15};
static uint8_t brightnessIndex = 0;
static Preferences prefs;

static int batteryPercent = -1;

// ---------------------------------------------------------------------------
//  US EPA AQI (unchanged from V2)
// ---------------------------------------------------------------------------

static int calcAQILinear(float Ih, float Il, float Ch, float Cl, float C) {
  float value = ((Ih - Il) / (Ch - Cl)) * (C - Cl) + Il;
  // Preserve the uint16_t sample/BLE format without wrapping extreme values.
  return value >= 65535.0f ? 65535 : (int)round(value);
}

int aqiFromPM25(float pm25) {
  if (!isfinite(pm25) || pm25 < 0.0f) return -1;
  pm25 = floorf(pm25 * 10.0f) / 10.0f;
  if (pm25 <= 9.0f)   return calcAQILinear(50, 0, 9.0f, 0.0f, pm25);
  if (pm25 <= 35.4f)  return calcAQILinear(100, 51, 35.4f, 9.1f, pm25);
  if (pm25 <= 55.4f)  return calcAQILinear(150, 101, 55.4f, 35.5f, pm25);
  if (pm25 <= 125.4f) return calcAQILinear(200, 151, 125.4f, 55.5f, pm25);
  if (pm25 <= 225.4f) return calcAQILinear(300, 201, 225.4f, 125.5f, pm25);
  // EPA: above 500, continue the 301–500 band's slope.
  return calcAQILinear(500, 301, 325.4f, 225.5f, pm25);
}

int aqiFromPM10(float pm10) {
  if (!isfinite(pm10) || pm10 < 0.0f) return -1;
  pm10 = floorf(pm10);
  if (pm10 <= 54.0f)  return calcAQILinear(50, 0, 54.0f, 0.0f, pm10);
  if (pm10 <= 154.0f) return calcAQILinear(100, 51, 154.0f, 55.0f, pm10);
  if (pm10 <= 254.0f) return calcAQILinear(150, 101, 254.0f, 155.0f, pm10);
  if (pm10 <= 354.0f) return calcAQILinear(200, 151, 354.0f, 255.0f, pm10);
  if (pm10 <= 424.0f) return calcAQILinear(300, 201, 424.0f, 355.0f, pm10);
  return calcAQILinear(500, 301, 604.0f, 425.0f, pm10);
}

const char *aqiCategory(int aqi) {
  if (aqi <= 50)  return "Good";
  if (aqi <= 100) return "Moderate";
  if (aqi <= 150) return "Unhealthy for Sensitive Groups";
  if (aqi <= 200) return "Unhealthy";
  if (aqi <= 300) return "Very Unhealthy";
  return "Hazardous";
}

// ---------------------------------------------------------------------------
//  BLE (V2 service and packet layout; CO2 and battery appended at the end)
// ---------------------------------------------------------------------------

// Live packet, little-endian: timestamp u32, PM1/2.5/4/10 u16 (x10), humidity u16 (x100),
// temperature i16 (x100), VOC u16, NOx u16, AQI u16, sensor code u8   <- V2 layout, 23 bytes
// then CO2 ppm u16 (0 = none), battery % u8 (255 = unknown)            <- V3 additions, 26 bytes
static const char *WEB_AQI_SERVICE_UUID = "7b46a200-fd8a-4a28-8f4b-4b3e7c4f0001";
static const char *WEB_AQI_LIVE_UUID    = "7b46a201-fd8a-4a28-8f4b-4b3e7c4f0001";
static const char *WEB_AQI_STATUS_UUID  = "7b46a202-fd8a-4a28-8f4b-4b3e7c4f0001";
static NimBLECharacteristic *liveCharacteristic = nullptr;
static NimBLECharacteristic *statusCharacteristic = nullptr;
static bool bleConnected = false;

static void writeU16(uint8_t *packet, size_t &offset, uint16_t value) {
  packet[offset++] = value & 0xff;
  packet[offset++] = (value >> 8) & 0xff;
}

static void writeU32(uint8_t *packet, size_t &offset, uint32_t value) {
  for (int i = 0; i < 4; i++) packet[offset++] = (value >> (8 * i)) & 0xff;
}

class WebBleServerCallbacks : public NimBLEServerCallbacks {
  void onConnect(NimBLEServer *) override {
    bleConnected = true;
    Serial.println("[BLE] Connected.");
  }
  void onDisconnect(NimBLEServer *) override {
    bleConnected = false;
    Serial.println("[BLE] Disconnected; advertising restarted.");
    NimBLEDevice::startAdvertising();
  }
};

static void updateWebBleStatus() {
  if (!statusCharacteristic) return;
  char status[192];
  snprintf(status, sizeof(status),
           "{\"name\":\"Portable AQI Recorder\",\"board\":\"V3\",\"sensor\":\"%s\",\"co2\":\"%s\","
           "\"battery\":%d,\"recording\":%s,\"samples\":%u,\"capacity\":%u}",
           sensors_pm_name(),
           sensors_has_scd4x() ? sensors_scd_name() : (sensors_has_co2() ? sensors_pm_name() : "none"),
           batteryPercent,
           dataBuffer.isRecording() ? "true" : "false", (unsigned)dataBuffer.getCount(),
           (unsigned)dataBuffer.getCapacity());
  statusCharacteristic->setValue((const uint8_t *)status, strlen(status));
}

static void setupWebBleService() {
  NimBLEDevice::init("AQI Recorder");
  NimBLEDevice::setPower(ESP_PWR_LVL_P9);
  NimBLEServer *server = NimBLEDevice::createServer();
  server->setCallbacks(new WebBleServerCallbacks());
  server->advertiseOnDisconnect(true);

  NimBLEService *service = server->createService(WEB_AQI_SERVICE_UUID);
  liveCharacteristic = service->createCharacteristic(
      WEB_AQI_LIVE_UUID, NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);
  statusCharacteristic = service->createCharacteristic(WEB_AQI_STATUS_UUID, NIMBLE_PROPERTY::READ);
  updateWebBleStatus();
  service->start();

  NimBLEAdvertising *advertising = NimBLEDevice::getAdvertising();
  advertising->addServiceUUID(WEB_AQI_SERVICE_UUID);
  advertising->setName("AQI Recorder");
  advertising->setScanResponse(true);
  advertising->start();
  Serial.println("[BLE] Advertising as AQI Recorder.");
}

static void notifyWebBleSample(const SensorSample &s) {
  if (!liveCharacteristic) return;
  uint8_t packet[26];
  size_t offset = 0;
  writeU32(packet, offset, s.timestamp);
  writeU16(packet, offset, s.pm1p0);
  writeU16(packet, offset, s.pm2p5);
  writeU16(packet, offset, s.pm4p0);
  writeU16(packet, offset, s.pm10p0);
  writeU16(packet, offset, s.humidity);
  writeU16(packet, offset, (uint16_t)s.temperature);
  writeU16(packet, offset, s.vocIndex);
  writeU16(packet, offset, s.noxIndex);
  writeU16(packet, offset, s.aqi);
  packet[offset++] = sensors_pm_code();
  writeU16(packet, offset, s.co2);
  packet[offset++] = batteryPercent < 0 ? 255 : (uint8_t)batteryPercent;
  liveCharacteristic->setValue(packet, offset);
  if (bleConnected) liveCharacteristic->notify();
  updateWebBleStatus();
}

// ---------------------------------------------------------------------------
//  Measurement
// ---------------------------------------------------------------------------

static uint16_t scaledU16(float v, float scale) {
  if (!isfinite(v) || v < 0.0f) return 0;
  float x = v * scale;
  return x >= 65535.0f ? 65535 : (uint16_t)x;
}

static void measureAndReport() {
  Reading r;
  bool fresh = sensors_read(r);
  latestSample.co2 = r.co2Ppm;          // CO2 may update even when the PM read didn't
  if (!fresh) return;

  int aqi = max(aqiFromPM25(r.pm2p5), aqiFromPM10(r.pm10p0));
  latestSample.pm1p0       = scaledU16(r.pm1p0, 10.0f);
  latestSample.pm2p5       = scaledU16(r.pm2p5, 10.0f);
  latestSample.pm4p0       = scaledU16(r.pm4p0, 10.0f);
  latestSample.pm10p0      = scaledU16(r.pm10p0, 10.0f);
  latestSample.humidity    = scaledU16(r.humidity, 100.0f);
  latestSample.temperature = isfinite(r.temperature) ? (int16_t)(r.temperature * 100.0f) : 0;
  latestSample.vocIndex    = scaledU16(r.vocIndex, 1.0f);
  latestSample.noxIndex    = scaledU16(r.noxIndex, 1.0f);
  latestSample.aqi         = (uint16_t)max(aqi, 0);
  latestSample.timestamp   = millis() - recordingStartMs;

  if (dataBuffer.isRecording()) dataBuffer.addSample(latestSample);
  notifyWebBleSample(latestSample);

  Serial.printf("PM1 %.1f  PM2.5 %.1f  PM4 %.1f  PM10 %.1f", r.pm1p0, r.pm2p5, r.pm4p0, r.pm10p0);
  if (sensors_has_environment())
    Serial.printf("  RH %.1f%%  T %.1fC  VOC %.0f", r.humidity, r.temperature, r.vocIndex);
  if (sensors_has_nox()) Serial.printf("  NOx %.0f", r.noxIndex);
  if (sensors_has_co2()) Serial.printf("  CO2 %u ppm", r.co2Ppm);
  if (batteryPercent >= 0) Serial.printf("  BAT %d%%", batteryPercent);
  Serial.printf("  | AQI %d [%s]\n", aqi, aqiCategory(aqi));
}

static void updateBattery() {
  unsigned percent;
  batteryPercent = BatteryPwmReader::read(percent) ? (int)percent : -1;
}

// ---------------------------------------------------------------------------
//  Buttons
// ---------------------------------------------------------------------------

static bool fieldAvailable(DataField f) {
  switch (f) {
    case DataField::CO2:         return sensors_has_co2();
    case DataField::NOX_INDEX:   return sensors_has_nox();
    case DataField::VOC_INDEX:
    case DataField::TEMPERATURE:
    case DataField::HUMIDITY:    return sensors_has_environment();
    case DataField::SETTINGS:    return false;   // not a chart
    default:                     return sensors_pm_type() != PmSensor::NONE;
  }
}

static void setBrightnessIndex(uint8_t index) {
  brightnessIndex = index % sizeof(BRIGHTNESS_LEVELS);
  display_set_brightness(BRIGHTNESS_LEVELS[brightnessIndex]);
  prefs.putUChar("bright", brightnessIndex);
}

static void toggleRecording() {
  if (dataBuffer.isRecording()) {
    dataBuffer.setRecording(false);
    Serial.println("[REC] Recording stopped.");
  } else {
    dataBuffer.clear();
    recordingStartMs = millis();
    dataBuffer.setRecording(true);
    Serial.printf("[REC] Recording started (%u samples max).\n", (unsigned)dataBuffer.getCapacity());
  }
  updateWebBleStatus();
}

// In a chart, LEFT/RIGHT step to the previous/next field that can be charted.
static void stepChart(int dir) {
  for (int i = 0; i < NAV_COUNT; i++) {
    navIndex = (navIndex + dir + NAV_COUNT) % NAV_COUNT;
    if (fieldAvailable(navSequence[navIndex])) break;
  }
  cursorField = navSequence[navIndex];
}

static void handleButtons() {
  Button btn = buttons_poll();
  if (btn == Button::NONE) return;
  lastDisplayUpdateMs = 0;   // redraw now

  switch (btn) {
    case Button::LEFT:
    case Button::RIGHT: {
      int dir = (btn == Button::LEFT) ? -1 : 1;
      if (screenMode == ScreenMode::HOME) {
        navIndex = (navIndex + dir + NAV_COUNT) % NAV_COUNT;
        cursorField = navSequence[navIndex];
      } else {
        stepChart(dir);
      }
      break;
    }
    case Button::OK:
      if (screenMode == ScreenMode::CHART) {
        screenMode = ScreenMode::HOME;
      } else if (cursorField == DataField::SETTINGS) {
        setBrightnessIndex(brightnessIndex + 1);
      } else if (fieldAvailable(cursorField)) {
        screenMode = ScreenMode::CHART;
      }
      break;
    case Button::OK_LONG:
      toggleRecording();
      break;
    default:
      break;
  }
}

// ---------------------------------------------------------------------------
//  Display
// ---------------------------------------------------------------------------

static void updateDisplay() {
  unsigned long now = millis();
  if (now - lastDisplayUpdateMs < DISPLAY_UPDATE_INTERVAL_MS) return;
  lastDisplayUpdateMs = now;
  if (screenMode == ScreenMode::HOME) {
    display_home(latestSample, cursorField, dataBuffer.isRecording(), bleConnected,
                 sensors_has_co2(), sensors_has_nox(), sensors_has_environment(), batteryPercent);
  } else {
    display_chart(dataBuffer, cursorField, latestSample);
  }
}

// ---------------------------------------------------------------------------
//  Arduino setup / loop
// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);   // native USB CDC on J1
  unsigned long waitStart = millis();
  while (!Serial && millis() - waitStart < 1500) delay(10);   // don't block without a host

  Serial.println("========================================");
  Serial.println("  Portable AQI Recorder V3 (main Rev B) ");
  Serial.println("========================================");

  buttons_begin();
  display_begin();
  prefs.begin("aqi", false);
  setBrightnessIndex(prefs.getUChar("bright", 0));

  BatteryPwmReader::begin(PIN_BAT_PWM);

  // ~64 KB of history: 2700 samples x 24 bytes = 45 min at 1 Hz.
  if (!dataBuffer.begin(2700)) Serial.println("ERROR: data buffer allocation failed.");

  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, 100000);
  sensors_begin(Wire);
  setupWebBleService();

  Serial.printf("Free heap: %u bytes\n", (unsigned)ESP.getFreeHeap());
  recordingStartMs = millis();
}

void loop() {
  if (millis() - lastMeasurementMs >= MEASUREMENT_INTERVAL_MS) {
    lastMeasurementMs = millis();
    updateBattery();
    measureAndReport();
  }
  handleButtons();
  updateDisplay();
  delay(5);
}
