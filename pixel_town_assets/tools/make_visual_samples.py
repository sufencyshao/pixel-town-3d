#!/usr/bin/env python3
"""Four-phase inspection boards for every entity with an animation manifest."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];DEST=ROOT/'validation';DEST.mkdir(exist_ok=True)
for group,label in [('characters','humans'),('pets','pets'),('codexmini','codexmini')]:
 folders=sorted(p for p in (ROOT/group).iterdir() if p.is_dir() and (p/'animation.json').exists())
 if group=='characters':
  groups=[('original-humans',[p for p in folders if int(p.name[:2])<=20]),('new-humans',[p for p in folders if int(p.name[:2])>20])]
 else:groups=[(label,folders)]
 for prefix,selected in groups:
  for page in range((len(selected)+4)//5):
   out=Image.new('RGB',(4*160,5*2*180),(217,228,223));d=ImageDraw.Draw(out)
   for row,p in enumerate(selected[page*5:page*5+5]):
    mf=json.loads((p/'animation.json').read_text());actions=mf['animations']
    if group=='characters':acts=['walk_down','wave']
    elif group=='pets':acts=['walk','fly' if 'fly' in actions else 'groom' if 'groom' in actions else 'eat']
    else:acts=['walk_right','work']
    for a,action in enumerate(acts):
     if action not in actions:continue
     spec=actions[action];atlas=Image.open(p/spec['atlas']).convert('RGBA');fw=mf['frameWidth'];fh=mf['frameHeight'];count=spec['frames']
     for col,f in enumerate([0,count//4,count//2,count*3//4]):
      im=atlas.crop((f*fw,0,(f+1)*fw,fh)).resize((160,160),Image.Resampling.NEAREST);x=col*160;y=(row*2+a)*180;out.paste(im,(x,y),im);d.text((x+2,y+162),p.name[:18]+' '+action+' '+str(f),fill='#22392d')
   out.save(DEST/f'{prefix}-visual-page-{page+1}.png');print(prefix,page+1)
