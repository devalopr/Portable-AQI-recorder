#include "buttons.h"
#include <Arduino.h>

// Main board Rev B: the buttons pull their GPIO low; R3, R2 and R4 (10k) are the pull-ups.
// All three are ESP32-C3 strapping pins, which is why the board has external pull-ups:
// holding OK (GPIO9) at reset enters the ROM bootloader; don't hold LEFT or RIGHT at reset.
static constexpr uint8_t PIN_LEFT  = 8;   // SW1
static constexpr uint8_t PIN_OK    = 9;   // SW2
static constexpr uint8_t PIN_RIGHT = 2;   // SW3

static constexpr unsigned long DEBOUNCE_MS = 30;
static constexpr unsigned long OK_LONG_MS  = 800;

struct ButtonState {
  uint8_t pin;
  bool lastReading;       // raw level, HIGH = released
  bool pressed;           // debounced state
  unsigned long lastChangeMs;
  unsigned long pressedAtMs;
  bool longFired;
};

static ButtonState left  = {PIN_LEFT,  true, false, 0, 0, false};
static ButtonState ok    = {PIN_OK,    true, false, 0, 0, false};
static ButtonState right = {PIN_RIGHT, true, false, 0, 0, false};

// Returns +1 on a debounced press, -1 on a debounced release, 0 otherwise.
static int debounce(ButtonState &b, unsigned long now) {
  bool reading = digitalRead(b.pin);
  if (reading != b.lastReading) {
    b.lastReading = reading;
    b.lastChangeMs = now;
  }
  if (now - b.lastChangeMs < DEBOUNCE_MS) return 0;
  bool pressedNow = (reading == LOW);
  if (pressedNow == b.pressed) return 0;
  b.pressed = pressedNow;
  if (pressedNow) {
    b.pressedAtMs = now;
    b.longFired = false;
    return 1;
  }
  return -1;
}

void buttons_begin() {
  for (ButtonState *b : {&left, &ok, &right}) {
    pinMode(b->pin, INPUT);           // external pull-ups on the board
    b->lastReading = digitalRead(b->pin);
    // A button already held at boot (e.g. OK after a bootloader entry) must be
    // released before it can fire.
    b->pressed = (b->lastReading == LOW);
    b->longFired = b->pressed;
    b->lastChangeMs = millis();
  }
}

Button buttons_poll() {
  unsigned long now = millis();

  if (debounce(left, now) == 1) return Button::LEFT;
  if (debounce(right, now) == 1) return Button::RIGHT;

  int okEdge = debounce(ok, now);
  if (ok.pressed && !ok.longFired && now - ok.pressedAtMs >= OK_LONG_MS) {
    ok.longFired = true;
    return Button::OK_LONG;
  }
  if (okEdge == -1) {
    bool wasLong = ok.longFired;
    ok.longFired = false;
    if (!wasLong) return Button::OK;
  }
  return Button::NONE;
}
