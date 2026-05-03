#include "display.h"
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
#define C_SELECT      RGB565(255, 239, 64)
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

static const uint16_t MAX_DISPLAY_AQI = 999;
static const uint16_t MAX_DISPLAY_PM = 999;
static const uint16_t MAX_DISPLAY_CO2 = 4000;
static const uint16_t MAX_DISPLAY_VOC = 500;
static const uint8_t PLACEHOLDER_BATTERY_PERCENT = 75;
static const uint16_t PLACEHOLDER_CO2_PPM = 1000;
static const uint16_t PLACEHOLDER_NOX_INDEX = 100;

static TFT_eSPI tft = TFT_eSPI();

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
    case DataField::NOX_INDEX:   return PLACEHOLDER_NOX_INDEX;
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
    case DataField::NOX_INDEX:   return (float)PLACEHOLDER_NOX_INDEX;
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

static uint16_t aqiTextColor(uint16_t aqi) {
  (void)aqi;
  return C_TEXT_WHITE;
}

static uint16_t pmColor(float pm25) {
  if (pm25 <= 12.0f) return C_GOOD;
  if (pm25 <= 35.4f) return C_MODERATE;
  if (pm25 <= 55.4f) return C_USG;
  if (pm25 <= 150.4f) return C_UNHEALTHY;
  if (pm25 <= 250.4f) return C_VERY_UNH;
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
}

// ---- Drawing functions ----

static void drawStatusChip(int x, int y, const char *label, bool active,
                           uint16_t activeColor) {
  uint16_t fill = active ? activeColor : C_TEXT_LIGHT;

  tft.fillRoundRect(x, y, 38, 21, 5, fill);
  tft.drawRoundRect(x, y, 38, 21, 5, C_BORDER);
  tft.setFreeFont(&RubikBold12);
  tft.setTextColor(C_TEXT_WHITE, fill);
  tft.setTextDatum(MC_DATUM);
  tft.drawString(label, x + 19, y + 11);
  tft.setTextDatum(TL_DATUM);
}

static void drawBatteryChip(int x, int y, uint8_t percent) {
  char buf[8];
  snprintf(buf, sizeof(buf), "%u%%", percent);

  tft.fillRoundRect(x, y, 38, 20, 5, C_CARD);
  tft.drawRoundRect(x, y, 38, 20, 5, C_BORDER);
  tft.fillRoundRect(x - 4, y + 7, 5, 7, 3, C_BORDER);

  tft.setFreeFont(&RubikBold12);
  tft.setTextColor(C_TEXT_DARK, C_CARD);
  tft.setTextDatum(MC_DATUM);
  tft.drawString(buf, x + 19, y + 10);
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

static void drawFittedValue(const char *text, int x, int y, int w, int h,
                            uint16_t color, uint16_t bg,
                            const uint8_t *sizes, int count,
                            int yNudge = 0) {
  uint8_t size = pickLargestRubik(text, w, h, sizes, count);

  tft.setFreeFont(rubikBySize(size));
  tft.setTextColor(color, bg);
  tft.setTextDatum(MC_DATUM);
  tft.drawString(text, x + w / 2, y + h / 2 + yNudge);
  tft.setTextDatum(TL_DATUM);
}

static uint16_t clampU16(float value, uint16_t maxValue) {
  if (value < 0.0f) return 0;
  if (value > (float)maxValue) return maxValue;
  return (uint16_t)round(value);
}

static uint16_t displayIntValue(const SensorSample &sample, DataField field) {
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
      if (value < 0.0f) return 0;
      if (value > 99.0f) return 99;
      return (uint16_t)round(value);
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
    tft.drawRoundRect(x + 2, y + 2, w - 4, h - 4, radius - 2, C_SELECT);
    tft.drawRoundRect(x + 3, y + 3, w - 6, h - 6, radius - 3, C_SELECT);
  }
}

static void fillCard(int x, int y, int w, int h, int radius, uint16_t color,
                     bool selected) {
  tft.fillRoundRect(x, y, w, h, radius, color);
  drawCardBorder(x, y, w, h, radius, selected);
}

static uint16_t pmPanelColor(const SensorSample &sample) {
  float pm1 = fieldValueFloat(sample, DataField::PM1_0);
  float pm25 = fieldValueFloat(sample, DataField::PM2_5);
  float pm4 = fieldValueFloat(sample, DataField::PM4_0);
  float pm10 = fieldValueFloat(sample, DataField::PM10_0);
  float worst = pm1;

  if (pm25 > worst) worst = pm25;
  if (pm4 > worst) worst = pm4;
  if (pm10 > worst) worst = pm10;
  return pmColor(worst);
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
  snprintf(buf, sizeof(buf), "%u", aqiVal);
  static const uint8_t aqiSizes[] = {62, 42, 32, 24};

  fillCard(4, 4, 232, 88, 4, bg, cursor == DataField::AQI);

  drawRubik("AQI", 10, 9, 20, C_TEXT_WHITE, bg);

  drawFittedValue(buf, 58, 6, 128, 58, aqiTextColor(aqiVal), bg,
                  aqiSizes, sizeof(aqiSizes), 0);

  drawRubik(aqiCategoryShort(aqiVal), 121, 80, 15, C_TEXT_WHITE, bg, MC_DATUM);

  drawStatusChip(194, 16, "REC", recording, C_REC_RED);
  drawStatusChip(194, 41, "BLE", bleConnected, C_BLE_BLUE);
  drawBatteryChip(194, 66, PLACEHOLDER_BATTERY_PERCENT);
}

static void drawPmRow(int y, const char *label, uint16_t value,
                      uint16_t bg) {
  char buf[8];
  snprintf(buf, sizeof(buf), "%u", value);
  static const uint8_t valueSizes[] = {32, 24, 20};

  drawRubik(label, 11, y, 15, C_TEXT_WHITE, bg, ML_DATUM);

  drawFittedValue(buf, 47, y - 18, 64, 36, C_TEXT_WHITE, bg,
                  valueSizes, sizeof(valueSizes), 0);
}

static void drawPmPanel(const SensorSample &sample, DataField cursor) {
  uint16_t bg = pmPanelColor(sample);
  fillCard(4, 96, 115, 164, 4, bg, isPmField(cursor));

  drawRubik("PM", 10, 102, 24, C_TEXT_WHITE, bg);
  drawRubik("ug/m3", 69, 103, 8, C_TEXT_WHITE, bg);

  drawPmRow(130, "1.0", displayIntValue(sample, DataField::PM1_0), bg);
  drawPmRow(174, "2.5", displayIntValue(sample, DataField::PM2_5), bg);
  drawPmRow(218, "4.0", displayIntValue(sample, DataField::PM4_0), bg);
  drawPmRow(248, "10.", displayIntValue(sample, DataField::PM10_0), bg);
}

static void drawSmallMetricCard(int x, int y, int w, int h, DataField field,
                                const SensorSample &sample,
                                DataField cursor) {
  uint16_t value = displayIntValue(sample, field);
  uint16_t bg = getHealthColor(field, value);
  char buf[8];
  snprintf(buf, sizeof(buf), "%u", value);
  static const uint8_t valueSizes[] = {32, 24, 20, 18};

  fillCard(x, y, w, h, 4, bg, cursor == field);

  drawRubik(fieldLabel(field), x + 6, y + 5, 20, C_TEXT_WHITE, bg);
  tft.setFreeFont(&RubikBold8);
  int unitW = tft.textWidth(fieldUnit(field));
  drawRubik(fieldUnit(field), x + w - 7 - unitW, y + 5, 8, C_TEXT_WHITE, bg);

  drawFittedValue(buf, x + 31, y + 19, w - 37, h - 22, C_TEXT_WHITE, bg,
                  valueSizes, sizeof(valueSizes), 0);
}

static void drawBottomMetricCard(int x, int y, int w, int h, DataField field,
                                 const SensorSample &sample,
                                 DataField cursor) {
  uint16_t value = displayIntValue(sample, field);
  uint16_t bg = getHealthColor(field, value);
  char buf[10];

  if (field == DataField::TEMPERATURE) {
    snprintf(buf, sizeof(buf), "%uC", value);
  } else if (field == DataField::HUMIDITY) {
    snprintf(buf, sizeof(buf), "%u%%", value);
  } else {
    snprintf(buf, sizeof(buf), "%u", value);
  }

  fillCard(x, y, w, h, 4, bg, cursor == field);

  const char *label = fieldLabel(field);
  uint8_t labelSize = 10;
  uint8_t valueSizes[] = {32, 24, 20};

  drawRubik(label, x + w / 2, y + 10, labelSize, C_TEXT_WHITE, bg, MC_DATUM);

  drawFittedValue(buf, x + 5, y + 18, w - 10, h - 20, C_TEXT_WHITE, bg,
                  valueSizes, sizeof(valueSizes), 0);
}

static ScreenMode lastScreenMode = (ScreenMode)-1;
static DataField lastCursorField = (DataField)-1;
static uint32_t lastTimestamp = 0xFFFFFFFF;
static uint16_t lastAqiValue = 0xFFFF;
static bool lastRecording = false;
static bool lastBleConnected = false;

void display_home(const SensorSample &current, DataField cursor,
                  bool recording, bool bleConnected) {
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

  drawHeader(current, cursor, recording, bleConnected);
  drawPmPanel(current, cursor);
  drawSmallMetricCard(122, 96, 114, 54, DataField::CO2, current, cursor);
  drawSmallMetricCard(122, 153, 114, 54, DataField::VOC_INDEX, current, cursor);
  drawSmallMetricCard(122, 210, 114, 50, DataField::NOX_INDEX, current, cursor);
  drawBottomMetricCard(4, 264, 89, 52, DataField::TEMPERATURE, current, cursor);
  drawBottomMetricCard(97, 264, 90, 52, DataField::HUMIDITY, current, cursor);

  fillCard(191, 264, 45, 52, 4, C_GEAR_BG, false);
  tft.fillRect(211, 273, 6, 9, C_TEXT_WHITE);
  tft.fillRect(211, 298, 6, 9, C_TEXT_WHITE);
  tft.fillRect(197, 287, 9, 6, C_TEXT_WHITE);
  tft.fillRect(222, 287, 9, 6, C_TEXT_WHITE);
  tft.fillRect(202, 278, 7, 7, C_TEXT_WHITE);
  tft.fillRect(219, 278, 7, 7, C_TEXT_WHITE);
  tft.fillRect(202, 295, 7, 7, C_TEXT_WHITE);
  tft.fillRect(219, 295, 7, 7, C_TEXT_WHITE);
  tft.fillCircle(214, 290, 12, C_TEXT_WHITE);
  tft.fillCircle(214, 290, 5, C_GEAR_BG);
}

// ---- Chart Screen ----
// Light theme chart, simple and effective

void display_chart(const DataBuffer &buf, DataField field) {
  static DataField lastChartField = (DataField)-1;
  static size_t lastChartCount = (size_t)-1;
  size_t count = buf.getCount();
  bool pmGroupChart = isPmField(field);
  static const DataField pmFields[] = {
    DataField::PM1_0, DataField::PM2_5, DataField::PM4_0, DataField::PM10_0
  };
  static const uint16_t pmColors[] = {
    C_CHART_PM1, C_CHART_PM25, C_CHART_PM4, C_CHART_PM10
  };

  bool fullRedraw = (lastScreenMode != ScreenMode::CHART || field != lastChartField);
  if (!fullRedraw && count == lastChartCount) {
    return;
  }

  lastChartField = field;
  lastChartCount = count;

  if (fullRedraw) {
    tft.fillScreen(C_BG);
    lastScreenMode = ScreenMode::CHART;
  } else {
    tft.fillRoundRect(6, 45, 228, 265, 9, C_CARD);
  }

  tft.fillRoundRect(7, 9, 228, 304, 9, C_SHADOW);
  tft.fillRoundRect(6, 6, 228, 304, 9, C_CARD);
  tft.drawRoundRect(6, 6, 228, 304, 9, C_BORDER);

  tft.setTextFont(2);
  tft.setTextColor(C_TEXT_DARK, C_CARD);
  char title[32];
  if (pmGroupChart) {
    snprintf(title, sizeof(title), "PM %s", fieldUnit(DataField::PM2_5));
  } else {
    snprintf(title, sizeof(title), "%s %s", fieldLabel(field), fieldUnit(field));
  }
  tft.drawString(title, 16, 14);

  tft.setTextFont(1);
  tft.setTextColor(C_TEXT_LIGHT, C_CARD);
  if (pmGroupChart) {
    int legendX = 16;
    const char *labels[] = {"1.0", "2.5", "4.0", "10"};
    for (int i = 0; i < 4; i++) {
      tft.fillRect(legendX, 35, 7, 4, pmColors[i]);
      tft.drawString(labels[i], legendX + 10, 32);
      legendX += 38;
    }
  } else {
    tft.drawString("history", 16, 32);
  }

  if (count < 2) {
    tft.setTextFont(2);
    tft.setTextColor(C_TEXT_MID, C_CARD);
    tft.drawString("Waiting for data...", 54, 156);
    return;
  }

  // Chart area
  const int CHART_X = 44;
  const int CHART_Y = 54;
  const int CHART_W = 174;
  const int CHART_H = 218;
  const int CHART_BOTTOM = CHART_Y + CHART_H;

  tft.fillRoundRect(CHART_X, CHART_Y, CHART_W, CHART_H, 6, 0xF7FF);
  tft.drawRoundRect(CHART_X, CHART_Y, CHART_W, CHART_H, 6, C_BORDER);

  size_t numPoints = count;
  size_t startIdx = 0;
  if (numPoints > (size_t)CHART_W) {
    startIdx = numPoints - CHART_W;
    numPoints = CHART_W;
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
  tft.setTextFont(2);
  tft.setTextColor(C_TEXT_MID, C_CARD);

  snprintf(lbl, sizeof(lbl), "%.0f", maxVal);
  tft.drawString(lbl, 14, CHART_Y);

  float midVal = (minVal + maxVal) / 2.0f;
  snprintf(lbl, sizeof(lbl), "%.0f", midVal);
  tft.drawString(lbl, 14, CHART_Y + CHART_H / 2 - 8);

  snprintf(lbl, sizeof(lbl), "%.0f", minVal);
  tft.drawString(lbl, 14, CHART_BOTTOM - 16);

  for (int g = 0; g <= 4; g++) {
    int gy = CHART_Y + (CHART_H * g) / 4;
    for (int gx = CHART_X + 5; gx < CHART_X + CHART_W - 5; gx += 6) {
      tft.drawPixel(gx, gy, C_BORDER);
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
      int px = CHART_X + 1 + (int)i;
      int py = CHART_BOTTOM - 1 - (int)(((v - minVal) / range) * (CHART_H - 2));

      if (py < CHART_Y + 1) py = CHART_Y + 1;
      if (py > CHART_BOTTOM - 1) py = CHART_BOTTOM - 1;

      if (prevPx >= 0) {
        tft.drawLine(prevPx, prevPy, px, py, lineColor);
        tft.drawLine(prevPx, prevPy + 1, px, py + 1, lineColor);
      }

      prevPx = px;
      prevPy = py;
    }
  }

  tft.setTextFont(2);
  tft.setTextColor(C_TEXT_LIGHT, C_CARD);
  snprintf(lbl, sizeof(lbl), "%ds ago", (int)(numPoints));
  tft.drawString(lbl, CHART_X, CHART_BOTTOM + 10);
  
  int nowW = tft.textWidth("now");
  tft.drawString("now", CHART_X + CHART_W - nowW, CHART_BOTTOM + 10);
}
