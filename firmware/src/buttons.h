#pragma once
#include <cstdint>

/// Button events from the three front buttons (SW1 LEFT, SW2 OK, SW3 RIGHT).
enum class Button : uint8_t {
  NONE,
  LEFT,     // SW1 pressed
  RIGHT,    // SW3 pressed
  OK,       // SW2 released after a short press
  OK_LONG   // SW2 held for OK_LONG_MS (fires once, while still held)
};

/// Initialize button GPIOs. Call once in setup().
void buttons_begin();

/// Poll buttons. Returns the newest debounced event, or Button::NONE.
/// Call every loop iteration.
Button buttons_poll();
