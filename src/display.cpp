#include "display.h"
#include <TFT_eSPI.h>
#include <SPI.h>

// --- Light Theme Colors (RGB565) ---
#define C_BG          0xFFFF  // white background
#define C_CARD        0xFFFF  // clean card surface
#define C_CARD_ALT    0xFFFF  // white status chip fill
#define C_SHADOW      0xFFFF  // keep the display plainly light
#define C_BORDER      0xDEFB  // subtle divider/border
#define C_TEXT_DARK   0x0000  // black text
#define C_TEXT_MID    0x5ACB  // secondary text
#define C_TEXT_LIGHT  0x8C51  // tertiary text / units
#define C_HIGHLIGHT   0x0473  // teal selection border
#define C_REC_RED     0xE986
#define C_BLE_BLUE    0x249F

// Health Colors
#define C_GOOD        0x0548  // green
#define C_MODERATE    0xCDE0  // yellow-orange
#define C_USG         0xFBE0  // orange
#define C_UNHEALTHY   0xE986  // red
#define C_VERY_UNH    0x7A1B  // purple
#define C_HAZARDOUS   0x7920  // maroon

static TFT_eSPI tft = TFT_eSPI();

// ---- Field helpers ----

const char *fieldLabel(DataField f) {
  switch (f) {
    case DataField::PM1_0:       return "PM 1.0";
    case DataField::PM2_5:       return "PM 2.5";
    case DataField::PM4_0:       return "PM 4.0";
    case DataField::PM10_0:      return "PM 10.0";
    case DataField::HUMIDITY:    return "Humidity";
    case DataField::TEMPERATURE: return "Temperature";
    case DataField::VOC_INDEX:   return "VOC Index";
    case DataField::NOX_INDEX:   return "NOx Index";
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
    case DataField::VOC_INDEX:   return "";
    case DataField::NOX_INDEX:   return "";
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
    case DataField::CO2:         return 480; // Placeholder
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
    case DataField::CO2:         return 480.0f; // Placeholder
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
  return (aqi <= 150) ? C_TEXT_DARK : C_CARD;
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
  if (t < 10.0f) return 0x03FF; // blue for cold
  if (t <= 28.0f) return C_GOOD;
  if (t <= 35.0f) return C_MODERATE;
  return C_UNHEALTHY;
}

static uint16_t humColor(float h) {
  if (h >= 30.0f && h <= 60.0f) return C_GOOD;
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

// ---- Init ----

void display_begin() {
  tft.begin();
  tft.invertDisplay(false);
  tft.setRotation(2);
  tft.fillScreen(C_BG);
}

// ---- Layout bounds ----
struct Card {
  int x, y, w, h;
  DataField field;
};

// Dashboard layout for a 240x320 portrait display.
static const Card CARDS[] = {
  {6,   68, 111, 98, DataField::PM2_5},
  {123, 68, 111, 48, DataField::PM1_0},
  {123, 122, 111, 48, DataField::PM4_0},
  {6,   172, 111, 74, DataField::VOC_INDEX},
  {123, 176, 111, 48, DataField::PM10_0},
  {123, 229, 111, 39, DataField::CO2},
  {6,   252, 111, 60, DataField::TEMPERATURE},
  {123, 273, 111, 39, DataField::HUMIDITY}
};
static const int NUM_CARDS = sizeof(CARDS)/sizeof(CARDS[0]);

// ---- Drawing functions ----

static void drawStatusChip(int x, int y, const char *label, bool active,
                           uint16_t activeColor) {
  uint16_t dotColor = active ? activeColor : C_BORDER;
  uint16_t textColor = active ? C_TEXT_DARK : C_TEXT_LIGHT;

  tft.fillRoundRect(x, y, 43, 16, 8, C_CARD_ALT);
  tft.drawRoundRect(x, y, 43, 16, 8, C_BORDER);
  tft.fillCircle(x + 8, y + 8, 3, dotColor);
  tft.setTextFont(1);
  tft.setTextColor(textColor, C_CARD_ALT);
  tft.drawString(label, x + 15, y + 4);
}

static int fontHeight(int font) {
  switch (font) {
    case 6: return 48;
    case 4: return 24;
    case 2: return 16;
    default: return 8;
  }
}

static int pickLargestFont(const char *text, int maxW, int maxH) {
  const int fonts[] = {6, 4, 2, 1};
  for (int i = 0; i < 4; i++) {
    tft.setTextFont(fonts[i]);
    if (fontHeight(fonts[i]) <= maxH && tft.textWidth(text) <= maxW) {
      return fonts[i];
    }
  }
  return 1;
}

static void drawFittedValue(const char *text, int x, int y, int w, int h,
                            uint16_t color, uint16_t bg, int yNudge = 0) {
  int font = pickLargestFont(text, w, h);

  tft.setTextFont(font);
  tft.setTextColor(color, bg);
  tft.setTextDatum(MC_DATUM);
  tft.drawString(text, x + w / 2, y + h / 2 + yNudge);
  tft.setTextDatum(TL_DATUM);
}

static bool showUnitInCard(DataField field) {
  return field != DataField::PM1_0 && field != DataField::PM4_0;
}

static void formatFieldValue(const Card &c, const SensorSample &sample,
                             char *buf, size_t bufSize, float &val) {
  val = fieldValueFloat(sample, c.field);
  if (c.field == DataField::TEMPERATURE) {
    int whole = (int)val;
    int frac = abs((int)(val * 10) % 10);
    snprintf(buf, bufSize, "%d.%d", whole, frac);
  } else {
    snprintf(buf, bufSize, "%d", (int)round(val));
  }
}

static void cardValueArea(const Card &c, int &x, int &y, int &w, int &h) {
  x = c.x + 5;
  w = c.w - 10;

  if (c.h <= 40) {
    y = c.y + 13;
    h = c.h - 15;
  } else if (c.h <= 50) {
    y = c.y + 13;
    h = c.h - 15;
  } else {
    y = c.y + 16;
    h = c.h - 20;
  }
}

static void drawCardValue(const Card &c, const SensorSample &sample) {
  float val;
  char buf[16];
  formatFieldValue(c, sample, buf, sizeof(buf), val);

  uint16_t vColor = getHealthColor(c.field, val);

  int valueX, valueY, valueW, valueH;
  cardValueArea(c, valueX, valueY, valueW, valueH);
  tft.fillRect(valueX, valueY, valueW, valueH, C_CARD);
  drawFittedValue(buf, valueX, valueY, valueW, valueH, vColor, C_CARD);
}

static void drawCard(const Card &c, const SensorSample &sample, bool selected) {
  tft.fillRoundRect(c.x, c.y, c.w, c.h, 7, C_CARD);

  if (selected) {
    tft.drawRoundRect(c.x, c.y, c.w, c.h, 7, C_HIGHLIGHT);
    tft.drawRoundRect(c.x + 1, c.y + 1, c.w - 2, c.h - 2, 6, C_HIGHLIGHT);
  } else {
    tft.drawRoundRect(c.x, c.y, c.w, c.h, 7, C_BORDER);
  }

  tft.setTextFont(1);
  tft.setTextColor(C_TEXT_MID, C_CARD);
  tft.drawString(fieldLabel(c.field), c.x + 7, c.y + 5);

  if (showUnitInCard(c.field)) {
    tft.setTextFont(1);
    tft.setTextColor(C_TEXT_LIGHT, C_CARD);
    int unitW = tft.textWidth(fieldUnit(c.field));
    tft.drawString(fieldUnit(c.field), c.x + c.w - 7 - unitW, c.y + 5);
  }

  drawCardValue(c, sample);
}

static ScreenMode lastScreenMode = (ScreenMode)-1;
static DataField lastCursorField = (DataField)-1;
static uint32_t lastTimestamp = 0xFFFFFFFF;
static uint16_t lastAqiValue = 0xFFFF;
static bool lastRecording = false;
static bool lastBleConnected = false;

void display_home(const SensorSample &current, DataField cursor,
                  bool recording, bool bleConnected) {
  
  bool fullRedraw = false;
  if (lastScreenMode != ScreenMode::HOME) {
    tft.fillScreen(C_BG);
    lastScreenMode = ScreenMode::HOME;
    fullRedraw = true;
  }

  bool dataChanged = (current.timestamp != lastTimestamp);
  bool cursorChanged = (cursor != lastCursorField);
  bool aqiChanged = (current.aqi != lastAqiValue);
  bool statusChanged = (recording != lastRecording || bleConnected != lastBleConnected);
  DataField previousCursorField = lastCursorField;

  if (!fullRedraw && !dataChanged && !cursorChanged && !statusChanged) {
    return; // Nothing to update
  }

  lastTimestamp = current.timestamp;
  lastCursorField = cursor;
  lastAqiValue = current.aqi;
  lastRecording = recording;
  lastBleConnected = bleConnected;

  // --- Header: AQI + status ---
  if (fullRedraw || aqiChanged || cursorChanged || statusChanged) {
    bool headerFullRedraw = fullRedraw || cursorChanged || statusChanged;
    uint16_t aqiVal = current.aqi;
    uint16_t acolor = aqiColor(aqiVal);
    uint16_t aqiInk = aqiTextColor(aqiVal);

    const char *cat;
    if (aqiVal <= 50)       cat = "Good";
    else if (aqiVal <= 100) cat = "Mod";
    else if (aqiVal <= 150) cat = "USG";
    else if (aqiVal <= 200) cat = "Unh";
    else if (aqiVal <= 300) cat = "V.Unh";
    else                    cat = "Haz";

    char buf[16];
    snprintf(buf, sizeof(buf), "%03d", aqiVal);

    if (headerFullRedraw) {
      tft.fillRoundRect(6, 4, 228, 58, 9, C_CARD);
      if (cursor == DataField::AQI) {
        tft.drawRoundRect(6, 4, 228, 58, 9, C_HIGHLIGHT);
        tft.drawRoundRect(7, 5, 226, 56, 8, C_HIGHLIGHT);
      } else {
        tft.drawRoundRect(6, 4, 228, 58, 9, C_BORDER);
      }

      tft.setTextFont(2);
      tft.setTextColor(C_TEXT_DARK, C_CARD);
      tft.drawString("AQI", 14, 12);

      drawStatusChip(186, 12, "REC", recording, C_REC_RED);
      drawStatusChip(186, 36, "BLE", bleConnected, C_BLE_BLUE);
    }

    tft.fillRect(14, 32, 40, 17, C_CARD);
    tft.setTextFont(2);
    tft.setTextColor(C_TEXT_MID, C_CARD);
    tft.drawString(cat, 14, 33);

    tft.fillRoundRect(58, 8, 104, 50, 8, acolor);
    drawFittedValue(buf, 64, 9, 92, 48, aqiInk, acolor, 3);
  }

  // --- Grid of Cards ---
  for (int i = 0; i < NUM_CARDS; i++) {
    const Card &c = CARDS[i];
    if (fullRedraw || dataChanged ||
        (cursorChanged && (c.field == cursor || c.field == previousCursorField))) {
      if (fullRedraw || cursorChanged) {
        drawCard(c, current, (c.field == cursor));
      } else {
        drawCardValue(c, current);
      }
    }
  }
}

// ---- Chart Screen ----
// Light theme chart, simple and effective

void display_chart(const DataBuffer &buf, DataField field) {
  static DataField lastChartField = (DataField)-1;
  static size_t lastChartCount = (size_t)-1;
  size_t count = buf.getCount();

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
  snprintf(title, sizeof(title), "%s %s", fieldLabel(field), fieldUnit(field));
  tft.drawString(title, 16, 14);

  tft.setTextFont(1);
  tft.setTextColor(C_TEXT_LIGHT, C_CARD);
  tft.drawString("history", 16, 32);

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
      float v = fieldValueFloat(s, field);
      if (v < minVal) minVal = v;
      if (v > maxVal) maxVal = v;
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

  int prevPx = -1, prevPy = -1;
  uint16_t lineColor = getHealthColor(field, midVal);

  for (size_t i = 0; i < numPoints; i++) {
    SensorSample s;
    if (!buf.getSample(startIdx + i, s)) continue;

    float v = fieldValueFloat(s, field);
    int px = CHART_X + 1 + (int)i;
    int py = CHART_BOTTOM - 1 - (int)(((v - minVal) / range) * (CHART_H - 2));

    if (py < CHART_Y + 1) py = CHART_Y + 1;
    if (py > CHART_BOTTOM - 1) py = CHART_BOTTOM - 1;

    if (prevPx >= 0) {
      tft.drawLine(prevPx, prevPy, px, py, lineColor);
    }

    prevPx = px;
    prevPy = py;
  }

  tft.setTextFont(2);
  tft.setTextColor(C_TEXT_LIGHT, C_CARD);
  snprintf(lbl, sizeof(lbl), "%ds ago", (int)(numPoints));
  tft.drawString(lbl, CHART_X, CHART_BOTTOM + 10);
  
  int nowW = tft.textWidth("now");
  tft.drawString("now", CHART_X + CHART_W - nowW, CHART_BOTTOM + 10);
}
