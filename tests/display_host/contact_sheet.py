"""Compose host-rendered framebuffer previews; run after render.cpp."""
from pathlib import Path
from PIL import Image, ImageDraw
import sys
folder = Path(sys.argv[1])
for group in ("aqi", "pm"):
    files = sorted(folder.glob(f"{group}-*.ppm"), key=lambda p: int(p.stem.split("-")[1]))
    if group == "aqi":
        files = [p for p in files if int(p.stem.split("-")[1]) <= 1844]
    sheet = Image.new("RGB", (260 * 5, 350 * ((len(files) + 4) // 5)), "#dddddd")
    draw = ImageDraw.Draw(sheet)
    for i, file in enumerate(files):
        x, y = (i % 5) * 260, (i // 5) * 350
        sheet.paste(Image.open(file), (x + 10, y + 24))
        draw.text((x + 10, y + 6), file.stem, fill="black")
    sheet.save(folder / f"{group}-contact.png")
