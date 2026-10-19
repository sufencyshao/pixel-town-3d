"""Deterministic animal pixel rigs. No morphing, cross-fading or human gestures.

Uses a generated side-view atlas, partitions natural anatomical regions and
animates feet, head, tail and wings in discrete pixel space. Raw atlas is kept.
"""
import argparse, json, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from expansion_data import ROOT, PETS
from atlas_tiles import tiles

N=16
def transparent(): return Image.new('RGBA',(256,256))

def gif_save(frames, path, ms=80):
 sample=Image.new('RGB',(256*len(frames),256),(18,20,24))
 for i,f in enumerate(frames): sample.paste(f,(256*i,0),f)
 palette=sample.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
 result=[]
 for f in frames:
  rgb=Image.new('RGB',f.size,(18,20,24));rgb.paste(f,mask=f.getchannel('A'))
  p=rgb.quantize(palette=palette,dither=Image.Dither.NONE)
  p.paste(255,mask=f.getchannel('A').point(lambda x:255 if x<128 else 0))
  p.info['transparency']=255;result.append(p)
 result[0].save(path,save_all=True,append_images=result[1:],duration=ms,loop=0,transparency=255,disposal=2,optimize=False)

def normalize(tile):
 tile=tile.convert('RGBA')
 tile.putalpha(tile.getchannel('A').point(lambda x:255 if x>=128 else 0))
 box=tile.getbbox()
 if not box: raise ValueError('Empty sprite cell')
 crop=tile.crop(box)
 # A deliberate 64px logical grid enforces hard edges; fixed bottom alignment.
 factor=min(52/crop.width,45/crop.height)
 crop=crop.resize((max(1,round(crop.width*factor)),max(1,round(crop.height*factor))),Image.Resampling.NEAREST)
 out=Image.new('RGBA',(64,64));out.alpha_composite(crop,((64-crop.width)//2,58-crop.height))
 return out.resize((256,256),Image.Resampling.NEAREST)

def layer(base,box):
 out=transparent();out.paste(base.crop(box),box[:2]);return out

def rotate(piece,pivot,angle,dy=0,dx=0):
 # nearest-neighbour only; keep straight pixel boundaries at all times.
 r=piece.rotate(angle,Image.Resampling.NEAREST,center=pivot)
 out=transparent();out.alpha_composite(r,(int(dx),int(dy)));return out

def animal_frames(base, rig, action):
 import numpy as np
 source=np.asarray(base);box=base.getbbox();x0,y0,x1,y1=box;w=x1-x0;h=y1-y0
 Y,X=np.mgrid[:256,:256].astype(float)
 def smooth(v):
  v=np.clip(v,0,1);return v*v*(3-2*v)
 def turn(xx,yy,px,py,degrees,weight):
  angle=degrees*math.pi/180*weight;c=np.cos(angle);s=np.sin(angle)
  dx=xx-px;dy=yy-py
  return px+c*dx+s*dy,py-s*dx+c*dy
 frames=[]
 phases=(0,math.pi,math.pi/2,3*math.pi/2) if rig in ('equine','tortoise') else (0,math.pi,math.pi,0)
 leg_start=y0+h*.74
 for i in range(N):
  t=2*math.pi*i/N;xx=X.copy();yy=Y.copy()
  moving=action in ('walk','run','flee')
  amplitude=(8 if action in ('run','flee') else 5) if rig!='tortoise' else 2
  hop=-round(max(0,math.sin(t))*7) if rig=='rabbit' and moving else 0
  if moving:yy-=hop-1.5*abs(math.sin(t))
  # Smooth weight fields keep neck, hip and tail joints connected. There are
  # no separately cut layers or duplicate limbs, and no cross-fading.
  head_weight=smooth((xx-(x0+w*.59))/(w*.22))*(1-smooth((yy-(y0+h*.56))/(h*.15)))
  angle=(6+math.sin(t)*3) if action in ('eat','drink','sniff') else math.sin(t)*(3 if action in ('observe','groom') else .6)
  xx,yy=turn(xx,yy,x0+w*.67,y0+h*.52,angle,head_weight)
  if rig not in ('bird','tortoise','small_mammal','rabbit'):
   tail_weight=(1-smooth((xx-(x0+w*.08))/(w*.17)))*(1-smooth((yy-(y0+h*.58))/(h*.17)))
   xx,yy=turn(xx,yy,x0+w*.22,y0+h*.58,math.sin(t)*5,tail_weight)
  legweight=smooth((yy-leg_start)/(h*.18))
  for j in range(4):
   center=x0+w*(.13+.24*j)
   weight=np.maximum(0,1-np.abs(xx-center)/(w*.24))*legweight
   theta=t+phases[j]
   if moving:
    xx+=math.sin(theta)*amplitude*weight
    yy+=max(0,math.cos(theta))*3*weight
   elif action=='groom' and j==3 and rig in ('cat','dog','rabbit','small_mammal'):
    xx,yy=turn(xx,yy,center,leg_start,12+math.sin(t)*4,weight)
  if not moving:
   torso=smooth((xx-x0)/(w*.15))*(1-smooth((xx-(x0+w*.72))/(w*.20)))
   yy+=math.sin(t)*.7*torso*(1-legweight)
  xi=np.rint(xx).astype(int);yi=np.rint(yy).astype(int)
  valid=(xi>=0)&(xi<256)&(yi>=0)&(yi<256)
  arr=np.zeros_like(source);arr[valid]=source[yi[valid],xi[valid]]
  out=Image.fromarray(arr)
  if rig=='bird' and action=='fly':
   # Find an ACTUAL shoulder pixel. Long bird tails make bbox midpoint an
   # invalid wing anchor. The wing root is always inside the native body.
   goal=(x0+w*.73,y0+h*.60)
   ys,xs=np.where(source[:,:,3]>0)
   distance=(xs-goal[0])**2+(ys-goal[1])**2
   nearest=int(np.argmin(distance));ax,ay=int(xs[nearest]),int(ys[nearest])
   feather=tuple(int(v) for v in source[ay,ax])
   draw=ImageDraw.Draw(out);lift=round(8+23*(math.sin(t)+1)/2)
   draw.polygon([(ax+7,ay+7),(ax-23,ay-lift),(ax-32,ay-lift+8),(ax-15,ay+13),(ax+7,ay+10)],fill=feather,outline=(39,41,40,255))
   draw.line((ax-25,ay-lift+7,ax-9,ay+8),fill=(68,72,62,255),width=2)
   draw.ellipse((ax-5,ay-4,ax+8,ay+10),fill=feather)
   elevated=transparent();elevated.alpha_composite(out,(0,-10-round(math.sin(t)*3)));out=elevated
  if action=='rest':
   bb=out.getbbox();c=out.crop(bb);height=round(c.height*.88)
   c=c.resize((c.width,height),Image.Resampling.NEAREST)
   out=transparent();out.alpha_composite(c,(bb[0],232-height))
  out=out.resize((128,128),Image.Resampling.NEAREST).resize((256,256),Image.Resampling.NEAREST)
  frames.append(out)
 return frames

def build(atlas):
 sprites=tiles(atlas)
 for index,spec in enumerate(PETS):
  folder=ROOT/'pets'/spec[0];folder.mkdir(exist_ok=True)
  override=ROOT/'production'/(spec[0]+'-source.png')
  tile=Image.open(override).convert('RGBA') if override.exists() else sprites[index]
  base=normalize(tile);base.save(folder/'frame_01.png')
  profile=json.loads((folder/'profile.json').read_text());rig=spec[7]
  manifest=dict(version=1,frameWidth=256,frameHeight=256,anchor=[.5,.90625],animations={},technique='anatomical pixel rig; local phase cycles; original source atlas preserved',qualityNotes=['2D side-view animation; up/down movement shares side-view locomotion','Rest uses crouch approximation, not a separately painted sleeping pose'])
  action_dir=folder/'animations';action_dir.mkdir(exist_ok=True)
  overview=[]
  daily_path=folder/'animations/daily/manifest.json'
  daily_actions=set(json.loads(daily_path.read_text())['animations']) if daily_path.exists() else set()
  # Daily clips have their own actual trajectories/painted poses. This older
  # builder must not recreate them with its generic idle fallback.
  for j,action in enumerate(a for a in profile['animal']['allowedActions'] if a not in daily_actions):
   frames=animal_frames(base,rig,action)
   atlas_img=Image.new('RGBA',(256*N,256))
   for k,f in enumerate(frames):atlas_img.alpha_composite(f,(256*k,0))
   atlas_img.save(action_dir/(action+'.png'))
   ms=60 if action in ('run','flee','fly') else 80
   gif_save(frames,action_dir/(action+'.gif'),ms)
   keyframe=frames[4];keyframe.save(folder/f'frame_{j+2:02d}.png')
   frame_dir=action_dir/action;frame_dir.mkdir(exist_ok=True)
   for k,f in enumerate(frames):f.save(frame_dir/f'{k:02d}.png')
   manifest['animations'][action]=dict(atlas='animations/'+action+'.png',gif='animations/'+action+'.gif',frames=N,frameMs=ms,loop=True)
   if action=='walk':
    # Viewpoint remains natural side-on; no fake front view or invented limbs.
    for direction in ('right','left','down','up'):
     df=[ImageOps.mirror(f) for f in frames] if direction=='left' else frames
     da=Image.new('RGBA',(256*N,256))
     for k,f in enumerate(df):da.alpha_composite(f,(256*k,0))
     alias='walk_'+direction;da.save(action_dir/(alias+'.png'));gif_save(df,action_dir/(alias+'.gif'),ms)
     manifest['animations'][alias]=dict(atlas='animations/'+alias+'.png',gif='animations/'+alias+'.gif',frames=N,frameMs=ms,loop=True)
   overview+=frames
  gif_save(overview,folder/'overview.gif',80)
  (folder/'animation.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
  if (folder/'animations/daily/manifest.json').exists():
   from build_daily_actions import restore_daily_metadata
   restore_daily_metadata(folder)
  print(spec[0],len(manifest['animations']),'animations')
 return True

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('atlas');build(p.parse_args().atlas)
