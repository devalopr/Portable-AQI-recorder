/**
 * Portable AQI Monitor
 * ESP32-C3 Super Mini + Sensirion SEN5x Sensor (SEN50 / SEN54 / SEN55)
 *
 * Auto-detects the connected sensor variant at boot:
 *   - SEN50: PM1.0, PM2.5, PM4.0, PM10.0
 *   - SEN54: PM + Humidity, Temperature, VOC Index
 *   - SEN55: PM + Humidity, Temperature, VOC Index, NOx Index
 *
 * Streams data over BLE to the Sensirion MyAmbience app.
 * Also calculates and prints US EPA AQI to the serial monitor.
 */

#include <Arduino.h>
#include <SensirionI2CSen5x.h>
#include <Sensirion_Gadget_BLE.h>
#include <Wire.h>

// ---------------------------------------------------------------------------
//  Sensor variant detection
// ---------------------------------------------------------------------------

enum SensorVariant { VARIANT_SEN50, VARIANT_SEN54, VARIANT_SEN55, VARIANT_UNKNOWN };

static SensorVariant sensorVariant = VARIANT_UNKNOWN;

SensirionI2CSen5x sen5x;

// BLE setup — constructed with a default DataType; reconfigured in setup()
static int64_t lastMeasurementTimeMs = 0;
static int measurementIntervalMs = 1000;
NimBLELibraryWrapper lib;
DataProvider provider(lib, DataType::PM10_PM25_PM40_PM100);

// ---------------------------------------------------------------------------
//  US EPA AQI Calculation
// ---------------------------------------------------------------------------

/**
 * Generic linear interpolation for AQI from a concentration value
 * using the standard EPA piecewise-linear formula:
 *
 *   AQI = ((I_hi - I_lo) / (C_hi - C_lo)) * (C - C_lo) + I_lo
 */
static int calcAQILinear(float Ih, float Il, float Ch, float Cl, float C) {
  return (int)round(((Ih - Il) / (Ch - Cl)) * (C - Cl) + Il);
}

/**
 * Calculates the AQI sub-index from PM2.5 (µg/m³) using US EPA breakpoints.
 * Returns -1 if the value is out of range.
 */
int aqiFromPM25(float pm25) {
  if (pm25 < 0.0f)
    return -1;
  if (pm25 > 500.4f)
    return 501; // "Beyond AQI"
  // EPA breakpoint table (2024 revised)
  if (pm25 <= 9.0f)
    return calcAQILinear(50, 0, 9.0f, 0.0f, pm25);
  if (pm25 <= 35.4f)
    return calcAQILinear(100, 51, 35.4f, 9.1f, pm25);
  if (pm25 <= 55.4f)
    return calcAQILinear(150, 101, 55.4f, 35.5f, pm25);
  if (pm25 <= 125.4f)
    return calcAQILinear(200, 151, 125.4f, 55.5f, pm25);
  if (pm25 <= 225.4f)
    return calcAQILinear(300, 201, 225.4f, 125.5f, pm25);
  if (pm25 <= 325.4f)
    return calcAQILinear(500, 301, 325.4f, 225.5f, pm25);
  return 501;
}

/**
 * Calculates the AQI sub-index from PM10 (µg/m³) using US EPA breakpoints.
 * Returns -1 if the value is out of range.
 */
int aqiFromPM10(float pm10) {
  if (pm10 < 0.0f)
    return -1;
  if (pm10 > 604.0f)
    return 501;
  if (pm10 <= 54.0f)
    return calcAQILinear(50, 0, 54.0f, 0.0f, pm10);
  if (pm10 <= 154.0f)
    return calcAQILinear(100, 51, 154.0f, 55.0f, pm10);
  if (pm10 <= 254.0f)
    return calcAQILinear(150, 101, 254.0f, 155.0f, pm10);
  if (pm10 <= 354.0f)
    return calcAQILinear(200, 151, 354.0f, 255.0f, pm10);
  if (pm10 <= 424.0f)
    return calcAQILinear(300, 201, 424.0f, 355.0f, pm10);
  if (pm10 <= 604.0f)
    return calcAQILinear(500, 301, 604.0f, 425.0f, pm10);
  return 501;
}

/**
 * Returns an AQI category label string.
 */
const char *aqiCategory(int aqi) {
  if (aqi <= 50)
    return "Good";
  if (aqi <= 100)
    return "Moderate";
  if (aqi <= 150)
    return "Unhealthy for Sensitive Groups";
  if (aqi <= 200)
    return "Unhealthy";
  if (aqi <= 300)
    return "Very Unhealthy";
  return "Hazardous";
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

/**
 * Detects the sensor variant by reading the product name via I2C.
 * Returns the variant enum and configures the BLE DataProvider accordingly.
 */
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
    provider.setSampleConfig(DataType::T_RH_VOC_NOX_PM25);
    return VARIANT_SEN55;
  } else if (name == "SEN54") {
    Serial.println("Detected: SEN54 (PM + T/RH + VOC)");
    provider.setSampleConfig(DataType::T_RH_VOC_PM25_V2);
    return VARIANT_SEN54;
  } else {
    Serial.println("Detected: SEN50 (PM only)");
    // Already initialized with PM10_PM25_PM40_PM100 — no change needed
    return VARIANT_SEN50;
  }
}

// ---------------------------------------------------------------------------
//  Main measurement + BLE reporting
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

  // Use the universal readMeasuredValues() for all variants.
  // Unsupported values come back as NAN.
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

  // ---- Serial output: PM values (all variants) ----
  Serial.print("PM1.0: ");
  Serial.print(massConcentrationPm1p0);
  Serial.print("\tPM2.5: ");
  Serial.print(massConcentrationPm2p5);
  Serial.print("\tPM4.0: ");
  Serial.print(massConcentrationPm4p0);
  Serial.print("\tPM10.0: ");
  Serial.print(massConcentrationPm10p0);

  // ---- Serial output: Environmental data (SEN54/SEN55) ----
  if (sensorVariant == VARIANT_SEN54 || sensorVariant == VARIANT_SEN55) {
    Serial.print("\tRH: ");
    if (isnan(ambientHumidity)) {
      Serial.print("n/a");
    } else {
      Serial.print(ambientHumidity);
      Serial.print("%");
    }
    Serial.print("\tT: ");
    if (isnan(ambientTemperature)) {
      Serial.print("n/a");
    } else {
      Serial.print(ambientTemperature);
      Serial.print("°C");
    }
    Serial.print("\tVOC: ");
    if (isnan(vocIndex)) {
      Serial.print("n/a");
    } else {
      Serial.print(vocIndex);
    }
  }

  // ---- Serial output: NOx (SEN55 only) ----
  if (sensorVariant == VARIANT_SEN55) {
    Serial.print("\tNOx: ");
    if (isnan(noxIndex)) {
      Serial.print("n/a");
    } else {
      Serial.print(noxIndex);
    }
  }

  // ---- AQI calculation (all variants) ----
  int aqi25 = aqiFromPM25(massConcentrationPm2p5);
  int aqi10 = aqiFromPM10(massConcentrationPm10p0);
  int aqiMax = max(aqi25, aqi10);

  Serial.print("\t| AQI(PM2.5): ");
  Serial.print(aqi25);
  Serial.print("  AQI(PM10): ");
  Serial.print(aqi10);
  Serial.print("  => AQI: ");
  Serial.print(aqiMax);
  Serial.print(" [");
  Serial.print(aqiCategory(aqiMax));
  Serial.println("]");

  // ---- BLE sample: write values according to detected variant ----
  switch (sensorVariant) {
  case VARIANT_SEN55:
    provider.writeValueToCurrentSample(
        ambientTemperature, SignalType::TEMPERATURE_DEGREES_CELSIUS);
    provider.writeValueToCurrentSample(
        ambientHumidity, SignalType::RELATIVE_HUMIDITY_PERCENTAGE);
    provider.writeValueToCurrentSample(vocIndex, SignalType::VOC_INDEX);
    // NOx may be NAN during the first ~10 seconds; send 0 in that case
    provider.writeValueToCurrentSample(isnan(noxIndex) ? 0.0f : noxIndex,
                                       SignalType::NOX_INDEX);
    provider.writeValueToCurrentSample(
        massConcentrationPm2p5,
        SignalType::PM2P5_MICRO_GRAMM_PER_CUBIC_METER);
    break;

  case VARIANT_SEN54:
    provider.writeValueToCurrentSample(
        ambientTemperature, SignalType::TEMPERATURE_DEGREES_CELSIUS);
    provider.writeValueToCurrentSample(
        ambientHumidity, SignalType::RELATIVE_HUMIDITY_PERCENTAGE);
    provider.writeValueToCurrentSample(vocIndex, SignalType::VOC_INDEX);
    provider.writeValueToCurrentSample(
        massConcentrationPm2p5,
        SignalType::PM2P5_MICRO_GRAMM_PER_CUBIC_METER);
    break;

  case VARIANT_SEN50:
  default:
    provider.writeValueToCurrentSample(
        massConcentrationPm1p0,
        SignalType::PM1P0_MICRO_GRAMM_PER_CUBIC_METER);
    provider.writeValueToCurrentSample(
        massConcentrationPm2p5,
        SignalType::PM2P5_MICRO_GRAMM_PER_CUBIC_METER);
    provider.writeValueToCurrentSample(
        massConcentrationPm4p0,
        SignalType::PM4P0_MICRO_GRAMM_PER_CUBIC_METER);
    provider.writeValueToCurrentSample(
        massConcentrationPm10p0,
        SignalType::PM10P0_MICRO_GRAMM_PER_CUBIC_METER);
    break;
  }

  provider.commitSample();
  lastMeasurementTimeMs = millis();
}

// ---------------------------------------------------------------------------
//  Arduino setup / loop
// ---------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);

  // Wait briefly for USB-CDC serial on ESP32-C3
  delay(2000);
  Serial.println("========================================");
  Serial.println("   Portable AQI Monitor — SEN5x + BLE  ");
  Serial.println("========================================");

  // ESP32-C3 Super Mini I2C: SDA = GPIO8, SCL = GPIO9
  Wire.begin(8, 9);

  // Initialize the GadgetBle Library
  provider.begin();
  Serial.print("BLE Gadget initialized, deviceId = ");
  Serial.println(provider.getDeviceIdString());

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

  // Auto-detect sensor variant and reconfigure BLE DataType
  sensorVariant = detectSensorVariant();

  // Print sensor info
  printSerialNumber();
  printModuleVersions();

  // Start Measurement
  error = sen5x.startMeasurement();
  if (error) {
    Serial.println("Error trying to start sensor measurement!");
  } else {
    Serial.println("Measurement started!");
    Serial.println("----------------------------------------");
  }
}

void loop() {
  if (millis() - lastMeasurementTimeMs >= measurementIntervalMs) {
    measure_and_report();
  }

  provider.handleDownload();
  delay(20);
}
