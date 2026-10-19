from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parent.parent
meta=json.loads((R/'assets/manifest.json').read_text())['characters'];font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',20)
meta=[c for c in meta if (R/'qa/people'/(c['id']+'-lie.png')).exists()]
views=[('front','正面'),('back','背面'),('side','侧面'),('wave','挥手'),('sit','坐姿'),('lie','侧躺')]
for offset in range(0,len(meta),5):
 chars=meta[offset:offset+5];sheet=Image.new('RGB',(1920,len(chars)*380+44),'#f4f2e9');d=ImageDraw.Draw(sheet)
 for x,(_,label) in enumerate(views):d.text((x*320+130,9),label,font=font,fill='#344c40')
 for y,c in enumerate(chars):
  for x,(view,label) in enumerate(views):
   p=R/'qa/people'/(c['id']+'-'+view+'.png');im=Image.open(p).convert('RGB');im.thumbnail((320,345));left=x*320+(320-im.width)//2;top=44+y*380;sheet.paste(im,(left,top));d.text((x*320+10,top+346),c['name']+' '+str(round(c['design']['height']*100))+'cm',font=font,fill='#344c40')
 sheet.save(R/'qa'/f'人物六视图-{offset+1:02d}-{offset+len(chars):02d}.jpg',quality=88)
print('Contact sheets complete')
