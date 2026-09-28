#include "BatteryPwmReader.h"
#include <assert.h>
#include <stdio.h>
uint32_t fake_us=0;
bool fake_level=false;
void (*fake_isr)()=nullptr;
static void edge(bool high, uint32_t delta) {
 fake_us+=delta; fake_level=high; fake_isr();
}
static void frames(unsigned pct, unsigned n) {
 const unsigned high=battery_pwm_high_us(pct);
 for(unsigned i=0;i<n;++i) { edge(false,high);edge(true,10000-high); }
}
int main() {
 unsigned n;
 BatteryPwmReader::begin();
 assert(!BatteryPwmReader::read(n));
 edge(true,100);
 frames(0,2); assert(!BatteryPwmReader::read(n));
 frames(0,1); assert(BatteryPwmReader::read(n)&&n==0);
 frames(50,4); assert(BatteryPwmReader::read(n)&&n==50);
 frames(100,4); assert(BatteryPwmReader::read(n)&&n==100);
 fake_us+=100001; assert(!BatteryPwmReader::read(n));
 /* Resynchronize after a long disconnection, then cross micros() rollover. */
 fake_us=UINT32_MAX-15000; edge(true,0);
 frames(25,4); assert(BatteryPwmReader::read(n)&&n==25);
 edge(false,5000);edge(true,15000);assert(!BatteryPwmReader::read(n));
 frames(75,3);assert(BatteryPwmReader::read(n)&&n==75);
 puts("Receiver: acquisition, endpoints, timeout, rollover, malformed frames pass");
}
