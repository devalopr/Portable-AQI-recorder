#pragma once
#include <Arduino.h>
#include <Wire.h>

/// Particulate sensor on J3 (SEN5x, 5 V, I2C 0x69) or J4 (SEN6x, 3.3 V, I2C 0x6B).
enum class PmSensor : uint8_t {
  NONE, SEN50, SEN54, SEN55, SEN63C, SEN65, SEN66, SEN68
};

/// One reading. Values a sensor doesn't measure, or hasn't produced yet, are NAN
/// (co2Ppm is 0 when unavailable).
struct Reading {
  float pm1p0 = NAN, pm2p5 = NAN, pm4p0 = NAN, pm10p0 = NAN;
  float humidity = NAN, temperature = NAN;
  float vocIndex = NAN, noxIndex = NAN;
  uint16_t co2Ppm = 0;
};

/// Probe the bus, reset and start whatever is fitted. Call once, after Wire.begin().
void sensors_begin(TwoWire &wire);

/// Read the latest values (call about once a second). Returns false if the
/// particulate sensor gave no new data this time.
bool sensors_read(Reading &out);

PmSensor sensors_pm_type();
bool sensors_has_scd4x();
/// "SCD40", "SCD41", "SCD43" (or "SCD4x" if the variant can't be read), "none" if not fitted.
const char *sensors_scd_name();

/// True if the fitted sensors provide these values.
bool sensors_has_environment();   // humidity, temperature, VOC
bool sensors_has_nox();
bool sensors_has_co2();           // SCD4x or a SEN63C/SEN66

const char *sensors_pm_name();
/// Numeric code used in the BLE packet: 50/54/55 for SEN5x, 63/65/66/68 for SEN6x, 0 for none.
uint8_t sensors_pm_code();
