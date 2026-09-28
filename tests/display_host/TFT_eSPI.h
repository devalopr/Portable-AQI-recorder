#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <vector>
#define PROGMEM
enum {TL_DATUM,TC_DATUM,TR_DATUM,ML_DATUM,MC_DATUM,MR_DATUM,BL_DATUM,BC_DATUM,BR_DATUM,L_BASELINE,C_BASELINE,R_BASELINE};
struct GFXglyph { uint16_t bitmapOffset; uint8_t width,height,xAdvance; int8_t xOffset,yOffset; };
struct GFXfont { uint8_t *bitmap; GFXglyph *glyph; uint16_t first,last; uint8_t yAdvance; };
extern const GFXfont RubikBold8, RubikBold15;
struct SerialStub { void println(const char*) {} };
static SerialStub Serial;
// Raster backend for the actual firmware display.cpp, using its GFX bitmaps.
// Built-in chart fonts are approximated with Rubik 8/15; free fonts are exact.
class TFT_eSPI {
public:
  int w=240,h=320,dx=0,dy=0,datum=0;
  const GFXfont *font=nullptr;
  uint16_t fg=0,bg=65535;
  std::vector<uint16_t> pixels=std::vector<uint16_t>(240*320,65535);
  unsigned long writes=0,pushes=0;
  void begin() {} void invertDisplay(bool) {} void setRotation(int) {}
  void resetViewport(){dx=dy=0;}
  void setViewport(int x,int y,int,int,bool){dx=x;dy=y;}
  void setFreeFont(const GFXfont *f){font=f;}
  void setTextFont(int n){font=n==1?&RubikBold8:&RubikBold15;}
  void setTextDatum(int d){datum=d;}
  void setTextColor(uint16_t f,uint16_t b){fg=f;bg=b;}
  int fontHeight(){return font?font->yAdvance:0;}
  int textWidth(const char *s){int n=0;for(size_t i=0;s[i];++i){auto g=font->glyph[(unsigned char)s[i]-32];n+=s[i+1]?g.xAdvance:g.xOffset+g.width;}return n;}
  void raw(int x,int y,uint16_t c){if(x>=0&&x<w&&y>=0&&y<h){pixels[y*w+x]=c;++writes;}}
  void drawPixel(int x,int y,uint16_t c){raw(x+dx,y+dy,c);}
  void fillScreen(uint16_t c){std::fill(pixels.begin(),pixels.end(),c);writes+=pixels.size();}
  void fillRect(int x,int y,int a,int b,uint16_t c){for(int j=std::max(0,y+dy);j<std::min(h,y+dy+b);++j)for(int i=std::max(0,x+dx);i<std::min(w,x+dx+a);++i)raw(i,j,c);}
  void drawLine(int x,int y,int xx,int yy,uint16_t c){int a=abs(xx-x),b=-abs(yy-y),sx=x<xx?1:-1,sy=y<yy?1:-1,e=a+b;for(;;){drawPixel(x,y,c);if(x==xx&&y==yy)break;int z=2*e;if(z>=b){e+=b;x+=sx;}if(z<=a){e+=a;y+=sy;}}}
  void fillCircle(int x,int y,int r,uint16_t c){for(int j=-r;j<=r;++j)for(int i=-r;i<=r;++i)if(i*i+j*j<=r*r)drawPixel(x+i,y+j,c);}
  void fillRoundRect(int x,int y,int a,int b,int r,uint16_t c){for(int j=0;j<b;++j)for(int i=0;i<a;++i){int px=std::max(r-i,std::max(0,i-(a-r-1)));int py=std::max(r-j,std::max(0,j-(b-r-1)));if(px*px+py*py<=r*r)drawPixel(x+i,y+j,c);}}
  void drawRoundRect(int x,int y,int a,int b,int r,uint16_t c){for(int j=0;j<b;++j)for(int i=0;i<a;++i){int px=std::max(r-i,std::max(0,i-(a-r-1)));int py=std::max(r-j,std::max(0,j-(b-r-1)));if(px*px+py*py<=r*r&&(i==0||j==0||i==a-1||j==b-1||px*px+py*py>(r-1)*(r-1)))drawPixel(x+i,y+j,c);}}
  void fillTriangle(int x1,int y1,int x2,int y2,int x3,int y3,uint16_t c){for(int y=std::min({y1,y2,y3});y<=std::max({y1,y2,y3});++y)for(int x=std::min({x1,x2,x3});x<=std::max({x1,x2,x3});++x){int a=(x-x1)*(y2-y1)-(y-y1)*(x2-x1),b=(x-x2)*(y3-y2)-(y-y2)*(x3-x2),d=(x-x3)*(y1-y3)-(y-y3)*(x1-x3);if((a>=0&&b>=0&&d>=0)||(a<=0&&b<=0&&d<=0))drawPixel(x,y,c);}}
  void drawString(const char *s,int x,int y){
    int ab=0,bb=0;
    for(int i=0;i<font->last-font->first;++i){auto g=font->glyph[i];ab=std::max(ab,-(int)g.yOffset);bb=std::max(bb,(int)g.height+g.yOffset);}
    int width=textWidth(s),ch=ab;
    if(datum>=BL_DATUM&&datum<=BR_DATUM)ch+=bb;
    y+=ab;
    if(datum==TC_DATUM||datum==MC_DATUM||datum==BC_DATUM||datum==C_BASELINE)x-=width/2;
    if(datum==TR_DATUM||datum==MR_DATUM||datum==BR_DATUM||datum==R_BASELINE)x-=width;
    if(datum>=ML_DATUM&&datum<=MR_DATUM)y-=ch/2;
    if(datum>=BL_DATUM&&datum<=BR_DATUM)y-=ch;
    if(datum>=L_BASELINE)y-=ab;
    // TFT_eSPI paints the entire font ascent/descent rectangle when opaque,
    // even if the visible number uses only a small part of that height.
    if(fg!=bg) fillRect(x,y-ab,width,ab+bb,bg);
    for(;*s;++s){auto g=font->glyph[(unsigned char)*s-font->first];for(int yy=0;yy<g.height;++yy)for(int xx=0;xx<g.width;++xx){int bit=yy*g.width+xx;if(font->bitmap[g.bitmapOffset+bit/8]&(128>>(bit%8)))drawPixel(x+g.xOffset+xx,y+g.yOffset+yy,fg);}x+=g.xAdvance;}
  }
  void save(const char *path){std::ofstream f(path,std::ios::binary);f<<"P6\n"<<w<<" "<<h<<"\n255\n";for(auto c:pixels){unsigned char rgb[]={static_cast<unsigned char>(((c>>11)&31)*255/31),static_cast<unsigned char>(((c>>5)&63)*255/63),static_cast<unsigned char>((c&31)*255/31)};f.write((char*)rgb,3);}}
};
class TFT_eSprite:public TFT_eSPI {
  TFT_eSPI *screen;
public:
  TFT_eSprite(TFT_eSPI *t):screen(t){}
  void setColorDepth(int){}
  void* createSprite(int a,int b){w=a;h=b;pixels.resize(a*b);return pixels.data();}
  void fillSprite(uint16_t c){fillScreen(c);}
  void pushSprite(int x,int y){++screen->pushes;for(int j=0;j<h;++j)for(int i=0;i<w;++i)screen->raw(x+i,y+j,pixels[j*w+i]);}
};
