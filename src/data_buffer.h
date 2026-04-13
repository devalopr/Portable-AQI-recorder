#pragma once
#include <cstdint>
#include <cstddef>

/**
 * Compact sensor sample — 22 bytes.
 * Floats are stored as scaled integers to save RAM.
 */
struct SensorSample {
  uint16_t pm1p0;        // PM1.0 × 10
  uint16_t pm2p5;        // PM2.5 × 10
  uint16_t pm4p0;        // PM4.0 × 10
  uint16_t pm10p0;       // PM10.0 × 10
  uint16_t humidity;     // RH% × 100
  int16_t  temperature;  // °C × 100
  uint16_t vocIndex;     // raw
  uint16_t noxIndex;     // raw
  uint16_t aqi;          // computed AQI
  uint32_t timestamp;    // millis() offset from recording start
};

/**
 * Fixed-size ring buffer in RAM for SensorSample data.
 * Overwrites oldest samples when full.
 */
class DataBuffer {
public:
  /// Allocate the buffer. Call once in setup() after BLE/display init.
  /// Returns true if allocation succeeded.
  bool begin(size_t maxSamples);

  /// Add a sample. Overwrites oldest if buffer is full.
  void addSample(const SensorSample &sample);

  /// Get sample by index (0 = oldest available).
  /// Returns false if index is out of range.
  bool getSample(size_t index, SensorSample &out) const;

  /// Number of samples currently stored.
  size_t getCount() const;

  /// Maximum capacity.
  size_t getCapacity() const;

  /// Clear all samples.
  void clear();

  /// Whether recording is active.
  bool isRecording() const;
  void setRecording(bool on);

private:
  SensorSample *_buf = nullptr;
  size_t _capacity = 0;
  size_t _head = 0;     // next write position
  size_t _count = 0;
  bool _recording = false;
};
