#include "BatteryPwmReader.h"
uint8_t BatteryPwmReader::pin_ = 21;
volatile uint32_t BatteryPwmReader::rise_ = 0, BatteryPwmReader::fall_ = 0,
 BatteryPwmReader::high_ = 0, BatteryPwmReader::period_ = 0,
 BatteryPwmReader::last_ = 0, BatteryPwmReader::good_ = 0;
volatile bool BatteryPwmReader::have_rise_ = false, BatteryPwmReader::have_fall_ = false;
