#include "data_buffer.h"
#include <cstdlib>
#include <cstring>

bool DataBuffer::begin(size_t maxSamples) {
  _buf = (SensorSample *)malloc(maxSamples * sizeof(SensorSample));
  if (!_buf) return false;
  _capacity = maxSamples;
  _head = 0;
  _count = 0;
  _recording = false;
  return true;
}

void DataBuffer::addSample(const SensorSample &sample) {
  if (!_buf || _capacity == 0) return;
  _buf[_head] = sample;
  _head = (_head + 1) % _capacity;
  if (_count < _capacity) _count++;
}

bool DataBuffer::getSample(size_t index, SensorSample &out) const {
  if (!_buf || index >= _count) return false;
  // index 0 = oldest sample
  size_t pos;
  if (_count < _capacity) {
    pos = index;  // buffer hasn't wrapped yet
  } else {
    pos = (_head + index) % _capacity;  // wrapped — head points to oldest
  }
  out = _buf[pos];
  return true;
}

size_t DataBuffer::getCount() const { return _count; }
size_t DataBuffer::getCapacity() const { return _capacity; }

void DataBuffer::clear() {
  _head = 0;
  _count = 0;
}

bool DataBuffer::isRecording() const { return _recording; }
void DataBuffer::setRecording(bool on) { _recording = on; }
