/**
 * Portable AQI Monitor — V2
 * ESP32-C3 Super Mini + Sensirion SEN5x + ILI9225 TFT Display
 *
 * Auto-detects the connected sensor variant at boot:
 *   - SEN50: PM1.0, PM2.5, PM4.0, PM10.0
 *   - SEN54: PM + Humidity, Temperature, VOC Index
 *   - SEN55: PM + Humidity, Temperature, VOC Index, NOx Index
 *
 * Displays data on a 176×220 ILI9225 TFT with 4-button navigation.
 * Streams data over BLE to the companion web app.
 * Records data into RAM ring buffer for on-device charting.
 * Calculates and displays US EPA AQI.
 */

#include <Arduino.h>
#include <cstring>
#include <NimBLEDevice.h>
#include <SensirionI2CSen5x.h>
#include <Wire.h>

#include "data_buffer.h"
#include "buttons.h"
#include "display.h"

// ---------------------------------------------------------------------------
//  Sensor variant detection
// ---------------------------------------------------------------------------

enum SensorVariant { VARIANT_SEN50, VARIANT_SEN54, VARIANT_SEN55, VARIANT_UNKNOWN };

static SensorVariant sensorVariant = VARIANT_UNKNOWN;

SensirionI2CSen5x sen5x;

static int64_t lastMeasurementTimeMs = 0;
static int measurementIntervalMs = 1000;

// Display + UI state
static ScreenMode screenMode = ScreenMode::HOME;
static DataField cursorField = DataField::PM1_0;
static SensorSample latestSample = {};
static unsigned long recordingStartMs = 0;

// Data buffer
DataBuffer dataBuffer;

// Display refresh timing
static unsigned long lastDisplayUpdateMs = 0;
static const unsigned long DISPLAY_UPDATE_INTERVAL_MS = 500;

// Browser-friendly BLE service for the companion web app.
// Samples are sent as a compact little-endian binary packet:
// timestamp u32, PM fields u16 x4, humidity u16, temperature i16,
// VOC u16, NOx u16, AQI u16, sensor variant u8.
static const char *WEB_AQI_SERVICE_UUID = "7b46a200-fd8a-4a28-8f4b-4b3e7c4f0001";
static const char *WEB_AQI_LIVE_UUID    = "7b46a201-fd8a-4a28-8f4b-4b3e7c4f0001";
static const char *WEB_AQI_STATUS_UUID  = "7b46a202-fd8a-4a28-8f4b-4b3e7c4f0001";
static NimBLEServer *bleServer = nullptr;
static NimBLECharacteristic *liveCharacteristic = nullptr;
static NimBLECharacteristic *statusCharacteristic = nullptr;
static bool bleConnected = false;

// ---------------------------------------------------------------------------
//  US EPA AQI Calculation
// ---------------------------------------------------------------------------

static int calcAQILinear(float Ih, float Il, float Ch, float Cl, float C) {
  return (int)round(((Ih - Il) / (Ch - Cl)) * (C - Cl) + Il);
}

int aqiFromPM25(float pm25) {
  if (pm25 < 0.0f)    return -1;
  if (pm25 > 500.4f)  return 501;
  if (pm25 <= 9.0f)   return calcAQILinear(50, 0, 9.0f, 0.0f, pm25);
  if (pm25 <= 35.4f)  return calcAQILinear(100, 51, 35.4f, 9.1f, pm25);
  if (pm25 <= 55.4f)  return calcAQILinear(150, 101, 55.4f, 35.5f, pm25);
  if (pm25 <= 125.4f) return calcAQILinear(200, 151, 125.4f, 55.5f, pm25);
  if (pm25 <= 225.4f) return calcAQILinear(300, 201, 225.4f, 125.5f, pm25);
  if (pm25 <= 325.4f) return calcAQILinear(500, 301, 325.4f, 225.5f, pm25);
  return 501;
}

int aqiFromPM10(float pm10) {
  if (pm10 < 0.0f)    return -1;
  if (pm10 > 604.0f)  return 501;
  if (pm10 <= 54.0f)  return calcAQILinear(50, 0, 54.0f, 0.0f, pm10);
  if (pm10 <= 154.0f) return calcAQILinear(100, 51, 154.0f, 55.0f, pm10);
  if (pm10 <= 254.0f) return calcAQILinear(150, 101, 254.0f, 155.0f, pm10);
  if (pm10 <= 354.0f) return calcAQILinear(200, 151, 354.0f, 255.0f, pm10);
  if (pm10 <= 424.0f) return calcAQILinear(300, 201, 424.0f, 355.0f, pm10);
  if (pm10 <= 604.0f) return calcAQILinear(500, 301, 604.0f, 425.0f, pm10);
  return 501;
}

const char *aqiCategory(int aqi) {
  if (aqi <= 50)  return "Good";
  if (aqi <= 100) return "Moderate";
  if (aqi <= 150) return "Unhealthy for Sensitive Groups";
  if (aqi <= 200) return "Unhealthy";
  if (aqi <= 300) return "Very Unhealthy";
  return "Hazardous";
}

static const char *sensorVariantName(SensorVariant variant) {
  switch (variant) {
  case VARIANT_SEN50: return "SEN50";
  case VARIANT_SEN54: return "SEN54";
  case VARIANT_SEN55: return "SEN55";
  default: return "Unknown";
  }
}

static uint8_t sensorVariantCode(SensorVariant variant) {
  switch (variant) {
  case VARIANT_SEN50: return 50;
  case VARIANT_SEN54: return 54;
  case VARIANT_SEN55: return 55;
  default: return 0;
  }
}

static void writeU16(uint8_t *packet, size_t &offset, uint16_t value) {
  packet[offset++] = value & 0xff;
  packet[offset++] = (value >> 8) & 0xff;
}

static void writeI16(uint8_t *packet, size_t &offset, int16_t value) {
  writeU16(packet, offset, (uint16_t)value);
}

static void writeU32(uint8_t *packet, size_t &offset, uint32_t value) {
  packet[offset++] = value & 0xff;
  packet[offset++] = (value >> 8) & 0xff;
  packet[offset++] = (value >> 16) & 0xff;
  packet[offset++] = (value >> 24) & 0xff;
}

class WebBleServerCallbacks : public NimBLEServerCallbacks {
  void onConnect(NimBLEServer *server) override {
    bleConnected = true;
    Serial.println("[BLE] Connected.");
  }

  void onDisconnect(NimBLEServer *server) override {
    bleConnected = false;
    Serial.println("[BLE] Disconnected; advertising restarted.");
    NimBLEDevice::startAdvertising();
  }
};

void updateWebBleStatus() {
  if (!statusCharacteristic) return;

  String status = "{";
  status += "\"name\":\"Portable AQI Recorder\",";
  status += "\"sensor\":\"";
  status += sensorVariantName(sensorVariant);
  status += "\",";
  status += "\"recording\":";
  status += dataBuffer.isRecording() ? "true" : "false";
  status += ",";
  status += "\"samples\":";
  status += dataBuffer.getCount();
  status += ",";
  status += "\"capacity\":";
  status += dataBuffer.getCapacity();
  status += "}";

  statusCharacteristic->setValue((const uint8_t *)status.c_str(), status.length());
}

void setupWebBleService() {
  NimBLEDevice::init("AQI Recorder");
  NimBLEDevice::setPower(ESP_PWR_LVL_P9);

  bleServer = NimBLEDevice::createServer();
  bleServer->setCallbacks(new WebBleServerCallbacks());
  bleServer->advertiseOnDisconnect(true);

  NimBLEService *service = bleServer->createService(WEB_AQI_SERVICE_UUID);
  liveCharacteristic = service->createCharacteristic(
      WEB_AQI_LIVE_UUID, NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);
  statusCharacteristic = service->createCharacteristic(
      WEB_AQI_STATUS_UUID, NIMBLE_PROPERTY::READ);

  updateWebBleStatus();
  service->start();

  NimBLEAdvertising *advertising = NimBLEDevice::getAdvertising();
  advertising->addServiceUUID(WEB_AQI_SERVICE_UUID);
  advertising->setName("AQI Recorder");
  advertising->setScanResponse(true);
  advertising->start();

  Serial.println("Web BLE initialized as AQI Recorder.");
}

void notifyWebBleSample(const SensorSample &sample) {
  if (!liveCharacteristic) return;

  uint8_t packet[23];
  size_t offset = 0;

  writeU32(packet, offset, sample.timestamp);
  writeU16(packet, offset, sample.pm1p0);
  writeU16(packet, offset, sample.pm2p5);
  writeU16(packet, offset, sample.pm4p0);
  writeU16(packet, offset, sample.pm10p0);
  writeU16(packet, offset, sample.humidity);
  writeI16(packet, offset, sample.temperature);
  writeU16(packet, offset, sample.vocIndex);
  writeU16(packet, offset, sample.noxIndex);
  writeU16(packet, offset, sample.aqi);
  packet[offset++] = sensorVariantCode(sensorVariant);

  liveCharacteristic->setValue(packet, offset);
  if (bleConnected) {
    liveCharacteristic->notify();
  }
  updateWebBleStatus();
}

// ---------------------------------------------------------------------------
//  Sensor helpers
// ---------------------------------------------------------------------------

void printSerialNumber() {
  uint16_t error;
  char errorMessage[256];
  unsigned char serialNumber[32];
  uint8_t serialNumberSize = 32;
  error = sen5x.getSerialNumber(serialNumber, serialNumberSize);
  if (error) {
    Serial.print("Error trying to execute getSerialNumber(): ");
    errorToString(error, errorMessage, 256);
    Serial.println(errorMessage);
  } else {
    Serial.print("SerialNumber: ");
    Serial.println((char *)serialNumber);
  }
}

void printModuleVersions() {
  uint16_t error;
  char errorMessage[256];

  unsigned char productName[32];
  uint8_t productNameSize = 32;
  error = sen5x.getProductName(productName, productNameSize);
  if (error) {
    Serial.print("Error trying to execute getProductName(): ");
    errorToString(error, errorMessage, 256);
    Serial.println(errorMessage);
  } else {
    Serial.print("ProductName: ");
    Serial.println((char *)productName);
  }

  uint8_t firmwareMajor, firmwareMinor;
  bool firmwareDebug;
  uint8_t hardwareMajor, hardwareMinor;
  uint8_t protocolMajor, protocolMinor;
  error = sen5x.getVersion(firmwareMajor, firmwareMinor, firmwareDebug,
                           hardwareMajor, hardwareMinor, protocolMajor,
                           protocolMinor);
  if (error) {
    Serial.print("Error trying to execute getVersion(): ");
    errorToString(error, errorMessage, 256);
    Serial.println(errorMessage);
  } else {
    Serial.print("Firmware: ");
    Serial.print(firmwareMajor);
    Serial.print(".");
    Serial.println(firmwareMinor);
    Serial.print("Hardware: ");
    Serial.print(hardwareMajor);
    Serial.print(".");
    Serial.println(hardwareMinor);
  }
}

SensorVariant detectSensorVariant() {
  uint16_t error;
  char errorMessage[256];
  unsigned char productName[32];
  uint8_t productNameSize = 32;

  error = sen5x.getProductName(productName, productNameSize);
  if (error) {
    Serial.print("Error reading product name: ");
    errorToString(error, errorMessage, 256);
    Serial.println(errorMessage);
    Serial.println("Falling back to SEN50 (PM-only) mode.");
    return VARIANT_SEN50;
  }

  String name = String((char *)productName);
  name.trim();

  if (name == "SEN55") {
    Serial.println("Detected: SEN55 (PM + T/RH + VOC + NOx)");
    return VARIANT_SEN55;
  } else if (name == "SEN54") {
    Serial.println("Detected: SEN54 (PM + T/RH + VOC)");
    return VARIANT_SEN54;
  } else {
    Serial.println("Detected: SEN50 (PM only)");
    return VARIANT_SEN50;
  }
}

// ---------------------------------------------------------------------------
//  Measurement + BLE + Buffer
// ---------------------------------------------------------------------------

void measure_and_report() {
  uint16_t error;
  char errorMessage[256];

  float massConcentrationPm1p0;
  float massConcentrationPm2p5;
  float massConcentrationPm4p0;
  float massConcentrationPm10p0;
  float ambientHumidity;
  float ambientTemperature;
  float vocIndex;
  float noxIndex;

  error = sen5x.readMeasuredValues(
      massConcentrationPm1p0, massConcentrationPm2p5, massConcentrationPm4p0,
      massConcentrationPm10p0, ambientHumidity, ambientTemperature, vocIndex,
      noxIndex);

  if (error) {
    Serial.print("Error trying to execute readMeasuredValues(): ");
    errorToString(error, errorMessage, 256);
    Serial.println(errorMessage);
    return;
  }

  // Compute AQI
  int aqi25 = aqiFromPM25(massConcentrationPm2p5);
  int aqi10 = aqiFromPM10(massConcentrationPm10p0);
  int aqiMax = max(aqi25, aqi10);

  // ---- Build compact sample for buffer ----
  latestSample.pm1p0       = (uint16_t)(massConcentrationPm1p0 * 10.0f);
  latestSample.pm2p5       = (uint16_t)(massConcentrationPm2p5 * 10.0f);
  latestSample.pm4p0       = (uint16_t)(massConcentrationPm4p0 * 10.0f);
  latestSample.pm10p0      = (uint16_t)(massConcentrationPm10p0 * 10.0f);
  latestSample.humidity    = isnan(ambientHumidity) ? 0 : (uint16_t)(ambientHumidity * 100.0f);
  latestSample.temperature = isnan(ambientTemperature) ? 0 : (int16_t)(ambientTemperature * 100.0f);
  latestSample.vocIndex    = isnan(vocIndex) ? 0 : (uint16_t)vocIndex;
  latestSample.noxIndex    = isnan(noxIndex) ? 0 : (uint16_t)noxIndex;
  latestSample.aqi         = (uint16_t)max(aqiMax, 0);
  latestSample.timestamp   = millis() - recordingStartMs;

  // Add to ring buffer if recording
  if (dataBuffer.isRecording()) {
    dataBuffer.addSample(latestSample);
  }
  notifyWebBleSample(latestSample);

  // ---- Serial output ----
  Serial.print("PM1.0: ");   Serial.print(massConcentrationPm1p0);
  Serial.print("\tPM2.5: "); Serial.print(massConcentrationPm2p5);
  Serial.print("\tPM4.0: "); Serial.print(massConcentrationPm4p0);
  Serial.print("\tPM10: ");  Serial.print(massConcentrationPm10p0);

  if (sensorVariant == VARIANT_SEN54 || sensorVariant == VARIANT_SEN55) {
    Serial.print("\tRH: ");
    Serial.print(isnan(ambientHumidity) ? 0.0f : ambientHumidity); Serial.print("%");
    Serial.print("\tT: ");
    Serial.print(isnan(ambientTemperature) ? 0.0f : ambientTemperature); Serial.print("C");
    Serial.print("\tVOC: ");
    Serial.print(isnan(vocIndex) ? 0.0f : vocIndex);
  }
  if (sensorVariant == VARIANT_SEN55) {
    Serial.print("\tNOx: ");
    Serial.print(isnan(noxIndex) ? 0.0f : noxIndex);
  }

  Serial.print("\t| AQI: "); Serial.print(aqiMax);
  Serial.print(" ["); Serial.print(aqiCategory(aqiMax)); Serial.println("]");
  lastMeasurementTimeMs = millis();
}

// ---------------------------------------------------------------------------
//  Button handling
// ---------------------------------------------------------------------------

void handleButtons() {
  Button btn = buttons_poll();
  if (btn == Button::NONE) return;

  switch (btn) {
  case Button::UP:
    if (screenMode == ScreenMode::HOME) {
      int cur = (int)cursorField;
      cur--;
      if (cur < 0) cur = (int)DataField::_COUNT - 1;
      cursorField = (DataField)cur;
    }
    break;

  case Button::DOWN:
    if (screenMode == ScreenMode::HOME) {
      int cur = (int)cursorField;
      cur++;
      if (cur >= (int)DataField::_COUNT) cur = 0;
      cursorField = (DataField)cur;
    }
    break;

  case Button::SELECT:
    if (screenMode == ScreenMode::HOME) {
      screenMode = ScreenMode::CHART;
    } else {
      screenMode = ScreenMode::HOME;
    }
    // Force immediate redraw on mode change
    lastDisplayUpdateMs = 0;
    break;

  case Button::RECORD:
    if (dataBuffer.isRecording()) {
      dataBuffer.setRecording(false);
      Serial.println("[REC] Recording stopped.");
    } else {
      dataBuffer.clear();
      recordingStartMs = millis();
      dataBuffer.setRecording(true);
      Serial.print("[REC] Recording started. Buffer capacity: ");
      Serial.print(dataBuffer.getCapacity());
      Serial.println(" samples.");
    }
    break;

  default:
    break;
  }
}

// ---------------------------------------------------------------------------
//  Display update
// ---------------------------------------------------------------------------

void updateDisplay() {
  unsigned long now = millis();
  if (now - lastDisplayUpdateMs < DISPLAY_UPDATE_INTERVAL_MS) return;
  lastDisplayUpdateMs = now;

  if (screenMode == ScreenMode::HOME) {
    display_home(latestSample, cursorField,
                 dataBuffer.isRecording(), bleConnected);
  } else {
    display_chart(dataBuffer, cursorField);
  }
}

// ---------------------------------------------------------------------------
//  Arduino setup / loop
// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(2000);

  Serial.println("========================================");
  Serial.println("  Portable AQI Monitor V2 — SEN5x+TFT  ");
  Serial.println("========================================");

  // Initialize display
  display_begin();
  Serial.println("Display initialized.");

  // Initialize buttons
  buttons_begin();
  Serial.println("Buttons initialized.");

  // Allocate ring buffer — use ~60KB for data
  // 60000 / 22 = ~2727 samples = ~45 min at 1/sec
  size_t bufferSamples = 2700;
  if (dataBuffer.begin(bufferSamples)) {
    Serial.print("Data buffer allocated: ");
    Serial.print(bufferSamples);
    Serial.print(" samples (");
    Serial.print(bufferSamples * sizeof(SensorSample));
    Serial.println(" bytes)");
  } else {
    Serial.println("ERROR: Failed to allocate data buffer!");
  }

  // ESP32-C3 Super Mini I2C: SDA = GPIO8, SCL = GPIO9
  Wire.begin(8, 9);

  // Initialize BLE
  setupWebBleService();

  // Initialize SEN5x
  sen5x.begin(Wire);
  uint16_t error = sen5x.deviceReset();
  if (error) {
    char errorMessage[256];
    Serial.print("Error trying to execute deviceReset(): ");
    errorToString(error, errorMessage, 256);
    Serial.println(errorMessage);
  }
  delay(100);

  // Auto-detect sensor variant
  sensorVariant = detectSensorVariant();
  printSerialNumber();
  printModuleVersions();

  // Print heap info
  Serial.print("Free heap: ");
  Serial.print(ESP.getFreeHeap());
  Serial.println(" bytes");

  // Start measurement
  error = sen5x.startMeasurement();
  if (error) {
    Serial.println("Error trying to start sensor measurement!");
  } else {
    Serial.println("Measurement started!");
    Serial.println("----------------------------------------");
  }

  recordingStartMs = millis();
}

void loop() {
  // Read sensor at 1 Hz
  if (millis() - lastMeasurementTimeMs >= measurementIntervalMs) {
    measure_and_report();
  }

  // Handle button input
  handleButtons();

  // Update display
  updateDisplay();

  delay(10);
}
