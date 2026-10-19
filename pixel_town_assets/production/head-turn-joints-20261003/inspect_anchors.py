import sys,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from build_daily_actions import residents
records=json.loads((ROOT/'validation/head-turn-joints/registration.json').read_text())
for n in (5,9,12,16,23,26,28,32,33,36,37,40):
 p=residents('characters')[n-1];raw=Image.open(p/'source/shake-head-solid-poses.png').convert('RGBA');b=Image.new('RGB',raw.size,'#b1bdb0');b.paste(raw,(0,0),raw);dr=ImageDraw.Draw(b)
 for i,(x,y) in enumerate(records[n-1]['anchors']):
  row,col=divmod(i,4);x+=round(col*raw.width/4);y+=round(row*raw.height/2)
  dr.line((x-12,y,x+12,y),fill='cyan',width=3);dr.line((x,y-12,x,y+12),fill='cyan',width=3)
 b.resize((1332,666)).save(ROOT/f'validation/head-turn-joints/anchors-{n}.png')
