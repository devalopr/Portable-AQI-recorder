#ifndef BATTERY_PWM_H
#define BATTERY_PWM_H
#include <stdbool.h>
#include <stdint.h>
/* Wire HIGH time: 1000us (empty) through 9000us (full), period 10000us. */
static inline uint16_t battery_pwm_high_us(unsigned percent) {
    return (uint16_t)(1000u + 80u * (percent > 100u ? 100u : percent));
}
static inline bool battery_pwm_decode(uint32_t high_us, uint32_t period_us,
                                      unsigned *percent) {
    if (!percent || period_us < 9000u || period_us > 11000u || high_us >= period_us)
        return false;
    uint32_t duty = (high_us * 10000u + period_us / 2u) / period_us;
    /* Allow 1 percentage point of wire-duty timing error at the endpoints. */
    if (duty < 900u || duty > 9100u) return false;
    if (duty < 1000u) duty = 1000u;
    if (duty > 9000u) duty = 9000u;
    *percent = (duty - 1000u + 40u) / 80u;
    return true;
}
/* CH32V003 driver; requires WCH GPIO/RCC/TIM standard peripheral library. */
bool battery_pwm_init(uint32_t timer_clock_hz);
void battery_pwm_submit(unsigned percent, bool valid);
void battery_pwm_tim2_irq(void);
#endif
