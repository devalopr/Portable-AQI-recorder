#include "display.h"
#include <TFT_22_ILI9225.h>
#include <SPI.h>

// --- Pin definitions ---
#define TFT_RST  1
#define TFT_RS   0
#define TFT_CS   7
#define TFT_SDI  6   // MOSI
#define TFT_CLK  4   // SCK

// --- Colors (RGB565) ---
#define C_BLACK       0x0000
#define C_WHITE       0xFFFF
#define C_DARK_BG     0x18E3  // dark grey background
#define C_HEADER_BG   0x2945  // slightly lighter header
#define C_GREEN       0x07E0
#define C_YELLOW      0xFFE0
#define C_ORANGE      0xFD20
#define C_RED         0xF800
#define C_PURPLE      0x780F
#define C_MAROON      0x8000
#define C_CYAN        0x07FF
#define C_HIGHLIGHT   0x4A69  // row highlight
#define C_REC_RED     0xF800
#define C_BLE_BLUE    0x001F

static TFT_22_ILI9225 tft(TFT_RST, TFT_RS, TFT_CS, TFT_SDI, TFT_CLK);

// ---- Field helpers ----

const char *fieldLabel(DataField f) {
  switch (f) {
    case DataField::PM1_0:       return "PM1.0";
    case DataField::PM2_5:       return "PM2.5";
    case DataField::PM4_0:       return "PM4.0";
    case DataField::PM10_0:      return "PM10";
    case DataField::HUMIDITY:    return "RH";
    case DataField::TEMPERATURE: return "Temp";
    case DataField::VOC_INDEX:   return "VOC";
    case DataField::NOX_INDEX:   return "NOx";
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
    case DataField::AQI:         return (float)s.aqi;
    default:                     return 0.0f;
  }
}

// ---- AQI color ----

static uint16_t aqiColor(uint16_t aqi) {
  if (aqi <= 50)  return C_GREEN;
  if (aqi <= 100) return C_YELLOW;
  if (aqi <= 150) return C_ORANGE;
  if (aqi <= 200) return C_RED;
  if (aqi <= 300) return C_PURPLE;
  return C_MAROON;
}

// ---- Init ----

void display_begin() {
  tft.begin();
  tft.setOrientation(0);  // portrait: 176 wide × 220 tall
  tft.setBackgroundColor(C_DARK_BG);
  tft.clear();
}

// ---- Home Screen ----
// Layout (portrait 176×220):
//   [0-35]   Header: AQI value large + category
//   [36-215] Data rows: 9 rows × ~20px each
//   [216-219] Status bar: REC indicator + BLE icon

void display_home(const SensorSample &current, DataField cursor,
                  bool recording, bool bleConnected) {
  // --- Header: AQI ---
  uint16_t aqiVal = current.aqi;
  uint16_t acolor = aqiColor(aqiVal);

  tft.fillRectangle(0, 0, 175, 37, C_HEADER_BG);

  // AQI number — large
  char buf[16];
  snprintf(buf, sizeof(buf), "%d", aqiVal);
  tft.setFont(Terminal12x16);
  tft.drawText(4, 2, "AQI", C_CYAN);
  tft.drawText(50, 2, buf, acolor);

  // Category text — small
  const char *cat;
  if (aqiVal <= 50)       cat = "Good";
  else if (aqiVal <= 100) cat = "Moderate";
  else if (aqiVal <= 150) cat = "USG";
  else if (aqiVal <= 200) cat = "Unhealthy";
  else if (aqiVal <= 300) cat = "Very Unhealthy";
  else                    cat = "Hazardous";

  tft.setFont(Terminal6x8);
  tft.drawText(4, 24, cat, acolor);

  // --- Data rows ---
  const int ROW_START_Y = 40;
  const int ROW_HEIGHT  = 19;
  const int NUM_FIELDS  = (int)DataField::_COUNT;

  for (int i = 0; i < NUM_FIELDS; i++) {
    DataField f = (DataField)i;
    int y = ROW_START_Y + i * ROW_HEIGHT;

    // Row background
    uint16_t bgColor = (f == cursor) ? C_HIGHLIGHT : C_DARK_BG;
    tft.fillRectangle(0, y, 175, y + ROW_HEIGHT - 2, bgColor);

    // Label
    tft.setFont(Terminal6x8);
    tft.drawText(4, y + 4, fieldLabel(f), C_CYAN);

    // Value
    float val = fieldValueFloat(current, f);
    if (f == DataField::AQI || f == DataField::VOC_INDEX || f == DataField::NOX_INDEX) {
      snprintf(buf, sizeof(buf), "%d", (int)val);
    } else if (f == DataField::TEMPERATURE) {
      // Show one decimal
      int whole = (int)val;
      int frac = abs((int)(val * 10) % 10);
      snprintf(buf, sizeof(buf), "%d.%d", whole, frac);
    } else {
      int whole = (int)val;
      int frac = (int)(val * 10) % 10;
      snprintf(buf, sizeof(buf), "%d.%d", whole, frac);
    }

    // Right-align the value
    int textWidth = strlen(buf) * 6;
    int unitWidth = strlen(fieldUnit(f)) * 6;
    int valX = 175 - 4 - unitWidth - 4 - textWidth;
    if (valX < 60) valX = 60;

    uint16_t valColor = (f == DataField::AQI) ? aqiColor(aqiVal) : C_WHITE;
    tft.drawText(valX, y + 4, buf, valColor);

    // Unit
    if (strlen(fieldUnit(f)) > 0) {
      tft.drawText(175 - 4 - unitWidth, y + 4, fieldUnit(f), C_CYAN);
    }
  }

  // --- Status bar ---
  int statusY = ROW_START_Y + NUM_FIELDS * ROW_HEIGHT + 2;
  tft.fillRectangle(0, statusY, 175, 219, C_DARK_BG);

  if (recording) {
    tft.fillCircle(10, statusY + 7, 4, C_REC_RED);
    tft.setFont(Terminal6x8);
    tft.drawText(18, statusY + 3, "REC", C_REC_RED);
  }

  if (bleConnected) {
    tft.setFont(Terminal6x8);
    tft.drawText(150, statusY + 3, "BLE", C_BLE_BLUE);
  }
}

// ---- Chart Screen ----
// Full-screen chart: title at top, axis labels, plotted line

void display_chart(const DataBuffer &buf, DataField field) {
  tft.clear();

  // Title
  tft.setFont(Terminal6x8);
  char title[32];
  snprintf(title, sizeof(title), "%s %s", fieldLabel(field), fieldUnit(field));
  tft.drawText(4, 2, title, C_CYAN);

  size_t count = buf.getCount();
  if (count < 2) {
    tft.drawText(20, 100, "Waiting for data...", C_WHITE);
    return;
  }

  // Chart area
  const int CHART_X = 30;   // left margin (for Y axis labels)
  const int CHART_Y = 16;   // top
  const int CHART_W = 175 - CHART_X - 2;  // width
  const int CHART_H = 220 - CHART_Y - 16; // height (leave room for X label)
  const int CHART_BOTTOM = CHART_Y + CHART_H;

  // Draw chart border
  tft.drawRectangle(CHART_X, CHART_Y, CHART_X + CHART_W, CHART_BOTTOM, C_WHITE);

  // Determine how many points to plot (at most CHART_W pixels)
  size_t numPoints = count;
  size_t startIdx = 0;
  if (numPoints > (size_t)CHART_W) {
    startIdx = numPoints - CHART_W;
    numPoints = CHART_W;
  }

  // Find min/max for scaling
  float minVal = 1e9f, maxVal = -1e9f;
  for (size_t i = 0; i < numPoints; i++) {
    SensorSample s;
    if (buf.getSample(startIdx + i, s)) {
      float v = fieldValueFloat(s, field);
      if (v < minVal) minVal = v;
      if (v > maxVal) maxVal = v;
    }
  }

  // Add 10% padding
  float range = maxVal - minVal;
  if (range < 1.0f) range = 1.0f;
  minVal -= range * 0.1f;
  maxVal += range * 0.1f;
  range = maxVal - minVal;

  // Y-axis labels (min, mid, max)
  char lbl[12];
  tft.setFont(Terminal6x8);

  snprintf(lbl, sizeof(lbl), "%.0f", maxVal);
  tft.drawText(0, CHART_Y, lbl, C_WHITE);

  float midVal = (minVal + maxVal) / 2.0f;
  snprintf(lbl, sizeof(lbl), "%.0f", midVal);
  tft.drawText(0, CHART_Y + CHART_H / 2 - 4, lbl, C_WHITE);

  snprintf(lbl, sizeof(lbl), "%.0f", minVal);
  tft.drawText(0, CHART_BOTTOM - 8, lbl, C_WHITE);

  // Draw horizontal grid lines
  for (int g = 0; g <= 4; g++) {
    int gy = CHART_Y + (CHART_H * g) / 4;
    for (int gx = CHART_X + 2; gx < CHART_X + CHART_W; gx += 4) {
      tft.drawPixel(gx, gy, C_HIGHLIGHT);
    }
  }

  // Plot data
  int prevPx = -1, prevPy = -1;
  uint16_t lineColor = C_GREEN;

  for (size_t i = 0; i < numPoints; i++) {
    SensorSample s;
    if (!buf.getSample(startIdx + i, s)) continue;

    float v = fieldValueFloat(s, field);
    int px = CHART_X + 1 + (int)i;
    int py = CHART_BOTTOM - 1 - (int)(((v - minVal) / range) * (CHART_H - 2));

    // Clamp
    if (py < CHART_Y + 1) py = CHART_Y + 1;
    if (py > CHART_BOTTOM - 1) py = CHART_BOTTOM - 1;

    if (prevPx >= 0) {
      tft.drawLine(prevPx, prevPy, px, py, lineColor);
    }

    prevPx = px;
    prevPy = py;
  }

  // Bottom label
  tft.setFont(Terminal6x8);
  snprintf(lbl, sizeof(lbl), "%ds ago", (int)(numPoints));
  tft.drawText(CHART_X, CHART_BOTTOM + 4, lbl, C_WHITE);
  tft.drawText(CHART_X + CHART_W - 24, CHART_BOTTOM + 4, "now", C_WHITE);
}
