#include "display.h"
#include <TFT_eSPI.h>
#include <SPI.h>

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

static TFT_eSPI tft = TFT_eSPI();

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
  // TFT_eSPI ST7789 typically uses rotation 0 or 2 for portrait. 
  // With connector at the top, rotation 2 is usually correct.
  tft.setRotation(2);  
  tft.fillScreen(C_DARK_BG);
}

// ---- Home Screen ----
// Layout (portrait 240x320):
//   [0-54]   Header: AQI value large + category
//   [55-288] Data rows: 9 rows x 26px each
//   [289-319] Status bar: REC indicator + BLE icon

void display_home(const SensorSample &current, DataField cursor,
                  bool recording, bool bleConnected) {
  // --- Header: AQI ---
  uint16_t aqiVal = current.aqi;
  uint16_t acolor = aqiColor(aqiVal);

  tft.fillRect(0, 0, 240, 55, C_HEADER_BG);

  // AQI number — large
  char buf[16];
  snprintf(buf, sizeof(buf), "%d", aqiVal);
  tft.setTextFont(4); // 26 pixel high
  tft.setTextColor(C_CYAN);
  tft.drawString("AQI", 10, 8);
  tft.setTextColor(acolor);
  tft.drawString(buf, 70, 8);

  // Category text — small
  const char *cat;
  if (aqiVal <= 50)       cat = "Good";
  else if (aqiVal <= 100) cat = "Moderate";
  else if (aqiVal <= 150) cat = "USG";
  else if (aqiVal <= 200) cat = "Unhealthy";
  else if (aqiVal <= 300) cat = "Very Unhealthy";
  else                    cat = "Hazardous";

  tft.setTextFont(2); // 16 pixel high
  tft.setTextColor(acolor);
  tft.drawString(cat, 10, 36);

  // --- Data rows ---
  const int ROW_START_Y = 58;
  const int ROW_HEIGHT  = 26;
  const int NUM_FIELDS  = (int)DataField::_COUNT;

  for (int i = 0; i < NUM_FIELDS; i++) {
    DataField f = (DataField)i;
    int y = ROW_START_Y + i * ROW_HEIGHT;

    // Row background
    uint16_t bgColor = (f == cursor) ? C_HIGHLIGHT : C_DARK_BG;
    tft.fillRect(0, y, 240, ROW_HEIGHT - 2, bgColor);

    // Label
    tft.setTextFont(2);
    tft.setTextColor(C_CYAN);
    tft.drawString(fieldLabel(f), 8, y + 4);

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

    int textWidth = tft.textWidth(buf);
    int unitWidth = tft.textWidth(fieldUnit(f));
    
    int unitX = 240 - 8 - unitWidth;
    int valX = unitX - 8 - textWidth;

    uint16_t valColor = (f == DataField::AQI) ? aqiColor(aqiVal) : C_WHITE;
    tft.setTextColor(valColor);
    tft.drawString(buf, valX, y + 4);

    // Unit
    if (strlen(fieldUnit(f)) > 0) {
      tft.setTextColor(C_CYAN);
      tft.drawString(fieldUnit(f), unitX, y + 4);
    }
  }

  // --- Status bar ---
  int statusY = ROW_START_Y + NUM_FIELDS * ROW_HEIGHT + 2;
  tft.fillRect(0, statusY, 240, 320 - statusY, C_DARK_BG);

  if (recording) {
    tft.fillCircle(16, statusY + 10, 6, C_REC_RED);
    tft.setTextFont(2);
    tft.setTextColor(C_REC_RED);
    tft.drawString("REC", 28, statusY + 2);
  }

  if (bleConnected) {
    tft.setTextFont(2);
    tft.setTextColor(C_BLE_BLUE);
    tft.drawString("BLE", 200, statusY + 2);
  }
}

// ---- Chart Screen ----
// Full-screen chart: title at top, axis labels, plotted line

void display_chart(const DataBuffer &buf, DataField field) {
  tft.fillScreen(C_DARK_BG);

  // Title
  tft.setTextFont(2);
  tft.setTextColor(C_CYAN);
  char title[32];
  snprintf(title, sizeof(title), "%s %s", fieldLabel(field), fieldUnit(field));
  tft.drawString(title, 8, 4);

  size_t count = buf.getCount();
  if (count < 2) {
    tft.setTextColor(C_WHITE);
    tft.drawString("Waiting for data...", 40, 160);
    return;
  }

  // Chart area
  const int CHART_X = 40;   // left margin (for Y axis labels)
  const int CHART_Y = 28;   // top
  const int CHART_W = 240 - CHART_X - 6;  // width
  const int CHART_H = 320 - CHART_Y - 24; // height (leave room for X label)
  const int CHART_BOTTOM = CHART_Y + CHART_H;

  // Draw chart border
  tft.drawRect(CHART_X, CHART_Y, CHART_W, CHART_H, C_WHITE);

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
  tft.setTextFont(2);
  tft.setTextColor(C_WHITE);

  snprintf(lbl, sizeof(lbl), "%.0f", maxVal);
  tft.drawString(lbl, 2, CHART_Y);

  float midVal = (minVal + maxVal) / 2.0f;
  snprintf(lbl, sizeof(lbl), "%.0f", midVal);
  tft.drawString(lbl, 2, CHART_Y + CHART_H / 2 - 8);

  snprintf(lbl, sizeof(lbl), "%.0f", minVal);
  tft.drawString(lbl, 2, CHART_BOTTOM - 16);

  // Draw horizontal grid lines
  for (int g = 0; g <= 4; g++) {
    int gy = CHART_Y + (CHART_H * g) / 4;
    for (int gx = CHART_X + 2; gx < CHART_X + CHART_W; gx += 6) {
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
  tft.setTextFont(2);
  tft.setTextColor(C_WHITE);
  snprintf(lbl, sizeof(lbl), "%ds ago", (int)(numPoints));
  tft.drawString(lbl, CHART_X, CHART_BOTTOM + 6);
  
  int nowW = tft.textWidth("now");
  tft.drawString("now", CHART_X + CHART_W - nowW, CHART_BOTTOM + 6);
}
