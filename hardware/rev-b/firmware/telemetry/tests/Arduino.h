#pragma once
#include <stdint.h>
#define IRAM_ATTR
#define INPUT 0
#define CHANGE 1
extern uint32_t fake_us;
extern bool fake_level;
extern void (*fake_isr)();
inline uint32_t micros() { return fake_us; }
inline void noInterrupts() {}
inline void interrupts() {}
inline void pinMode(uint8_t, int) {}
inline int digitalPinToInterrupt(uint8_t p) { return p; }
inline int digitalRead(uint8_t) { return fake_level; }
inline void attachInterrupt(int, void (*f)(), int) { fake_isr=f; }
