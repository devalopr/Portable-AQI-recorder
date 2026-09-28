#include "battery_pwm.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
 unsigned n;
 for (unsigned p=0;p<=100;++p) {
  assert(battery_pwm_decode(battery_pwm_high_us(p),10000,&n) && n==p);
  /* Ratio decoding survives oscillator/receiver timing scale errors. */
  assert(battery_pwm_decode(battery_pwm_high_us(p)*11/10,11000,&n) && n==p);
 }
 assert(!battery_pwm_decode(0,10000,&n));
 assert(!battery_pwm_decode(10000,10000,&n));
 assert(!battery_pwm_decode(5000,20000,&n));
 assert(!battery_pwm_decode(5000,0,&n));
 assert(battery_pwm_high_us(101)==9000);
 puts("PWM protocol: endpoints, all percentages, clock scaling and invalid pulses pass");
}
