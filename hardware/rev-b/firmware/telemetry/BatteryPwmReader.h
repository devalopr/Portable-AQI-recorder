#pragma once
#include <Arduino.h>
#include "battery_pwm.h"
/* Single receiver instance. GPIO21 on AQI Main PWM; USB logging only.
 * External 10k pull-up required. Example targets Arduino-ESP32/ESP32-C3.
 */
class BatteryPwmReader {
 public:
  static void begin(uint8_t pin = 21) {
    pin_ = pin;
    pinMode(pin_, INPUT);
    attachInterrupt(digitalPinToInterrupt(pin_), edge, CHANGE);
  }
  static bool read(unsigned &percent) {
    noInterrupts();
    const uint32_t h = high_, p = period_, t = last_, count = good_;
    interrupts();
    return count >= 3 && (uint32_t)(micros() - t) <= 100000u &&
           battery_pwm_decode(h, p, &percent);
  }
 private:
  static void IRAM_ATTR edge() {
    const uint32_t now = micros();
    if (digitalRead(pin_)) {
      if (have_rise_ && have_fall_) {
        const uint32_t period = now - rise_, high = fall_ - rise_;
        /* No library calls or division in the ISR. Decode in read(). */
        if (period >= 9000u && period <= 11000u && high < period &&
            high * 100u >= period * 9u && high * 100u <= period * 91u) {
          high_ = high; period_ = period; last_ = now;
          if (good_ < 3) ++good_;
        } else good_ = 0;
      } else good_ = 0;
      rise_ = now; have_rise_ = true; have_fall_ = false;
    } else if (have_rise_) { fall_ = now; have_fall_ = true; }
  }
  static uint8_t pin_;
  static volatile uint32_t rise_, fall_, high_, period_, last_, good_;
  static volatile bool have_rise_, have_fall_;
};
