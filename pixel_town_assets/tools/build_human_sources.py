"""Package new, individual-faced people with genuine side/back and pose sources.

Generated originals are kept in production/. This stage only slices, aligns,
and prepares neutral/step key images for deterministic game rig animation.
"""
import argparse,sys
from PIL import Image,ImageOps
from expansion_data import ROOT,HUMANS
from atlas_tiles import tiles

def normalize(tile,height=210):
 box=tile.getbbox();tile=tile.crop(box)
 scale=min(height/tile.height,198/tile.width)
 tile=tile.resize((round(tile.width*scale),round(tile.height*scale)),Image.Resampling.NEAREST)
 out=Image.new('RGBA',(256,256));out.alpha_composite(tile,((256-tile.width)//2,230-tile.height))
 return out

def step(im,phase,direction):
 import numpy as np
 src=np.array(im);Y,X=np.mgrid[:256,:256].astype(float);xx=X.copy();yy=Y.copy()
 legweight=np.clip((yy-180)/40,0,1)
 for side in (-1,1):
  weight=legweight*np.clip((side*(xx-128)+2)/7,0,1)
  xx+=side*phase*3*weight;yy+=max(0,side*phase)*4*weight
 xi=np.rint(xx).astype(int);yi=np.rint(yy).astype(int);ok=(xi>=0)&(xi<256)&(yi>=0)&(yi<256)
 arr=np.zeros_like(src);arr[ok]=src[yi[ok],xi[ok]]
 return Image.fromarray(arr)

def build(pose_atlas=None):
 front=tiles(ROOT/'production/humans-front-source.png',filter_size=1)
 directions=tiles(ROOT/'production/humans-direction-source.png',count=40,columns=10)
 poses=tiles(pose_atlas,count=60,columns=15,filter_size=1) if pose_atlas else None
 for i,spec in enumerate(HUMANS):
  folder=ROOT/'characters'/spec[0];folder.mkdir(exist_ok=True)
  neutral=normalize(front[i]);left=normalize(directions[i*2]);right=ImageOps.mirror(left);back=normalize(directions[i*2+1])
  for n,im in ((1,neutral),(4,left),(7,right),(10,back)):im.save(folder/f'frame_{n:02d}.png')
  for start,im,direction in ((2,neutral,'down'),(5,left,'left'),(8,right,'right')):
   for j,phase in enumerate((-1,1)):step(im,phase,direction).save(folder/f'frame_{start+j:02d}.png')
  neutral.save(folder/'frame_13.png')
  if poses:
   for n,j,height in ((14,0,210),(16,1,168),(11,2,210)):
    im=normalize(poses[i*3+j],height);im.save(folder/f'frame_{n:02d}.png')
   Image.open(folder/'frame_11.png').save(folder/'frame_12.png')
   # Surprise uses the person's own neutral morphology; minor facial cue,
   # not replacement with a generic template face.
   from PIL import ImageDraw
   surprise=neutral.copy();d=ImageDraw.Draw(surprise)
   box=neutral.getbbox();face_y=box[1]+int((box[3]-box[1])*.43)
   d.ellipse((125,face_y-2,131,face_y+4),fill=(61,39,38,255))
   surprise.save(folder/'frame_15.png')
  print(spec[0], 'pose sources ready' if poses else 'directions ready, waiting pose atlas')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--poses');build(p.parse_args().poses)
