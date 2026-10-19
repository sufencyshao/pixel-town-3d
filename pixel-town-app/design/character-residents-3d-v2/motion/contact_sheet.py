from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import json
O=Path(__file__).resolve().parent/'qa';shots=json.loads((O/'render-shots.json').read_text());font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',19)
for group,actions in [('daily',['Eat','Drink','Read','Phone','Stretch']),('lying-wave',['Wave','LieDown','LieRest','GetUp'])]:
 selected=[s for s in shots if s['action'] in actions];w,h=288,278;sheet=Image.new('RGB',(w*8,h*len(actions)),(241,240,233));d=ImageDraw.Draw(sheet)
 for i,a in enumerate(actions):
  cells=[s for s in selected if s['action']==a]
  for j,s in enumerate(cells):
   img=Image.open(O/s['file']).convert('RGB');img.thumbnail((w,245));x=j*w+(w-img.width)//2;y=i*h+30;sheet.paste(img,(x,y));d.text((j*w+8,i*h+6),f'{a} {s["phase"]:.2f} {s["view"]}',font=font,fill=(25,31,33))
 sheet.save(O/(group+'-contact.png'))
print('contact sheets ready')
