#pragma once
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

// Compact display only; samples and BLE keep the complete numeric value.
inline void formatCompactValue(char *out, size_t size, int32_t value) {
  if (value > 999) {
    uint32_t tenths = (static_cast<uint32_t>(value) + 50) / 100;
    snprintf(out, size, "%lu.%luK", (unsigned long)(tenths / 10),
             (unsigned long)(tenths % 10));
  } else {
    snprintf(out, size, "%ld", (long)value);
  }
}
