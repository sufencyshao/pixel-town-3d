import sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from build_daily_actions import residents,prepare_human
from head_turn import frames,CALIBRATION
for page in range(8):
 b=Image.new('RGB',(1680,1150),'#d6ddd5');d=ImageDraw.Draw(b)
 for row,p in enumerate(residents('characters')[page*5:page*5+5]):
  front,box=prepare_human(p);out,meta=frames(p,front,box);join=min(meta['jointCalibration']['neckRoot'][2],meta['cutY']-3)
  for col,index in enumerate((0,1,2,3,7,8,9)):
   crop=out[index].crop((78,join-34,174,join+58)).resize((240,230),Image.Resampling.NEAREST);b.paste(crop,(col*240,row*230),crop)
   d.text((col*240+2,row*230),p.name[:2]+f' phase {index}',fill='yellow')
 b.save(ROOT/f'validation/head-turn-joints/seams-{page+1}.png')
