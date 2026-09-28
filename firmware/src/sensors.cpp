#include "sensors.h"

#include <SensirionI2CSen5x.h>
#include <SensirionI2cScd4x.h>
#include <SensirionI2cSen63c.h>
#include <SensirionI2cSen65.h>
#include <SensirionI2cSen66.h>
#include <SensirionI2cSen68.h>

// I2C addresses (Sensirion datasheets / drivers).
static constexpr uint8_t ADDR_SEN5X = 0x69;
static constexpr uint8_t ADDR_SEN6X = 0x6B;
static constexpr uint8_t ADDR_SCD4X = 0x62;

static SensirionI2CSen5x sen5x;
static SensirionI2cSen63c sen63c;
static SensirionI2cSen65 sen65;
static SensirionI2cSen66 sen66;
static SensirionI2cSen68 sen68;
static SensirionI2cScd4x scd4x;

static TwoWire *bus = nullptr;
static PmSensor pmType = PmSensor::NONE;
static bool scdFitted = false;
static const char *scdName = "none";
static uint16_t scdCo2 = 0;   // last SCD4x reading; it updates every 5 s

static bool present(uint8_t addr) {
  bus->beginTransmission(addr);
  return bus->endTransmission() == 0;
}

// ---- SEN5x (J3) ----

static PmSensor startSen5x() {
  sen5x.begin(*bus);
  if (sen5x.deviceReset()) return PmSensor::NONE;
  delay(100);
  unsigned char name[32] = {0};
  PmSensor type = PmSensor::SEN50;   // SEN50 has no product-name variant suffix to rely on
  if (!sen5x.getProductName(name, sizeof(name))) {
    String s = String((char *)name);
    s.trim();
    if (s == "SEN55") type = PmSensor::SEN55;
    else if (s == "SEN54") type = PmSensor::SEN54;
  }
  if (sen5x.startMeasurement()) return PmSensor::NONE;
  return type;
}

// ---- SEN6x (J4) ----
// Every SEN6x answers the same product-name command, so any driver can identify it.

static PmSensor startSen6x() {
  sen66.begin(*bus, ADDR_SEN6X);
  if (sen66.deviceReset()) return PmSensor::NONE;
  delay(1200);                       // SEN6x device-reset time
  int8_t name[32] = {0};
  if (sen66.getProductName(name, sizeof(name))) return PmSensor::NONE;
  String s = String((const char *)name);
  s.trim();
  int16_t err;
  PmSensor type;
  if (s == "SEN66") {
    type = PmSensor::SEN66; err = sen66.startContinuousMeasurement();
  } else if (s == "SEN63C") {
    sen63c.begin(*bus, ADDR_SEN6X); type = PmSensor::SEN63C; err = sen63c.startContinuousMeasurement();
  } else if (s == "SEN65") {
    sen65.begin(*bus, ADDR_SEN6X); type = PmSensor::SEN65; err = sen65.startContinuousMeasurement();
  } else if (s == "SEN68") {
    sen68.begin(*bus, ADDR_SEN6X); type = PmSensor::SEN68; err = sen68.startContinuousMeasurement();
  } else {
    Serial.printf("[SENS] Unknown SEN6x product name '%s'\n", s.c_str());
    return PmSensor::NONE;
  }
  return err ? PmSensor::NONE : type;
}

// SEN6x reports "not available yet" as all-ones raw values; the drivers only scale them.
static float pmOrNan(float v)  { return v >= 6553.4f ? NAN : v; }   // 0xFFFF / 10
static float rhOrNan(float v)  { return v >= 327.66f ? NAN : v; }   // 0x7FFF / 100
static float tOrNan(float v)   { return v >= 163.83f ? NAN : v; }   // 0x7FFF / 200
static float idxOrNan(float v) { return v >= 3276.6f ? NAN : v; }   // 0x7FFF / 10

static bool readSen6x(Reading &r) {
  float pm1, pm25, pm4, pm10, rh, t, voc = NAN, nox = NAN;
  uint16_t co2 = 0xFFFF;
  int16_t err;
  switch (pmType) {
    case PmSensor::SEN66:
      err = sen66.readMeasuredValues(pm1, pm25, pm4, pm10, rh, t, voc, nox, co2);
      break;
    case PmSensor::SEN63C: {
      int16_t c = 0x7FFF;
      err = sen63c.readMeasuredValues(pm1, pm25, pm4, pm10, rh, t, c);
      co2 = (c == 0x7FFF || c < 0) ? 0xFFFF : (uint16_t)c;
      break;
    }
    case PmSensor::SEN65:
      err = sen65.readMeasuredValues(pm1, pm25, pm4, pm10, rh, t, voc, nox);
      break;
    case PmSensor::SEN68: {
      float hcho;
      err = sen68.readMeasuredValues(pm1, pm25, pm4, pm10, rh, t, voc, nox, hcho);
      break;
    }
    default:
      return false;
  }
  if (err) return false;
  r.pm1p0 = pmOrNan(pm1); r.pm2p5 = pmOrNan(pm25); r.pm4p0 = pmOrNan(pm4); r.pm10p0 = pmOrNan(pm10);
  r.humidity = rhOrNan(rh); r.temperature = tOrNan(t);
  r.vocIndex = idxOrNan(voc); r.noxIndex = idxOrNan(nox);
  r.co2Ppm = (co2 == 0xFFFF) ? 0 : co2;
  return true;
}

static bool readSen5x(Reading &r) {
  float pm1, pm25, pm4, pm10, rh, t, voc, nox;
  if (sen5x.readMeasuredValues(pm1, pm25, pm4, pm10, rh, t, voc, nox)) return false;
  r.pm1p0 = pm1; r.pm2p5 = pm25; r.pm4p0 = pm4; r.pm10p0 = pm10;
  r.humidity = rh; r.temperature = t; r.vocIndex = voc; r.noxIndex = nox;   // NAN where absent
  return true;
}

// ---- SCD4x (CO2 island, fitted by hand): SCD40, SCD41 or SCD43 ----
// All three share the package, I2C address and periodic-measurement commands used here.

static bool startScd4x() {
  scd4x.begin(*bus, ADDR_SCD4X);
  scd4x.wakeUp();                    // SCD41/43 only; ignored (not even acknowledged) otherwise
  scd4x.stopPeriodicMeasurement();   // in case it kept running across an MCU reset
  delay(500);
  if (scd4x.reinit()) return false;
  delay(30);
  SCD4xSensorVariant variant;        // only readable in idle mode, i.e. before starting
  if (!scd4x.getSensorVariant(variant)) {
    switch (variant & SCD4X_SENSOR_VARIANT_MASK) {
      case SCD4X_SENSOR_VARIANT_SCD40: scdName = "SCD40"; break;
      case SCD4X_SENSOR_VARIANT_SCD41: scdName = "SCD41"; break;
      case SCD4X_SENSOR_VARIANT_SCD42: scdName = "SCD42"; break;
      case SCD4X_SENSOR_VARIANT_SCD43: scdName = "SCD43"; break;
      default: scdName = "SCD4x"; break;
    }
  } else {
    scdName = "SCD4x";
  }
  return scd4x.startPeriodicMeasurement() == 0;
}

static void pollScd4x() {
  bool ready = false;
  if (scd4x.getDataReadyStatus(ready) || !ready) return;
  uint16_t co2;
  float t, rh;
  if (!scd4x.readMeasurement(co2, t, rh) && co2 > 0) scdCo2 = co2;
}

// ---- Public API ----

void sensors_begin(TwoWire &wire) {
  bus = &wire;
  delay(50);   // sensor power-up after the board switch turns on
  if (present(ADDR_SEN5X)) pmType = startSen5x();
  if (pmType == PmSensor::NONE && present(ADDR_SEN6X)) pmType = startSen6x();
  scdFitted = present(ADDR_SCD4X) && startScd4x();
  if (!scdFitted) scdName = "none";
  Serial.printf("[SENS] PM sensor: %s, CO2 sensor: %s\n", sensors_pm_name(), scdName);
}

bool sensors_read(Reading &out) {
  if (scdFitted) pollScd4x();
  Reading r;
  bool ok = false;
  if (pmType == PmSensor::SEN50 || pmType == PmSensor::SEN54 || pmType == PmSensor::SEN55) ok = readSen5x(r);
  else if (pmType != PmSensor::NONE) ok = readSen6x(r);
  if (ok) out = r;
  // The SCD4x on its isolated island is preferred over a SEN6x's built-in CO2.
  if (scdFitted && scdCo2) out.co2Ppm = scdCo2;
  return ok;
}

PmSensor sensors_pm_type() { return pmType; }
bool sensors_has_scd4x() { return scdFitted; }
const char *sensors_scd_name() { return scdName; }

bool sensors_has_environment() {
  return pmType == PmSensor::SEN54 || pmType == PmSensor::SEN55 || pmType == PmSensor::SEN65 ||
         pmType == PmSensor::SEN66 || pmType == PmSensor::SEN68;
}

bool sensors_has_nox() {
  return pmType == PmSensor::SEN55 || pmType == PmSensor::SEN65 || pmType == PmSensor::SEN66 ||
         pmType == PmSensor::SEN68;
}

bool sensors_has_co2() {
  return scdFitted || pmType == PmSensor::SEN63C || pmType == PmSensor::SEN66;
}

const char *sensors_pm_name() {
  switch (pmType) {
    case PmSensor::SEN50: return "SEN50";
    case PmSensor::SEN54: return "SEN54";
    case PmSensor::SEN55: return "SEN55";
    case PmSensor::SEN63C: return "SEN63C";
    case PmSensor::SEN65: return "SEN65";
    case PmSensor::SEN66: return "SEN66";
    case PmSensor::SEN68: return "SEN68";
    default: return "none";
  }
}

uint8_t sensors_pm_code() {
  switch (pmType) {
    case PmSensor::SEN50: return 50;
    case PmSensor::SEN54: return 54;
    case PmSensor::SEN55: return 55;
    case PmSensor::SEN63C: return 63;
    case PmSensor::SEN65: return 65;
    case PmSensor::SEN66: return 66;
    case PmSensor::SEN68: return 68;
    default: return 0;
  }
}
