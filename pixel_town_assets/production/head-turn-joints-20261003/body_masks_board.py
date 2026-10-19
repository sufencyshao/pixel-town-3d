import sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from build_daily_actions import residents,prepare_human
for page in range(4):
 b=Image.new('RGB',(1280,1000),'#d6ddd5');dr=ImageDraw.Draw(b)
 for i,p in enumerate(residents('characters')[page*10:page*10+10]):
  row,col=divmod(i,2);x=col*640;y=row*200
  front,_=prepare_human(p)
  for n,im in enumerate((Image.fromarray(front),Image.open(p/'source/shake-head-joint-body.png'))):
   crop=im.crop((48,90,208,190)).resize((320,200),Image.Resampling.NEAREST);b.paste(crop,(x+n*320,y),crop)
   dr.text((x+n*320+4,y),p.name[:2]+(' original' if n==0 else ' fixed body'),fill='yellow')
 b.save(ROOT/f'validation/head-turn-joints/body-masks-{page+1}.png')
