#include "display.h"
#include <TFT_eSPI.h>
#include <SPI.h>

// --- Light Theme Colors (RGB565) ---
#define C_BG          0xFFFF  // Pure White background
#define C_CARD        0xFFFF  // Pure White card background
#define C_TEXT_DARK   0x0000  // Pure Black text
#define C_TEXT_LIGHT  0x7BEF  // Grey text for units
#define C_HIGHLIGHT   0x03E0  // Selection border (e.g., strong blue or dark green)
#define C_REC_RED     0xF800
#define C_BLE_BLUE    0x001F

// Health Colors
#define C_GOOD        0x0505  // Nice green
#define C_MODERATE    0xFDA0  // Yellow-orange
#define C_USG         0xFC00  // Orange
#define C_UNHEALTHY   0xF800  // Red
#define C_VERY_UNH    0x8010  // Purple
#define C_HAZARDOUS   0x8000  // Maroon

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
  tft.setRotation(2);
  tft.fillScreen(C_BG);
}

// ---- Layout bounds ----
struct Card {
  int x, y, w, h;
  DataField field;
};

// We place them in a nice dashboard layout
static const Card CARDS[] = {
  {6, 66, 111, 94, DataField::PM2_5},
  {123, 66, 111, 44, DataField::PM1_0},
  {123, 116, 111, 44, DataField::PM4_0},
  {6, 166, 228, 44, DataField::PM10_0},
  {6, 216, 111, 44, DataField::VOC_INDEX},
  {123, 216, 111, 44, DataField::CO2},
  {6, 266, 111, 44, DataField::TEMPERATURE},
  {123, 266, 111, 44, DataField::HUMIDITY}
};
static const int NUM_CARDS = sizeof(CARDS)/sizeof(CARDS[0]);

// ---- Drawing functions ----

static void drawCard(const Card &c, const SensorSample &sample, bool selected) {
  // Background
  tft.fillRoundRect(c.x, c.y, c.w, c.h, 6, C_CARD);

  // Border (Selection vs default)
  if (selected) {
    tft.drawRoundRect(c.x, c.y, c.w, c.h, 6, C_HIGHLIGHT);
    tft.drawRoundRect(c.x+1, c.y+1, c.w-2, c.h-2, 5, C_HIGHLIGHT); // Thicker border
  } else {
    tft.drawRoundRect(c.x, c.y, c.w, c.h, 6, 0xDEFB); // subtle border
  }

  // Label
  tft.setTextFont(2); // 16px
  tft.setTextColor(C_TEXT_DARK);
  tft.drawString(fieldLabel(c.field), c.x + 6, c.y + 6);

  // Unit (top right)
  tft.setTextFont(1); // 8px
  tft.setTextColor(C_TEXT_LIGHT);
  int unitW = tft.textWidth(fieldUnit(c.field));
  tft.drawString(fieldUnit(c.field), c.x + c.w - 6 - unitW, c.y + 10);

  // Value
  float val = fieldValueFloat(sample, c.field);
  char buf[16];
  if (c.field == DataField::TEMPERATURE) {
    int whole = (int)val;
    int frac = abs((int)(val * 10) % 10);
    snprintf(buf, sizeof(buf), "%d.%d", whole, frac);
  } else {
    // PM, VOC, NOX, CO2, HUMIDITY are all displayed as integers
    snprintf(buf, sizeof(buf), "%d", (int)round(val));
  }

  uint16_t vColor = getHealthColor(c.field, val);
  
  if (c.field == DataField::PM2_5) {
    // Large card
    tft.setTextFont(6); // 48px font
    tft.setTextColor(vColor);
    int vw = tft.textWidth(buf);
    tft.drawString(buf, c.x + (c.w - vw)/2, c.y + 38); // Centered vertically
  } else {
    // Normal card
    tft.setTextFont(4); // 26px font
    tft.setTextColor(vColor);
    int vw = tft.textWidth(buf);
    tft.drawString(buf, c.x + (c.w - vw)/2, c.y + 20);
  }
}

static ScreenMode lastScreenMode = (ScreenMode)-1;
static DataField lastCursorField = (DataField)-1;
static uint32_t lastTimestamp = 0xFFFFFFFF;

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

  if (!fullRedraw && !dataChanged && !cursorChanged) {
    return; // Nothing to update
  }

  lastTimestamp = current.timestamp;
  lastCursorField = cursor;

  // --- Banner: AQI ---
  if (fullRedraw || dataChanged) {
    uint16_t aqiVal = current.aqi;
    uint16_t acolor = aqiColor(aqiVal);

    tft.fillRoundRect(6, 6, 228, 54, 8, acolor);

    const char *cat;
    if (aqiVal <= 50)       cat = "Good";
    else if (aqiVal <= 100) cat = "Moderate";
    else if (aqiVal <= 150) cat = "USG";
    else if (aqiVal <= 200) cat = "Unhealthy";
    else if (aqiVal <= 300) cat = "Very Unhealthy";
    else                    cat = "Hazardous";

    tft.setTextFont(2); // 16px small label
    tft.setTextColor(C_CARD);
    tft.drawString("AQI", 14, 12);

    int catW = tft.textWidth(cat);
    tft.drawString(cat, 228 + 6 - 8 - catW, 12);

    char buf[16];
    snprintf(buf, sizeof(buf), "%03d", aqiVal);

    tft.setTextFont(4); // 26px large number
    tft.setTextColor(C_CARD);
    int numW = tft.textWidth(buf);
    tft.drawString(buf, 6 + (228 - numW)/2, 30);
  }

  // --- Grid of Cards ---
  for (int i = 0; i < NUM_CARDS; i++) {
    const Card &c = CARDS[i];
    if (fullRedraw || dataChanged || (cursorChanged && (c.field == cursor || c.field == lastCursorField))) {
      drawCard(c, current, (c.field == cursor));
    }
  }
}

// ---- Chart Screen ----
// Light theme chart, simple and effective

void display_chart(const DataBuffer &buf, DataField field) {
  if (lastScreenMode != ScreenMode::CHART) {
    tft.fillScreen(C_BG); // Light theme background
    lastScreenMode = ScreenMode::CHART;
  } else {
    // Already in chart mode, just clear chart area
    tft.fillRect(0, 24, 240, 320-24, C_BG);
  }

  tft.setTextFont(2);
  tft.setTextColor(C_TEXT_DARK); 
  char title[32];
  snprintf(title, sizeof(title), "%s %s", fieldLabel(field), fieldUnit(field));
  tft.drawString(title, 8, 4);

  size_t count = buf.getCount();
  if (count < 2) {
    tft.setTextColor(C_TEXT_DARK);
    tft.drawString("Waiting for data...", 40, 160);
    return;
  }

  // Chart area
  const int CHART_X = 40;
  const int CHART_Y = 28;
  const int CHART_W = 240 - CHART_X - 6;
  const int CHART_H = 320 - CHART_Y - 24;
  const int CHART_BOTTOM = CHART_Y + CHART_H;

  tft.drawRect(CHART_X, CHART_Y, CHART_W, CHART_H, C_TEXT_DARK);

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
  tft.setTextColor(C_TEXT_DARK);

  snprintf(lbl, sizeof(lbl), "%.0f", maxVal);
  tft.drawString(lbl, 2, CHART_Y);

  float midVal = (minVal + maxVal) / 2.0f;
  snprintf(lbl, sizeof(lbl), "%.0f", midVal);
  tft.drawString(lbl, 2, CHART_Y + CHART_H / 2 - 8);

  snprintf(lbl, sizeof(lbl), "%.0f", minVal);
  tft.drawString(lbl, 2, CHART_BOTTOM - 16);

  for (int g = 0; g <= 4; g++) {
    int gy = CHART_Y + (CHART_H * g) / 4;
    for (int gx = CHART_X + 2; gx < CHART_X + CHART_W; gx += 6) {
      tft.drawPixel(gx, gy, 0xDEFB); // Subtle grid for light theme
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
  tft.setTextColor(C_TEXT_DARK);
  snprintf(lbl, sizeof(lbl), "%ds ago", (int)(numPoints));
  tft.drawString(lbl, CHART_X, CHART_BOTTOM + 6);
  
  int nowW = tft.textWidth("now");
  tft.drawString("now", CHART_X + CHART_W - nowW, CHART_BOTTOM + 6);
}
