"""Compose source/3D review pages from already rendered PNGs only."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, sys
R=Path(__file__).resolve().parent.parent
Q=R/'qa-identity'
identities=json.loads((R/'identity/identities.json').read_text())['characters']
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',24)
small=ImageFont.truetype('/System/Library/Fonts/STHeiti Light.ttc',16)
for c in identities:
 out=Q/c['id']
 if not (out/'Idle-00-front.png').exists():continue
 images=[(Path(c['referencePath']),'原2D / '+c['name'])]
 for fn,title in [('Idle-00-front.png','3D 正面'),('Idle-00-quarter.png','3D 前侧'),('Idle-00-side.png','3D 侧面'),('Idle-00-face.png','脸部近看'),('Walk-28-side.png','行走侧面'),('Sit-50-front.png','坐姿正面'),('Sit-50-side.png','坐姿侧面'),('Wave-57-quarter.png','挥手前侧'),('Wave-57-side.png','挥手侧面')]:
  if (out/fn).exists():images.append((out/fn,title))
 page=Image.new('RGB',(2000,1120),'#ebece4');d=ImageDraw.Draw(page)
 for n,(p,title) in enumerate(images):
  x=n%5*400;y=n//5*560
  d.rectangle((x+4,y+4,x+396,y+552),fill='#f6f5ef',outline='#c9cbbf')
  im=Image.open(p).convert('RGBA')
  if n==0:im=im.crop(im.getbbox())
  scale=min(386/im.width,500/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if n==0 else Image.Resampling.LANCZOS)
  page.paste(im,(x+(400-im.width)//2,y+7),im)
  d.text((x+12,y+516),title,font=font,fill='#243327')
 page.save(out/'原图与3D动作对照.png')

# Fifteen residents per comparison page, original and 3D share each tile.
available=[c for c in identities if (Q/c['id']/'Idle-00-front.png').exists()]
for start in range(0,len(available),15):
 page=Image.new('RGB',(1800,1230),'#ebece4');d=ImageDraw.Draw(page)
 for i,c in enumerate(available[start:start+15]):
  x=i%5*360;y=i//5*410
  for off,path,mode in [(0,Path(c['referencePath']),Image.Resampling.NEAREST),(170,Q/c['id']/'Idle-00-front.png',Image.Resampling.LANCZOS)]:
   im=Image.open(path).convert('RGBA')
   if off==0:im=im.crop(im.getbbox())
   scale=min(175/im.width,340/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),mode);page.paste(im,(x+off+(175-im.width)//2,y+8),im)
  d.text((x+12,y+354),f'{identities.index(c)+1:02d} {c["name"]}  原2D / 3D',font=small,fill='#243327')
  d.text((x+12,y+380),c['id'],font=small,fill='#435142')
 page.save(Q/f'全员原图对照-{start+1:02d}-{min(start+15,len(available)):02d}.png')
print('Composed',len(available),'resident review pages')
