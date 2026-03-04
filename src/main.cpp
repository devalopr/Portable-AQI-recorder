/**
 * Portable AQI Monitor
 * ESP32-C3 Super Mini + SEN50 Sensor
 *
 * Streams PM1.0, PM2.5, PM4.0, PM10.0 over BLE to Sensirion MyAmbience app.
 * Also calculates and prints US EPA AQI to the serial monitor.
 */

#include <Arduino.h>
#include <SensirionI2CSen5x.h>
#include <Sensirion_Gadget_BLE.h>
#include <Wire.h>


SensirionI2CSen5x sen5x;

// BLE setup — PM-only data type for SEN50
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

  error = sen5x.readMeasuredValuesSen50(
      massConcentrationPm1p0, massConcentrationPm2p5, massConcentrationPm4p0,
      massConcentrationPm10p0);

  if (error) {
    Serial.print("Error trying to execute readMeasuredValuesSen50(): ");
    errorToString(error, errorMessage, 256);
    Serial.println(errorMessage);
    return;
  }

  // Print raw PM values
  Serial.print("PM1.0: ");
  Serial.print(massConcentrationPm1p0);
  Serial.print("\tPM2.5: ");
  Serial.print(massConcentrationPm2p5);
  Serial.print("\tPM4.0: ");
  Serial.print(massConcentrationPm4p0);
  Serial.print("\tPM10.0: ");
  Serial.print(massConcentrationPm10p0);

  // Calculate and print AQI
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

  // Write all four PM values to the BLE sample
  provider.writeValueToCurrentSample(
      massConcentrationPm1p0, SignalType::PM1P0_MICRO_GRAMM_PER_CUBIC_METER);

  provider.writeValueToCurrentSample(
      massConcentrationPm2p5, SignalType::PM2P5_MICRO_GRAMM_PER_CUBIC_METER);

  provider.writeValueToCurrentSample(
      massConcentrationPm4p0, SignalType::PM4P0_MICRO_GRAMM_PER_CUBIC_METER);

  provider.writeValueToCurrentSample(
      massConcentrationPm10p0, SignalType::PM10P0_MICRO_GRAMM_PER_CUBIC_METER);

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
  Serial.println("   Portable AQI Monitor — SEN50 + BLE  ");
  Serial.println("========================================");

  // ESP32-C3 Super Mini I2C: SDA = GPIO8, SCL = GPIO9
  Wire.begin(8, 9);

  // Initialize the GadgetBle Library
  provider.begin();
  Serial.print("BLE Gadget initialized, deviceId = ");
  Serial.println(provider.getDeviceIdString());

  // Initialize SEN50
  sen5x.begin(Wire);

  uint16_t error = sen5x.deviceReset();
  if (error) {
    char errorMessage[256];
    Serial.print("Error trying to execute deviceReset(): ");
    errorToString(error, errorMessage, 256);
    Serial.println(errorMessage);
  }
  delay(100);

  // Print sensor info
  printSerialNumber();
  printModuleVersions();

  // Start Measurement
  error = sen5x.startMeasurement();
  if (error) {
    Serial.println("Error trying to start sensor measurement!");
  } else {
    Serial.println("SEN50 measurement started!");
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
