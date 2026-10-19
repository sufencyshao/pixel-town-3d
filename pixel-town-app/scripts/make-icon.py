"""Draw the app's code-native 町 brand, without modifying any character art."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess
root = Path(__file__).resolve().parents[1]
build = root / 'build'
icons = build / 'town.iconset'
icons.mkdir(parents=True, exist_ok=True)
im = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.rounded_rectangle((36, 36, 988, 988), radius=180, fill='#eef3df')
d.rectangle((180, 170, 850, 870), fill='#49694b')
d.rectangle((210, 200, 820, 840), fill='#fcfcef')
d.rectangle((244, 234, 786, 806), outline='#a7ba86', width=12)
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Songti.ttc', 440)
box = d.textbbox((0, 0), '町', font=font)
d.text(((1024-(box[2]-box[0]))/2-box[0], (1024-(box[3]-box[1]))/2-box[1]+20), '町', font=font, fill='#49694b')
d.rectangle((730, 120, 850, 200), fill='#d5a34f')
im.save(build / 'town-1024.png')
for size in [16, 32, 128, 256, 512]:
    for scale in [1, 2]:
        file = icons / f'icon_{size}x{size}{"@2x" if scale==2 else ""}.png'
        im.resize((size*scale, size*scale), Image.Resampling.LANCZOS).save(file)
subprocess.run(['iconutil', '-c', 'icns', str(icons), '-o', str(build / 'town.icns')], check=True)
print(build / 'town.icns')
