#include "../../src/display.cpp"
#include <cassert>
#include <string>
int main(int argc,char **argv){
  assert(argc==2);
  display_begin();
  SensorSample s{};s.temperature=2450;s.humidity=5200;s.vocIndex=110;s.noxIndex=80;
  for (int value : {0,9,99,100,500}) {
    s.vocIndex=value;s.temperature=value==500?-1000:value*100;s.humidity=10000;
    tft.fillScreen(0x1234);
    drawSmallMetricCard(122,152,114,52,DataField::VOC_INDEX,s,DataField::AQI,true);
    for(int x=128;x<230;++x) assert(tft.pixels[203*240+x]==C_BORDER);
    for(int y=206;y<208;++y) for(int x=128;x<230;++x) assert(tft.pixels[y*240+x]==0x1234);
    drawBottomMetricCard(4,264,89,52,DataField::TEMPERATURE,s,DataField::AQI,true);
    drawBottomMetricCard(97,264,90,52,DataField::HUMIDITY,s,DataField::AQI,true);
    for(int x=8;x<89;++x) assert(tft.pixels[315*240+x]==C_BORDER);
    for(int x=101;x<183;++x) assert(tft.pixels[315*240+x]==C_BORDER);
    for(int y=318;y<320;++y) for(int x=12;x<175;++x) assert(tft.pixels[y*240+x]==0x1234);
  }
  int values[]={0,9,50,99,100,188,300,888,999,1000,1100,1500,1844};
  s.temperature=3000;s.humidity=6000;s.vocIndex=100;s.noxIndex=100;
  for(int v:values){s.aqi=v;s.pm1p0=80;s.pm2p5=125;s.pm4p0=150;s.pm10p0=190;++s.timestamp;
    char number[8];formatCompactValue(number,sizeof(number),v);
    const uint8_t sizes[]={62,42,32};
    drawFittedValue(number,56,12,128,54,0,65535,v>999?sizes+1:sizes,v>999?2:3);
    assert(tft.font==rubikBySize(v>999?42:62));
    assert(tft.textWidth(number)<=128);
    display_home(s,DataField::AQI,false,true,false,true,true);
    std::string path=std::string(argv[1])+"/aqi-"+std::to_string(v)+".ppm";tft.save(path.c_str());
  }
  s.aqi=100;++s.timestamp;
  display_home(s,DataField::AQI,false,true,false,true,true);
  auto writes=tft.writes;
  display_home(s,DataField::AQI,false,true,false,true,true);assert(tft.writes==writes);
  display_home(s,DataField::PM2_5,false,true,false,true,true);
  assert(tft.writes-writes<65000); // Two selected panels, not the whole screen.
  for (int pm : {9990,10000}) {
    s.pm1p0=s.pm2p5=s.pm4p0=s.pm10p0=pm;s.aqi=1844;
    s.temperature=-1000;s.humidity=10000;s.vocIndex=500;s.noxIndex=500;++s.timestamp;
    display_home(s,DataField::PM2_5,false,true,false,true,true);
    tft.save((std::string(argv[1])+"/limits-"+std::to_string(pm)+".ppm").c_str());
  }
  DataBuffer history;assert(history.begin(200));
  for(int i=0;i<200;++i){s.timestamp=i*1000;s.pm2p5=100+i*2;s.pm1p0=s.pm2p5*0.9;s.pm4p0=s.pm2p5+20;s.pm10p0=s.pm2p5+40;history.addSample(s);}
  const int concentrations[]={0,90,354,554,1254,2254,3254,9999,10000};
  for(int v:concentrations){s.pm2p5=v;++s.timestamp;display_chart(history,DataField::PM2_5,s);std::string path=std::string(argv[1])+"/pm-"+std::to_string(v)+".ppm";tft.save(path.c_str());}
  auto pushes=tft.pushes;display_chart(history,DataField::PM2_5,s);assert(pushes==tft.pushes);
  ++s.timestamp;display_chart(history,DataField::PM2_5,s);assert(pushes==tft.pushes);
  ++s.pm2p5;display_chart(history,DataField::PM2_5,s);assert(tft.pushes==pushes+1);
  ++s.timestamp;history.addSample(s);pushes=tft.pushes;display_chart(history,DataField::PM2_5,s);assert(tft.pushes==pushes+2);
  history.clear();display_chart(history,DataField::PM2_5,s);tft.save((std::string(argv[1])+"/empty.ppm").c_str());
  puts("Rendered 13 AQI, 9 PM and 2 metric-limit cases; redraw checks passed.");
}
