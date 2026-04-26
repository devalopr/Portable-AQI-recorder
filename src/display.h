#pragma once
#include "data_buffer.h"
#include <cstdint>

/// Which screen is currently shown
enum class ScreenMode : uint8_t {
  HOME,   // All values + AQI
  CHART   // Full-screen chart of selected field
};

/// Data fields that can be selected / charted
enum class DataField : uint8_t {
  PM1_0 = 0,
  PM2_5,
  PM4_0,
  PM10_0,
  HUMIDITY,
  TEMPERATURE,
  VOC_INDEX,
  NOX_INDEX,
  CO2,
  AQI,
  _COUNT  // sentinel — number of fields
};

/// Initialize the ST7789 display. Call once in setup().
void display_begin();

/// Draw the home screen with current sensor values.
/// cursor = which DataField row is highlighted.
void display_home(const SensorSample &current, DataField cursor,
                  bool recording, bool bleConnected);

/// Draw a full-screen chart of `field` using data from `buf`.
void display_chart(const DataBuffer &buf, DataField field);

/// Returns short label for a data field (e.g. "PM2.5")
const char *fieldLabel(DataField f);

/// Returns unit string for a data field (e.g. "µg/m³")
const char *fieldUnit(DataField f);

/// Extracts the raw uint16 value from a sample for a given field.
uint16_t fieldValue(const SensorSample &s, DataField f);

/// Converts the raw uint16 value to a float for display.
float fieldValueFloat(const SensorSample &s, DataField f);
