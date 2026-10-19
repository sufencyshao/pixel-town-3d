"""Stage generated sources and make review boards without replacing animations."""
import sys,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from build_daily_actions import residents,prepare_human
from head_turn import frames

roles=residents('characters');data=[]
for page in range(8):
    board=Image.new('RGB',(1536,1280),'#e1e6de');draw=ImageDraw.Draw(board)
    for row,folder in enumerate(roles[page*5:page*5+5]):
        source=Path(__file__).parent/folder.name/'generated-head-poses.png'
        if not source.exists():continue
        dest=folder/'source/shake-head-solid-poses.png';dest.parent.mkdir(exist_ok=True);shutil.copy2(source,dest)
        front,box=prepare_human(folder);out,meta=frames(folder,front,box)
        data.append({'role':folder.name,**meta})
        for col,index in enumerate((0,1,3,7,9,24)):
            tile=out[index];board.paste(tile,(col*256,row*256),tile)
            draw.text((col*256+4,row*256+240),folder.name[:2]+f' phase {index}',fill='#223c2c')
    board.save(ROOT/f'validation/head-turn-solid/draft-keyposes-{page+1}.png')
(ROOT/'validation/head-turn-solid/draft-registration.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print('Prepared whole-head review boards for',len(data),'characters.')
