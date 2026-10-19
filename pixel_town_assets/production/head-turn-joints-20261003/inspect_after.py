import sys,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from build_daily_actions import residents,prepare_human
from head_turn import frames,joint_masks
records=[]
for page in range(8):
    board=Image.new('RGB',(1280,1200),'#d6ddd5');d=ImageDraw.Draw(board)
    for r,p in enumerate(residents('characters')[page*5:page*5+5]):
        front,box=prepare_human(p);out,meta=frames(p,front,box);records.append({'role':p.name,**meta})
        for c,i in enumerate((0,1,3,9)):
            tile=out[i].crop((38,50,218,170)).resize((360,240),Image.Resampling.NEAREST).crop((20,0,340,240))
            board.paste(tile,(c*320,r*240),tile);d.text((c*320+4,r*240),p.name[:2]+f' phase{i}',fill='yellow')
    board.save(ROOT/f'validation/head-turn-joints/draft-{page+1}.png')
(ROOT/'validation/head-turn-joints/registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
