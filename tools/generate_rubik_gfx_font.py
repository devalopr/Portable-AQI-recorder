#!/usr/bin/env python3
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = ROOT / "tools" / "Rubik-Bold.ttf"
OUT_PATH = ROOT / "src" / "rubik_bold_fonts.h"
FIRST = 32
LAST = 126
SIZES = [8, 10, 12, 15, 18, 20, 24, 32, 42, 62]


def glyph_bytes(font, char):
    scratch = Image.new("L", (160, 160), 0)
    draw = ImageDraw.Draw(scratch)
    bbox = draw.textbbox((0, 0), char, font=font, anchor="ls")
    left, top, right, bottom = bbox
    width = max(0, right - left)
    height = max(0, bottom - top)
    advance = max(1, round(draw.textlength(char, font=font)))

    if width == 0 or height == 0:
        return [], 0, 0, advance, 0, 0

    image = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(image)
    draw.text((-left, -top), char, fill=255, font=font, anchor="ls")

    packed = []
    byte = 0
    bit = 0
    for y in range(height):
        for x in range(width):
            if image.getpixel((x, y)) >= 96:
                byte |= 0x80 >> bit
            bit += 1
            if bit == 8:
                packed.append(byte)
                byte = 0
                bit = 0
    if bit:
        packed.append(byte)

    return packed, width, height, advance, left, top


def emit_array(name, values, columns=12):
    lines = [f"const uint8_t {name}[] PROGMEM = {{"]
    for i in range(0, len(values), columns):
        chunk = values[i:i + columns]
        lines.append("  " + ", ".join(f"0x{value:02X}" for value in chunk) + ",")
    lines.append("};")
    return "\n".join(lines)


def build_font(size):
    font = ImageFont.truetype(str(FONT_PATH), size)
    ascent, descent = font.getmetrics()
    bitmap = []
    glyphs = []

    for code in range(FIRST, LAST + 1):
        data, width, height, advance, x_offset, y_offset = glyph_bytes(font, chr(code))
        glyphs.append((len(bitmap), width, height, advance, x_offset, y_offset))
        bitmap.extend(data)

    stem = f"RubikBold{size}"
    out = [emit_array(f"{stem}Bitmaps", bitmap), ""]
    out.append(f"const GFXglyph {stem}Glyphs[] PROGMEM = {{")
    for offset, width, height, advance, x_offset, y_offset in glyphs:
        out.append(
            f"  {{ {offset:5d}, {width:3d}, {height:3d}, {advance:3d}, {x_offset:4d}, {y_offset:4d} }},"
        )
    out.append("};")
    out.append("")
    out.append(f"const GFXfont {stem} PROGMEM = {{")
    out.append(f"  (uint8_t *){stem}Bitmaps,")
    out.append(f"  (GFXglyph *){stem}Glyphs,")
    out.append(f"  {FIRST}, {LAST}, {ascent + descent}")
    out.append("};")
    return "\n".join(out)


def main():
    sections = [
        "#pragma once",
        "#include <TFT_eSPI.h>",
        "",
        "// Generated from Rubik Bold by tools/generate_rubik_gfx_font.py.",
        "// Glyph range: ASCII 32-126.",
        "",
    ]
    for size in SIZES:
        sections.append(build_font(size))
        sections.append("")
    OUT_PATH.write_text("\n".join(sections), encoding="utf-8")


if __name__ == "__main__":
    main()
