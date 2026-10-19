import sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from build_daily_actions import residents,prepare_human
from head_turn import CUT_Y
for page in range(8):
    board=Image.new('RGB',(1280,1200),'#d6ddd5');d=ImageDraw.Draw(board)
    for r,p in enumerate(residents('characters')[page*5:page*5+5]):
        front,_=prepare_human(p);atlas=Image.open(p/'animations/daily/shake_head.png')
        for c,i in enumerate((0,1,3,9)):
            tile=atlas.crop((i*256,50,(i+1)*256,170)).resize((512,240),Image.Resampling.NEAREST).crop((96,0,416,240))
            board.paste(tile,(c*320,r*240),tile)
            d.text((c*320+4,r*240+2),p.name[:2]+f' phase{i} cut{CUT_Y[int(p.name[:2])-1]}',fill='#ffff00')
    board.save(ROOT/f'validation/head-turn-joints/before-{page+1}.png')
