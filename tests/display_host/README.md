# Display regression previews

The host harness compiles the real `src/display.cpp` against a raster backend and uses the firmware's exact Rubik GFX glyph bitmaps, text datums, and opaque background rectangles. It checks that number rendering does not overwrite card borders. Built-in chart fonts 1/2 are approximated with Rubik 8/15; this is a layout check, not an electrical/display timing simulator. The home layout reference is `assets/ui_4x_resolution.png`: 62-point AQI through 999, consistently 42-point compact thousands, right-aligned PM/gas numbers, and suffix units on temperature/humidity.

```sh
mkdir -p /tmp/aqi-display-review
c++ -std=c++11 -I tests/display_host tests/display_host/render.cpp src/data_buffer.cpp -o /tmp/aqi-display-review/render
/tmp/aqi-display-review/render /tmp/aqi-display-review
python3 tests/display_host/contact_sheet.py /tmp/aqi-display-review
```

Inspect the AQI and PM contact PNGs before flashing. Cases cover single/double/triple digits, 999, compact thousands through the SEN5x range's AQI maximum of 1844, and PM color boundaries. The metric-limit PPMs cover PM 999/1000, negative temperature, 100% humidity and 500 gas indices. Assertions cover number fitting, original 42-point AQI sizing, unchanged frames, partial navigation redraw, live-value-only chart updates, and new samples in a full buffer. Device serial `[UI]` messages report actual render time and available heap.
