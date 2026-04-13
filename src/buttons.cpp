#include "buttons.h"
#include <Arduino.h>

// Pin assignments
static constexpr uint8_t PIN_UP     = 20;
static constexpr uint8_t PIN_DOWN   = 21;
static constexpr uint8_t PIN_SELECT = 5;
static constexpr uint8_t PIN_RECORD = 3;

// Debounce interval in ms
static constexpr unsigned long DEBOUNCE_MS = 50;

struct ButtonState {
  uint8_t pin;
  Button id;
  bool lastReading;
  bool stableState;
  unsigned long lastChangeTime;
  bool fired;  // true if press event was already reported
};

static ButtonState buttons[] = {
  { PIN_UP,     Button::UP,     true, true, 0, false },
  { PIN_DOWN,   Button::DOWN,   true, true, 0, false },
  { PIN_SELECT, Button::SELECT, true, true, 0, false },
  { PIN_RECORD, Button::RECORD, true, true, 0, false },
};
static constexpr size_t NUM_BUTTONS = sizeof(buttons) / sizeof(buttons[0]);

void buttons_begin() {
  for (auto &b : buttons) {
    pinMode(b.pin, INPUT_PULLUP);
    b.lastReading = digitalRead(b.pin);
    b.stableState = b.lastReading;
    b.lastChangeTime = millis();
    b.fired = false;
  }
}

Button buttons_poll() {
  unsigned long now = millis();

  for (auto &b : buttons) {
    bool reading = digitalRead(b.pin);

    if (reading != b.lastReading) {
      b.lastChangeTime = now;
      b.lastReading = reading;
    }

    if ((now - b.lastChangeTime) >= DEBOUNCE_MS) {
      if (reading != b.stableState) {
        b.stableState = reading;
        b.fired = false;
      }

      // Active LOW — button is pressed when stableState is LOW
      if (!b.stableState && !b.fired) {
        b.fired = true;
        return b.id;
      }
      // Reset fired when released
      if (b.stableState) {
        b.fired = false;
      }
    }
  }

  return Button::NONE;
}
