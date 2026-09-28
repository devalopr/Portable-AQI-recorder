#include <Arduino.h>
#include "BatteryPwmReader.h"
void setup() {
    Serial.begin(115200); // native USB CDC; do not start UART0 on GPIO21
    BatteryPwmReader::begin(21);
}
void loop() {
    unsigned percent;
    if (BatteryPwmReader::read(percent)) Serial.printf("Battery estimate: %u%%\n", percent);
    else Serial.println("Battery telemetry unavailable");
    delay(1000);
}
