#pragma once
#include <cstdint>

/// Button identifiers
enum class Button : uint8_t {
  NONE,
  UP,
  DOWN,
  SELECT,
  RECORD
};

/// Initialize button GPIOs. Call once in setup().
void buttons_begin();

/// Poll buttons. Returns the button that was just pressed (debounced),
/// or Button::NONE if nothing new. Call every loop iteration.
Button buttons_poll();
