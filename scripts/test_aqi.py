"""Compile the actual firmware AQI functions and formatting on the host."""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / "src/main.cpp").read_text()
functions = source[source.index("static int calcAQILinear("):source.index("const char *aqiCategory(")]
harness = r'''
#include <cmath>
#include <cassert>
#include <cstring>
#include <limits>
#include "display_format.h"
using std::isfinite;
'''+functions+r'''
int main() {
  const float pm25[] = {0, 9, 9.1f, 35.4f, 35.5f, 55.4f, 55.5f, 125.4f, 125.5f, 225.4f, 225.5f, 325.4f};
  const int expected[] = {0,50,51,100,101,150,151,200,201,300,301,500};
  for (int i=0; i<12; ++i) assert(aqiFromPM25(pm25[i]) == expected[i]);
  assert(aqiFromPM25(9.09f) == 50);
  assert(aqiFromPM25(575.9f) == 999);
  assert(aqiFromPM25(576.0f) == 999);
  assert(aqiFromPM25(1000) == 1844);
  assert(aqiFromPM10(604) == 500);
  assert(aqiFromPM10(604.9f) == 500);
  assert(aqiFromPM10(1000) == 940);
  assert(aqiFromPM25(-1) == -1);
  assert(aqiFromPM25(NAN) == -1);
  assert(aqiFromPM10(INFINITY) == -1);
  assert(aqiFromPM25(1e9f) == 65535);
  int previous = 0;
  for (int i=0; i<=10000; ++i) {
    int current = aqiFromPM25(i/10.0f);
    assert(current >= previous);
    previous = current;
  }
  const int values[] = {999,1000,1100,1500,1844,9999,65535,-12};
  const char *labels[] = {"999","1.0K","1.1K","1.5K","1.8K","10.0K","65.5K","-12"};
  for (int i=0; i<8; ++i) {
    char label[8];
    formatCompactValue(label, sizeof(label), values[i]);
    assert(strcmp(label, labels[i]) == 0);
  }
}
'''
with tempfile.TemporaryDirectory(prefix="aqi-test-") as temp:
    cpp = Path(temp) / "test.cpp"
    binary = Path(temp) / "test"
    cpp.write_text(harness)
    subprocess.run(["c++", "-std=c++11", "-Wall", "-Wextra", "-I", str(root / "src"), str(cpp), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print("AQI breakpoints, extrapolation, monotonicity, invalid inputs and compact formatting passed.")
