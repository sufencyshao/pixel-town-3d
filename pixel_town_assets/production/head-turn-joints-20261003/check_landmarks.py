import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from build_daily_actions import residents,prepare_human
from head_turn import frames
points=[[(106,110),(151,110)],[(105,116),(150,116)],[(108,117),(145,117)],[(110,139),(145,139)],[(104,105),(149,105)],[(108,122),(147,122)],[(102,116),(152,116)],[(108,123),(146,123)],[(108,120),(145,120)],[(109,121),(148,121)],[(108,140),(144,140)],[(116,107),(146,109)],[(110,142),(143,142)],[(114,120),(145,120)],[(109,139),(146,139)],[(114,106),(142,106)],[(114,108),(147,107)],[(114,120),(146,120)],[(111,125),(144,125)],[(115,108),(146,108)],[(110,117),(148,117)],[(114,122),(146,122)],[(100,120),(150,120)],[(109,125),(148,125)],[(111,122),(146,127)],[(105,117),(149,117)],[(112,121),(145,121)],[(106,121),(147,121)],[(96,124),(159,121)],[(112,122),(147,122)],[(110,117),(148,117)],[(112,123),(143,123)],[(121,128),(135,128)],[(112,126),(146,126)],[(110,128),(146,128)],[(111,127),(148,127)],[(112,122),(144,123)],[(113,122),(144,122)],[(117,126),(148,123)],[(114,131),(147,131)]]
records={};errors=[]
for p,xy in zip(residents('characters'),points):
 front,box=prepare_human(p);out,meta=frames(p,front,box);rects=[]
 for x,y in xy:
  original=front[y-1:y+2,x-1:x+2]
  bad=[i for i,im in enumerate(out) if not np.array_equal(np.asarray(im)[y-1:y+2,x-1:x+2],original)]
  if bad:errors.append({'role':p.name,'point':[x,y],'rgba':front[y,x].tolist(),'badPhases':bad})
  rects.append([x-1,y-1,x+2,y+2])
 records[p.name]={'fixedGarmentRects':rects}
(ROOT/'validation/head-turn-joints/garment-check-regions.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(errors,ensure_ascii=False,indent=2))
