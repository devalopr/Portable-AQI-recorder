#include "display.h"
#include "display_format.h"
#include "rubik_bold_fonts.h"
#include <TFT_eSPI.h>
#include <SPI.h>

// --- Dashboard Colors (RGB565) ---
#define RGB565(r, g, b) (uint16_t)((((r) & 0xF8) << 8) | (((g) & 0xFC) << 3) | ((b) >> 3))

#define C_BG          0xFFFF
#define C_CARD        0xFFFF
#define C_CARD_ALT    0xFFFF
#define C_SHADOW      0xFFFF
#define C_BORDER      0x0000
#define C_TEXT_DARK   0x0000
#define C_TEXT_MID    RGB565(72, 72, 72)
#define C_TEXT_LIGHT  RGB565(96, 96, 96)
#define C_TEXT_WHITE  0xFFFF
#define C_HIGHLIGHT   0xFFFF
#define C_SELECT      0x0000 // Black outline for maximum contrast
#define C_REC_RED     RGB565(255, 86, 91)
#define C_BLE_BLUE    RGB565(84, 135, 255)
#define C_TEMP_ORANGE RGB565(248, 136, 31)
#define C_HUM_CYAN    RGB565(82, 197, 224)
#define C_GEAR_BG     RGB565(70, 70, 76)
#define C_CHART_PM1   RGB565(30, 144, 255)
#define C_CHART_PM25  RGB565(248, 136, 31)
#define C_CHART_PM4   RGB565(151, 79, 201)
#define C_CHART_PM10  RGB565(126, 32, 58)

// Health Colors
#define C_GOOD        RGB565(27, 205, 0)
#define C_MODERATE    RGB565(245, 208, 0)
#define C_USG         RGB565(248, 136, 31)
#define C_UNHEALTHY   RGB565(238, 76, 76)
#define C_VERY_UNH    RGB565(151, 79, 201)
#define C_HAZARDOUS   RGB565(126, 32, 58)

static const uint16_t MAX_DISPLAY_AQI = 65535;
static const uint16_t MAX_DISPLAY_PM = 65535;
static const uint16_t MAX_DISPLAY_CO2 = 4000;
static const uint16_t MAX_DISPLAY_VOC = 500;
static const uint16_t PLACEHOLDER_CO2_PPM = 1000;

static TFT_eSPI tft = TFT_eSPI();
static TFT_eSprite chartFrame(&tft);
static bool chartFrameReady = false;

// ---- Field helpers ----

const char *fieldLabel(DataField f) {
  switch (f) {
    case DataField::PM1_0:       return "PM1.0";
    case DataField::PM2_5:       return "PM2.5";
    case DataField::PM4_0:       return "PM4.0";
    case DataField::PM10_0:      return "PM10";
    case DataField::HUMIDITY:    return "Humidity";
    case DataField::TEMPERATURE: return "Temperature";
    case DataField::VOC_INDEX:   return "VOC";
    case DataField::NOX_INDEX:   return "NOx";
    case DataField::CO2:         return "CO2";
    case DataField::AQI:         return "AQI";
    case DataField::SETTINGS:    return "Settings";
    default:                     return "?";
  }
}

const char *fieldUnit(DataField f) {
  switch (f) {
    case DataField::PM1_0:
    case DataField::PM2_5:
    case DataField::PM4_0:
    case DataField::PM10_0:      return "ug/m3";
    case DataField::HUMIDITY:    return "%";
    case DataField::TEMPERATURE: return "C";
    case DataField::VOC_INDEX:   return "index";
    case DataField::NOX_INDEX:   return "index";
    case DataField::CO2:         return "ppm";
    case DataField::AQI:         return "";
    default:                     return "";
  }
}

uint16_t fieldValue(const SensorSample &s, DataField f) {
  switch (f) {
    case DataField::PM1_0:       return s.pm1p0;
    case DataField::PM2_5:       return s.pm2p5;
    case DataField::PM4_0:       return s.pm4p0;
    case DataField::PM10_0:      return s.pm10p0;
    case DataField::HUMIDITY:    return s.humidity;
    case DataField::TEMPERATURE: return (uint16_t)s.temperature;
    case DataField::VOC_INDEX:   return s.vocIndex;
    case DataField::NOX_INDEX:   return s.noxIndex;
    case DataField::CO2:         return PLACEHOLDER_CO2_PPM;
    case DataField::AQI:         return s.aqi;
    default:                     return 0;
  }
}

float fieldValueFloat(const SensorSample &s, DataField f) {
  switch (f) {
    case DataField::PM1_0:       return s.pm1p0 / 10.0f;
    case DataField::PM2_5:       return s.pm2p5 / 10.0f;
    case DataField::PM4_0:       return s.pm4p0 / 10.0f;
    case DataField::PM10_0:      return s.pm10p0 / 10.0f;
    case DataField::HUMIDITY:    return s.humidity / 100.0f;
    case DataField::TEMPERATURE: return s.temperature / 100.0f;
    case DataField::VOC_INDEX:   return (float)s.vocIndex;
    case DataField::NOX_INDEX:   return (float)s.noxIndex;
    case DataField::CO2:         return (float)PLACEHOLDER_CO2_PPM;
    case DataField::AQI:         return (float)s.aqi;
    default:                     return 0.0f;
  }
}

// ---- Colors ----

static uint16_t aqiColor(uint16_t aqi) {
  if (aqi <= 50)  return C_GOOD;
  if (aqi <= 100) return C_MODERATE;
  if (aqi <= 150) return C_USG;
  if (aqi <= 200) return C_UNHEALTHY;
  if (aqi <= 300) return C_VERY_UNH;
  return C_HAZARDOUS;
}

static uint16_t textOnColor(uint16_t bg) {
  return (bg == C_GOOD || bg == C_MODERATE || bg == C_USG ||
          bg == C_UNHEALTHY || bg == C_HUM_CYAN) ? C_TEXT_DARK : C_TEXT_WHITE;
}

static uint16_t pmColor(float pm25) {
  if (pm25 <= 9.0f) return C_GOOD;
  if (pm25 <= 35.4f) return C_MODERATE;
  if (pm25 <= 55.4f) return C_USG;
  if (pm25 <= 125.4f) return C_UNHEALTHY;
  if (pm25 <= 225.4f) return C_VERY_UNH;
  return C_HAZARDOUS;
}

static uint16_t vocColor(float voc) {
  if (voc <= 150) return C_GOOD;
  if (voc <= 250) return C_MODERATE;
  if (voc <= 350) return C_USG;
  if (voc <= 450) return C_UNHEALTHY;
  return C_HAZARDOUS;
}

static uint16_t co2Color(float co2) {
  if (co2 <= 800) return C_GOOD;
  if (co2 <= 1000) return C_MODERATE;
  if (co2 <= 1500) return C_USG;
  if (co2 <= 2000) return C_UNHEALTHY;
  return C_HAZARDOUS;
}

static uint16_t tempColor(float t) {
  if (t < 10.0f) return C_HUM_CYAN;
  if (t <= 25.0f) return C_GOOD;
  if (t <= 35.0f) return C_TEMP_ORANGE;
  return C_UNHEALTHY;
}

static uint16_t humColor(float h) {
  if (h >= 30.0f && h <= 60.0f) return C_HUM_CYAN;
  if (h >= 20.0f && h <= 70.0f) return C_MODERATE;
  return C_USG;
}

static uint16_t getHealthColor(DataField f, float val) {
  switch (f) {
    case DataField::PM1_0:
    case DataField::PM2_5:
    case DataField::PM4_0:
    case DataField::PM10_0: return pmColor(val);
    case DataField::VOC_INDEX: return vocColor(val);
    case DataField::NOX_INDEX: return vocColor(val); // Similar scale
    case DataField::CO2: return co2Color(val);
    case DataField::TEMPERATURE: return tempColor(val);
    case DataField::HUMIDITY: return humColor(val);
    case DataField::AQI: return aqiColor((uint16_t)val);
    default: return C_TEXT_DARK;
  }
}

static bool isPmField(DataField field) {
  return field == DataField::PM1_0 || field == DataField::PM2_5 ||
         field == DataField::PM4_0 || field == DataField::PM10_0;
}

// ---- Init ----

void display_begin() {
  tft.begin();
  tft.invertDisplay(false);
  tft.setRotation(2);
  tft.fillScreen(C_BG);
  // Reuse one half-screen RGB565 tile: 76.8KB, native SPI pixel format.
  chartFrame.setColorDepth(16);
  chartFrameReady = chartFrame.createSprite(240, 160) != nullptr;
  if (!chartFrameReady) Serial.println("ERROR: Chart framebuffer allocation failed.");
}

// ---- Drawing functions ----

static void drawStatusChip(int x, int y, const char *label, bool active,
                           uint16_t activeColor) {
  uint16_t fill = active ? activeColor : C_TEXT_LIGHT;

  tft.fillRoundRect(x, y, 42, 22, 4, fill);
  tft.drawRoundRect(x, y, 42, 22, 4, C_BORDER);
  tft.setFreeFont(&RubikBold12);
  tft.setTextColor(C_TEXT_WHITE, fill);
  tft.setTextDatum(MC_DATUM);
  tft.drawString(label, x + 21, y + 12);
  tft.setTextDatum(TL_DATUM);
}

static void drawBatteryChip(int x, int y) {
  char buf[8];
  snprintf(buf, sizeof(buf), "--"); // No battery measurement in this hardware.

  tft.fillRoundRect(x, y, 42, 22, 4, C_CARD);
  tft.drawRoundRect(x, y, 42, 22, 4, C_BORDER);
  tft.fillRoundRect(x - 3, y + 7, 4, 8, 2, C_BORDER);

  tft.setFreeFont(&RubikBold12);
  tft.setTextColor(C_TEXT_DARK, C_CARD);
  tft.setTextDatum(MC_DATUM);
  tft.drawString(buf, x + 21, y + 12);
  tft.setTextDatum(TL_DATUM);
}

static const GFXfont *rubikBySize(uint8_t size) {
  switch (size) {
    case 62: return &RubikBold62;
    case 42: return &RubikBold42;
    case 32: return &RubikBold32;
    case 24: return &RubikBold24;
    case 20: return &RubikBold20;
    case 18: return &RubikBold18;
    case 15: return &RubikBold15;
    case 12: return &RubikBold12;
    case 10: return &RubikBold10;
    default: return &RubikBold8;
  }
}

static uint8_t pickLargestRubik(const char *text, int maxW, int maxH,
                                const uint8_t *sizes, int count) {
  for (int i = 0; i < count; i++) {
    tft.setFreeFont(rubikBySize(sizes[i]));
    if (tft.fontHeight() <= maxH && tft.textWidth(text) <= maxW) {
      return sizes[i];
    }
  }
  return sizes[count - 1];
}

static void drawRubik(const char *text, int x, int y, uint8_t size,
                      uint16_t color, uint16_t bg, uint8_t datum = TL_DATUM) {
  tft.setFreeFont(rubikBySize(size));
  tft.setTextColor(color, bg);
  tft.setTextDatum(datum);
  tft.drawString(text, x, y);
  tft.setTextDatum(TL_DATUM);
}

static void drawFittedLabel(const char *text, int x, int y, int maxW,
                            uint16_t color, uint16_t bg,
                            const uint8_t *sizes, int count) {
  uint8_t size = sizes[count - 1]; // smallest
  for (int i = 0; i < count; i++) {
    tft.setFreeFont(rubikBySize(sizes[i]));
    if (tft.textWidth(text) <= maxW) {
      size = sizes[i];
      break;
    }
  }
  tft.setFreeFont(rubikBySize(size));
  tft.setTextColor(color, bg);
  tft.setTextDatum(TL_DATUM);
  tft.drawString(text, x, y);
}

static void drawFittedValue(const char *text, int x, int y, int w, int h,
                            uint16_t color, uint16_t bg,
                            const uint8_t *sizes, int count,
                            int yNudge = 0, bool rightAligned = false) {
  int top = 0, bottom = 0;
  // Fit and centre visible glyphs, not unused ascender/descender space.
  for (int i = 0; i < count; ++i) {
    const GFXfont *font = rubikBySize(sizes[i]);
    tft.setFreeFont(font);
    top = 127; bottom = -127;
    for (const char *p = text; *p; ++p) {
      const GFXglyph &g = font->glyph[(uint8_t)*p - font->first];
      if (!g.height) continue;
      if (g.yOffset < top) top = g.yOffset;
      if (g.yOffset + g.height > bottom) bottom = g.yOffset + g.height;
    }
    if (tft.textWidth(text) <= w && bottom - top <= h) break;
  }
  // The card is already filled. Equal foreground/background disables GFX's
  // full-font background rectangle, which can extend below the number box.
  (void)bg;
  tft.setTextColor(color, color);
  tft.setTextDatum(rightAligned ? R_BASELINE : C_BASELINE);
  tft.drawString(text, rightAligned ? x + w : x + w / 2,
                 y + (h - (bottom - top)) / 2 - top + yNudge);
  tft.setTextDatum(TL_DATUM);
}

static uint16_t clampU16(float value, uint16_t maxValue) {
  if (value < 0.0f) return 0;
  if (value > (float)maxValue) return maxValue;
  return (uint16_t)round(value);
}

static int32_t displayIntValue(const SensorSample &sample, DataField field) {
  float value = fieldValueFloat(sample, field);

  switch (field) {
    case DataField::PM1_0:
    case DataField::PM2_5:
    case DataField::PM4_0:
    case DataField::PM10_0:
      return clampU16(value, MAX_DISPLAY_PM);
    case DataField::VOC_INDEX:
      return clampU16(value, MAX_DISPLAY_VOC);
    case DataField::CO2:
      return clampU16(value, MAX_DISPLAY_CO2);
    case DataField::AQI:
      return clampU16(value, MAX_DISPLAY_AQI);
    case DataField::HUMIDITY:
      return clampU16(value, 100);
    case DataField::TEMPERATURE:
      return (int32_t)round(value);
    case DataField::NOX_INDEX:
      return clampU16(value, MAX_DISPLAY_VOC);
    default:
      return 0;
  }
}

static void drawCardBorder(int x, int y, int w, int h, int radius,
                           bool selected) {
  tft.drawRoundRect(x, y, w, h, radius, C_BORDER);
  if (selected) {
    tft.drawRoundRect(x - 1, y - 1, w + 2, h + 2, radius + 1, C_SELECT);
    tft.drawRoundRect(x - 2, y - 2, w + 4, h + 4, radius + 2, C_SELECT);
  } else {
    tft.drawRoundRect(x - 1, y - 1, w + 2, h + 2, radius + 1, C_BG);
    tft.drawRoundRect(x - 2, y - 2, w + 4, h + 4, radius + 2, C_BG);
  }
}

static void fillCard(int x, int y, int w, int h, int radius, uint16_t color,
                     bool selected) {
  tft.fillRoundRect(x, y, w, h, radius, color);
  drawCardBorder(x, y, w, h, radius, selected);
}

static uint16_t pmPanelColor(const SensorSample &sample) {
  return aqiColor(sample.aqi);
}

static const char *aqiCategoryShort(uint16_t aqi) {
  if (aqi <= 50) return "Good";
  if (aqi <= 100) return "Moderate";
  if (aqi <= 150) return "USG";
  if (aqi <= 200) return "Unhealthy";
  if (aqi <= 300) return "Very Unh";
  return "Hazardous";
}

static void drawHeader(const SensorSample &sample, DataField cursor,
                       bool recording, bool bleConnected) {
  uint16_t aqiVal = displayIntValue(sample, DataField::AQI);
  uint16_t bg = aqiColor(aqiVal);
  char buf[8];
  formatCompactValue(buf, sizeof(buf), aqiVal);
  static const uint8_t aqiSizes[] = {62, 42, 32};

  fillCard(4, 4, 232, 88, 4, bg, cursor == DataField::AQI);

  drawRubik("AQI", 10, 28, 24, textOnColor(bg), bg, L_BASELINE);

  // README reference: large three-digit AQI, centred between label/status.
  drawFittedValue(buf, 56, 12, 128, 54, textOnColor(bg), bg,
                  aqiVal > 999 ? aqiSizes + 1 : aqiSizes,
                  aqiVal > 999 ? 2 : 3);

  drawRubik(aqiCategoryShort(aqiVal), 120, 82, 15, textOnColor(bg), bg, C_BASELINE);

  drawStatusChip(184, 10, "REC", recording, C_REC_RED);
  drawStatusChip(184, 35, "BLE", bleConnected, C_BLE_BLUE);
  drawBatteryChip(184, 60);
}

static void drawPmRow(int y, const char *label, uint16_t value,
                      uint16_t bg) {
  char buf[8];
  formatCompactValue(buf, sizeof(buf), value);
  static const uint8_t valueSizes[] = {32, 24, 20};

  static const uint8_t labelSizes[] = {15};
  drawFittedValue(label, 10, y - 16, 30, 32, textOnColor(bg), bg, labelSizes, 1);

  drawFittedValue(buf, 44, y - 16, 66, 32, textOnColor(bg), bg,
                  valueSizes, 3, 0, true);
}

static void drawPmPanel(const SensorSample &sample, DataField cursor) {
  uint16_t bg = pmPanelColor(sample);
  fillCard(4, 96, 114, 164, 4, bg, isPmField(cursor));

  drawRubik("PM", 12, 113, 15, textOnColor(bg), bg, L_BASELINE);
  
  tft.setFreeFont(rubikBySize(12));
  int unitW = tft.textWidth("ug/m3");
  drawRubik("ug/m3", 110 - unitW, 113, 12, textOnColor(bg), bg, L_BASELINE);

  drawPmRow(142, "1.0", displayIntValue(sample, DataField::PM1_0), bg);
  drawPmRow(175, "2.5", displayIntValue(sample, DataField::PM2_5), bg);
  drawPmRow(208, "4.0", displayIntValue(sample, DataField::PM4_0), bg);
  drawPmRow(241, "10", displayIntValue(sample, DataField::PM10_0), bg);
}

static void drawSmallMetricCard(int x, int y, int w, int h, DataField field,
                                const SensorSample &sample,
                                DataField cursor, bool enabled) {
  int32_t value = displayIntValue(sample, field);
  uint16_t bg = enabled ? getHealthColor(field, value) : C_GEAR_BG;
  char buf[8];
  if (enabled) {
    formatCompactValue(buf, sizeof(buf), value);
  } else {
    snprintf(buf, sizeof(buf), "--");
  }
  static const uint8_t valueSizes[] = {32, 24, 20};

  fillCard(x, y, w, h, 4, bg, cursor == field);

  tft.setFreeFont(rubikBySize(12));
  int unitW = tft.textWidth(fieldUnit(field));
  drawRubik(fieldLabel(field), x + 8, y + 16, 15, textOnColor(bg), bg, L_BASELINE);
  drawRubik(fieldUnit(field), x + w - 6 - unitW, y + 16, 12, textOnColor(bg), bg, L_BASELINE);

  drawFittedValue(buf, x + 6, y + 22, w - 12, h - 26, textOnColor(bg), bg,
                  valueSizes, 3, 0, true);
}

static void drawBottomMetricCard(int x, int y, int w, int h, DataField field,
                                 const SensorSample &sample,
                                 DataField cursor, bool enabled) {
  int32_t value = displayIntValue(sample, field);
  uint16_t bg = enabled ? getHealthColor(field, value) : C_GEAR_BG;
  char buf[10];

  if (!enabled) {
    snprintf(buf, sizeof(buf), "--");
  } else if (field == DataField::TEMPERATURE) {
    snprintf(buf, sizeof(buf), "%ldC", (long)value);
  } else if (field == DataField::HUMIDITY) {
    snprintf(buf, sizeof(buf), "%ld%%", (long)value);
  } else {
    formatCompactValue(buf, sizeof(buf), value);
  }

  fillCard(x, y, w, h, 4, bg, cursor == field);

  const char *label = fieldLabel(field);
  static const uint8_t valueSizes[] = {32, 24, 20};

  drawRubik(label, x + w / 2, y + 16, 12, textOnColor(bg), bg, C_BASELINE);

  drawFittedValue(buf, x + 6, y + 22, w - 12, h - 26, textOnColor(bg), bg,
                  valueSizes, 3, 0);
}

static ScreenMode lastScreenMode = (ScreenMode)-1;
static DataField lastCursorField = (DataField)-1;
static uint32_t lastTimestamp = 0xFFFFFFFF;
static uint16_t lastAqiValue = 0xFFFF;
static bool lastRecording = false;
static bool lastBleConnected = false;

void display_home(const SensorSample &current, DataField cursor,
                  bool recording, bool bleConnected, bool hasCo2, bool hasNox,
                  bool hasEnvironment) {
  static SensorSample previous{};
  DataField oldCursor = lastCursorField;
  bool modeChanged = (lastScreenMode != ScreenMode::HOME);
  if (lastScreenMode != ScreenMode::HOME) {
    lastScreenMode = ScreenMode::HOME;
    tft.fillScreen(C_BG);
  }

  bool dataChanged = (current.timestamp != lastTimestamp);
  bool cursorChanged = (cursor != lastCursorField);
  bool aqiChanged = (displayIntValue(current, DataField::AQI) != lastAqiValue);
  bool statusChanged = (recording != lastRecording || bleConnected != lastBleConnected);

  if (!modeChanged && !dataChanged && !cursorChanged && !statusChanged && !aqiChanged) {
    return; // Nothing to update
  }

  lastTimestamp = current.timestamp;
  lastCursorField = cursor;
  lastAqiValue = displayIntValue(current, DataField::AQI);
  lastRecording = recording;
  lastBleConnected = bleConnected;

  auto selectionChanged = [&](DataField field) {
    return cursorChanged && (cursor == field || oldCursor == field);
  };
  if (modeChanged || aqiChanged || statusChanged || selectionChanged(DataField::AQI))
    drawHeader(current, cursor, recording, bleConnected);
  if (modeChanged || aqiChanged || current.pm1p0 != previous.pm1p0 ||
      current.pm2p5 != previous.pm2p5 || current.pm4p0 != previous.pm4p0 ||
      current.pm10p0 != previous.pm10p0 ||
      (cursorChanged && (isPmField(cursor) || isPmField(oldCursor))))
    drawPmPanel(current, cursor);
  if (modeChanged || selectionChanged(DataField::CO2))
    drawSmallMetricCard(122, 96, 114, 52, DataField::CO2, current, cursor, hasCo2);
  if (modeChanged || current.vocIndex != previous.vocIndex || selectionChanged(DataField::VOC_INDEX))
    drawSmallMetricCard(122, 152, 114, 52, DataField::VOC_INDEX, current, cursor, hasEnvironment);
  if (modeChanged || current.noxIndex != previous.noxIndex || selectionChanged(DataField::NOX_INDEX))
    drawSmallMetricCard(122, 208, 114, 52, DataField::NOX_INDEX, current, cursor, hasNox);
  if (modeChanged || current.temperature != previous.temperature || selectionChanged(DataField::TEMPERATURE))
    drawBottomMetricCard(4, 264, 89, 52, DataField::TEMPERATURE, current, cursor, hasEnvironment);
  if (modeChanged || current.humidity != previous.humidity || selectionChanged(DataField::HUMIDITY))
    drawBottomMetricCard(97, 264, 90, 52, DataField::HUMIDITY, current, cursor, hasEnvironment);
  previous = current;
  if (!modeChanged && !selectionChanged(DataField::SETTINGS)) return;

  bool settingsSelected = (cursor == DataField::SETTINGS);
  fillCard(191, 264, 45, 52, 4, C_GEAR_BG, settingsSelected);
  
  int cx = 213;
  int cy = 290;
  // Square-ended teeth on a solid gear body, with a clear circular bore.
  tft.fillCircle(cx, cy, 10, C_TEXT_WHITE);
  for (int tooth = 0; tooth < 8; ++tooth) {
    float angle = tooth * 3.14159265f / 4.0f;
    float ux = cosf(angle), uy = sinf(angle);
    int x[4], y[4];
    const float radius[] = {8, 14, 14, 8};
    const float tangent[] = {-3, -3, 3, 3};
    for (int i = 0; i < 4; ++i) {
      x[i] = cx + (int)roundf(radius[i] * ux - tangent[i] * uy);
      y[i] = cy + (int)roundf(radius[i] * uy + tangent[i] * ux);
    }
    tft.fillTriangle(x[0], y[0], x[1], y[1], x[2], y[2], C_TEXT_WHITE);
    tft.fillTriangle(x[0], y[0], x[2], y[2], x[3], y[3], C_TEXT_WHITE);
  }
  tft.fillCircle(cx, cy, 5, C_GEAR_BG);
}

// ---- Chart Screen ----
// Light theme chart, simple and effective

void display_chart(const DataBuffer &buf, DataField field, const SensorSample &current) {
  static DataField lastChartField = (DataField)-1;
  static size_t lastChartCount = (size_t)-1;
  static uint32_t lastChartTimestamp = 0;
  if (!chartFrameReady) {
    if (lastScreenMode != ScreenMode::CHART) {
      tft.fillScreen(C_BG);
      tft.setTextFont(2);
      tft.setTextColor(C_TEXT_DARK, C_BG);
      tft.drawString("Chart memory unavailable", 12, 140);
      lastScreenMode = ScreenMode::CHART;
    }
    return;
  }
  size_t count = buf.getCount();
  SensorSample newest{};
  if (count) buf.getSample(count - 1, newest);
  bool pmGroupChart = isPmField(field);
  static const DataField pmFields[] = {
    DataField::PM1_0, DataField::PM2_5, DataField::PM4_0, DataField::PM10_0
  };
  static const uint16_t pmColors[] = {
    C_CHART_PM1, C_CHART_PM25, C_CHART_PM4, C_CHART_PM10
  };

  bool fullRedraw = (lastScreenMode != ScreenMode::CHART || field != lastChartField);
  bool historyChanged = count != lastChartCount || newest.timestamp != lastChartTimestamp;
  static uint16_t lastPm25 = 0;
  bool valueChanged = pmGroupChart && current.pm2p5 != lastPm25;
  if (!fullRedraw && !historyChanged && !valueChanged) {
    return;
  }

  lastChartField = field;
  lastChartCount = count;
  lastChartTimestamp = newest.timestamp;
  lastPm25 = current.pm2p5;

  lastScreenMode = ScreenMode::CHART;
  for (int tileY = 0; tileY < 320; tileY += 160) {
  if (tileY == 160 && !fullRedraw && !historyChanged) continue;
  chartFrame.resetViewport();
  chartFrame.fillSprite(C_BG);
  chartFrame.setViewport(0, -tileY, 240, 320, true);

  chartFrame.fillRoundRect(7, 9, 228, 304, 9, C_SHADOW);
  chartFrame.fillRoundRect(6, 6, 228, 304, 9, C_CARD);
  chartFrame.drawRoundRect(6, 6, 228, 304, 9, C_BORDER);

  chartFrame.setTextFont(2);
  chartFrame.setTextColor(C_TEXT_DARK, C_CARD);
  char title[32];
  if (pmGroupChart) {
    snprintf(title, sizeof(title), "PM2.5 %s", fieldUnit(DataField::PM2_5));
  } else {
    snprintf(title, sizeof(title), "%s %s", fieldLabel(field), fieldUnit(field));
  }
  if (!pmGroupChart) chartFrame.drawString(title, 16, 14);

  if (pmGroupChart) {
    uint16_t bg = pmColor(fieldValueFloat(current, DataField::PM2_5));
    chartFrame.fillRoundRect(10, 10, 220, 86, 4, bg);
    chartFrame.drawRoundRect(10, 10, 220, 86, 4, C_BORDER);
    chartFrame.setFreeFont(rubikBySize(15));
    chartFrame.setTextColor(textOnColor(bg), bg);
    chartFrame.setTextDatum(L_BASELINE);
    chartFrame.drawString("PM2.5", 18, 30);
    chartFrame.setFreeFont(rubikBySize(12));
    chartFrame.drawString("ug/m3", 222 - chartFrame.textWidth("ug/m3"), 30);
    char value[12];
    // Keep PM2.5 in ug/m3, with a decimal at ordinary concentrations.
    float pm25 = fieldValueFloat(current, DataField::PM2_5);
    if (pm25 < 1000) snprintf(value, sizeof(value), "%.1f", pm25);
    else formatCompactValue(value, sizeof(value), (int32_t)round(pm25));
    const uint8_t sizes[] = {42, 32, 24};
    for (uint8_t size : sizes) {
      chartFrame.setFreeFont(rubikBySize(size));
      if (chartFrame.textWidth(value) <= 208) break;
    }
    chartFrame.setTextColor(textOnColor(bg), bg);
    chartFrame.setTextDatum(C_BASELINE);
    chartFrame.drawString(value, 120, 78);
    chartFrame.setTextDatum(TL_DATUM);
  }
  chartFrame.setTextFont(1);
  chartFrame.setTextColor(C_TEXT_LIGHT, C_CARD);
  if (pmGroupChart) {
    int legendX = 16;
    const char *labels[] = {"1.0", "2.5", "4.0", "10"};
    for (int i = 0; i < 4; i++) {
      chartFrame.fillRect(legendX, 103, 7, 4, pmColors[i]);
      chartFrame.drawString(labels[i], legendX + 10, 100);
      legendX += 38;
    }
  } else {
    chartFrame.drawString("history", 16, 32);
  }

  if (count < 2) {
    chartFrame.setTextFont(2);
    chartFrame.setTextColor(C_TEXT_MID, C_CARD);
    chartFrame.drawString("Waiting for data...", 54, 156);
    chartFrame.resetViewport();
    chartFrame.pushSprite(0, tileY);
    continue;
  }

  // Chart area
  const int CHART_X = 52;
  const int CHART_Y = pmGroupChart ? 122 : 54;
  const int CHART_W = 166;
  const int CHART_H = 272 - CHART_Y;
  const int CHART_BOTTOM = CHART_Y + CHART_H;

  chartFrame.fillRoundRect(CHART_X, CHART_Y, CHART_W, CHART_H, 6, 0xF7FF);
  chartFrame.drawRoundRect(CHART_X, CHART_Y, CHART_W, CHART_H, 6, C_BORDER);

  size_t numPoints = count;
  size_t startIdx = 0;
  if (numPoints > (size_t)(CHART_W - 2)) {
    startIdx = numPoints - (CHART_W - 2);
    numPoints = CHART_W - 2;
  }

  float minVal = 1e9f, maxVal = -1e9f;
  for (size_t i = 0; i < numPoints; i++) {
    SensorSample s;
    if (buf.getSample(startIdx + i, s)) {
      if (pmGroupChart) {
        for (int j = 0; j < 4; j++) {
          float v = fieldValueFloat(s, pmFields[j]);
          if (v < minVal) minVal = v;
          if (v > maxVal) maxVal = v;
        }
      } else {
        float v = fieldValueFloat(s, field);
        if (v < minVal) minVal = v;
        if (v > maxVal) maxVal = v;
      }
    }
  }

  float range = maxVal - minVal;
  if (range < 1.0f) range = 1.0f;
  minVal -= range * 0.1f;
  maxVal += range * 0.1f;
  range = maxVal - minVal;

  char lbl[12];
  chartFrame.setTextFont(1);
  chartFrame.setTextColor(C_TEXT_MID, C_CARD);

  formatCompactValue(lbl, sizeof(lbl), (int32_t)round(maxVal));
  chartFrame.drawString(lbl, 14, CHART_Y);

  float midVal = (minVal + maxVal) / 2.0f;
  formatCompactValue(lbl, sizeof(lbl), (int32_t)round(midVal));
  chartFrame.drawString(lbl, 14, CHART_Y + CHART_H / 2 - 8);

  formatCompactValue(lbl, sizeof(lbl), (int32_t)round(minVal));
  chartFrame.drawString(lbl, 14, CHART_BOTTOM - 16);

  for (int g = 0; g <= 4; g++) {
    int gy = CHART_Y + (CHART_H * g) / 4;
    for (int gx = CHART_X + 5; gx < CHART_X + CHART_W - 5; gx += 6) {
      chartFrame.drawPixel(gx, gy, C_BORDER);
    }
  }

  int lineCount = pmGroupChart ? 4 : 1;
  for (int line = 0; line < lineCount; line++) {
    DataField lineField = pmGroupChart ? pmFields[line] : field;
    uint16_t lineColor = pmGroupChart ? pmColors[line] : getHealthColor(field, midVal);
    int prevPx = -1, prevPy = -1;

    for (size_t i = 0; i < numPoints; i++) {
      SensorSample s;
      if (!buf.getSample(startIdx + i, s)) continue;

      float v = fieldValueFloat(s, lineField);
      int px = CHART_X + 1 + (int)(i * (CHART_W - 3) / (numPoints - 1));
      int py = CHART_BOTTOM - 1 - (int)(((v - minVal) / range) * (CHART_H - 2));

      if (py < CHART_Y + 1) py = CHART_Y + 1;
      if (py > CHART_BOTTOM - 1) py = CHART_BOTTOM - 1;

      if (prevPx >= 0) {
        chartFrame.drawLine(prevPx, prevPy, px, py, lineColor);
        chartFrame.drawLine(prevPx, prevPy + 1, px, py + 1, lineColor);
      }

      prevPx = px;
      prevPy = py;
    }
  }

  chartFrame.setTextFont(2);
  chartFrame.setTextColor(C_TEXT_LIGHT, C_CARD);
  SensorSample oldest{};
  buf.getSample(startIdx, oldest);
  snprintf(lbl, sizeof(lbl), "%lus ago", (unsigned long)((newest.timestamp - oldest.timestamp) / 1000));
  chartFrame.drawString(lbl, CHART_X, CHART_BOTTOM + 10);
  
  int nowW = chartFrame.textWidth("now");
  chartFrame.drawString("now", CHART_X + CHART_W - nowW, CHART_BOTTOM + 10);
  chartFrame.resetViewport();
  chartFrame.pushSprite(0, tileY);
  }
}
