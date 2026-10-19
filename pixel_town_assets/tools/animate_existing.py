#!/usr/bin/env python3
"""Reproducible nearest-neighbour skeletal deformation of original town sprites.
Only reads original frame_NN.png. Outputs RGBA atlases and transparent GIFs.
No optical blending, no redrawing of faces. See animation-production.md limitations.
"""
from pathlib import Path
import json, math, hashlib, argparse
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
SIZE=256; FEET=230; N=16; MS=80
NECK=[.43,.44,.45,.55,.49,.52,.50,.48,.53,.45,.55,.48,.54,.48,.50,.48,.46,.48,.46,.47]
SKIRTS={2,12,13,14,15,16,17,18,20}
# Newly generated residents have trousers and a different, wider two-head rig.
NEW_NECK=[.48,.47,.55,.51,.47,.48,.48,.49,.48,.49,.48,.46,.53,.50,.48,.49,.47,.48,.47,.49]
ACTIONS=['idle','walk_down','walk_left','walk_right','walk_up','wave','surprise','sit','jump','cheer','work']
SOURCE={'idle':1,'walk_down':1,'walk_left':4,'walk_right':7,'walk_up':10,'wave':14,'surprise':15,'sit':16,'jump':1,'cheer':11,'work':1}
Y,X=np.mgrid[:SIZE,:SIZE].astype(float)
def smooth(v):
 v=np.clip(v,0,1);return v*v*(3-2*v)
def clean_source(path):
 src=Image.open(path).convert('RGBA');arr=np.array(src);mask=arr[:,:,3]>0;seen=np.zeros(mask.shape,bool)
 # A few source slices contain a tiny shoe fragment from the preceding grid row.
 # Remove only small disconnected components wholly within the top 38 pixels.
 for cy,cx in zip(*np.where(mask[:38])):
  if seen[cy,cx]:continue
  queue=[(int(cy),int(cx))];seen[cy,cx]=True;component=[]
  while queue:
   py,px=queue.pop();component.append((py,px))
   for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
    ny,nx=py+dy,px+dx
    if 0<=ny<256 and 0<=nx<256 and mask[ny,nx] and not seen[ny,nx]:seen[ny,nx]=True;queue.append((ny,nx))
  if len(component)<300 and max(py for py,px in component)<38:
   for py,px in component:arr[py,px]=0
 return Image.fromarray(arr)

def normalize(path,action):
 src=clean_source(path);box=src.getbbox();cut=src.crop(box)
 # Extra headroom allows genuine jump trajectories without cutting hair.
 h=168 if action=='sit' else 210
 w=round(cut.width*h/cut.height);cut=cut.resize((w,h),Image.Resampling.NEAREST)
 im=Image.new('RGBA',(SIZE,SIZE));im.paste(cut,((SIZE-w)//2,FEET-h))
 return np.asarray(im),((SIZE-w)/2,FEET-h,w,h)
def rotate_inverse(x,y,px,py,angle,weight):
 a=angle*weight;c=np.cos(a);s=np.sin(a);dx=x-px;dy=y-py
 return px+c*dx+s*dy,py-s*dx+c*dy

def frame(src,box,idx,role,action):
 left,top,w,h=box;phase=idx*2*math.pi/N;s=math.sin(phase);c=math.cos(phase)
 neck_ratio=NEW_NECK[role-21] if 21<=role<=40 else NECK[(role-1)%20]
 neck=top+h*neck_ratio;shoulder=neck+h*.075
 hip=top+h*(.76 if 21<=role<=40 else .79 if neck_ratio>.5 else .75)
 leg_start=top+h*(.78 if 21<=role<=40 else .88 if role in SKIRTS else .77)
 xx=X.copy();yy=Y.copy()
 # Global component contains grounding/breathing, while limb weights below
 # make head, arms and legs move independently and in opposite phases.
 bob=0.;headangle=math.radians(1.1)*s;armamp=2.;legamp=0.
 if action.startswith('walk'):
  bob=-1.6*(1-math.cos(2*phase))/2;headangle=math.radians(.7)*s;armamp=12.;legamp=10.
 elif action=='wave':armamp=8.;headangle=math.radians(2)*s
 elif action=='surprise':armamp=3.5;headangle=math.radians(2.5)*s;bob=-1.3*(1-c)/2
 elif action=='sit':armamp=2.;headangle=math.radians(1.7)*s
 elif action=='jump':
  # Smooth launch/air/landing. Starts and closes on the exact grounded pose.
  u=idx/N;bob=-15*math.sin(math.pi*u)**2;armamp=8.;legamp=5.;headangle=math.radians(1.2)*s
 elif action=='cheer':armamp=5.5;bob=-2*(1-math.cos(2*phase))/2;headangle=math.radians(1.6)*s
 elif action=='work':armamp=8.;headangle=math.radians(2)*math.sin(phase+.35)
 headangle+=math.radians(.45)*math.cos(phase+.1)
 yy-=bob
 # Independent head tilt around the neck, with a short smooth join.
 hw=1-smooth((yy-(neck-5))/12)
 xx,yy=rotate_inverse(xx,yy,128,neck,headangle,hw)
 # Breathing in the torso with shoulders anchored: no whole-image scale pulse.
 torso=smooth((yy-neck)/12)*(1-smooth((yy-hip)/10))
 xx=128+(xx-128)/(1+.006*s*torso)
 # Right/left upper-limb arcs. Lateral masks protect hair, face and skirt.
 raised=action in ('wave','cheer')
 armtop=neck-h*.20 if raised else shoulder-6
 armend=hip-7
 yw=smooth((yy-armtop)/9)*(1-smooth((yy-armend)/10))
 core=w*.225
 for side in (-1,1):
  lateral=smooth((side*(xx-128)-core)/(w*.105))
  weight=yw*lateral
  # Raised pose hands rotate around their existing shoulder, independently.
  a=math.radians(armamp)*math.sin(phase+(0 if side<0 else math.pi))
  if action=='work':a=math.radians(armamp)*math.sin(phase+(0 if side<0 else .8))
  xx,yy=rotate_inverse(xx,yy,128+side*w*.20,shoulder,a,weight)
 # Alternating hips/feet, strongest below the skirt hem for skirt wearers.
 if action!='sit':
  lw=smooth((yy-leg_start)/8)
  for side in (-1,1):
   sideweight=smooth((side*(xx-128)+2)/5)*lw
   a=math.radians(legamp)*math.sin(phase+(0 if side<0 else math.pi))
   xx,yy=rotate_inverse(xx,yy,128+side*w*.115,leg_start,a,sideweight)
   if action.startswith('walk'):
    # Swing-foot lift is tied to gait phase, without shifting the grounded foot.
    yy+=4.0*max(0,math.cos(phase+(0 if side<0 else math.pi)))*sideweight*smooth((yy-(FEET-24))/18)
 xi=np.rint(xx).astype(int);yi=np.rint(yy).astype(int);valid=(xi>=0)&(xi<SIZE)&(yi>=0)&(yi<SIZE)
 out=np.zeros_like(src);out[valid]=src[yi[valid],xi[valid]]
 out[out[:,:,3]==0,:3]=0
 im=Image.fromarray(out,'RGBA')
 if action=='work':draw_work_prop(im,role,hip,phase)
 return im

def draw_work_prop(im,role,hip,phase):
 """Small hard-edge occupational props; hand-tool trajectories are independent."""
 d=ImageDraw.Draw(im);yy=round(hip-10);k=round(3*math.sin(phase));ink='#33323e';paper='#f5e5bd';wood='#aa7445'
 if 21<=role<=40:
  # Specific tools convey an occupational task; no vehicle/tool physics claim.
  if role==21:
   d.ellipse((109,yy-4,139,yy+21),fill=ink);d.ellipse((113,yy,135,yy+17),fill='#d1ab57');d.ellipse((117,yy+4,131,yy+13),fill=ink)
   d.line((136,yy+5,148+k,yy-2),fill='#d1ab57',width=5);d.rectangle((146+k,yy-6,152+k,yy+2),fill='#8c9a9f',outline=ink,width=1);return
  if role in (22,32):
   d.rectangle((109,yy-3,148,yy+20),fill='#b88951',outline=ink,width=2);d.rectangle((112,yy+1,145,yy+6),fill='#c9a169')
   d.line((128,yy-3,128,yy+20),fill='#8d6338',width=3);d.line((115,yy+10,122,yy+10),fill=ink,width=2);d.rectangle((139+k,yy-8,145+k,yy-1),fill='#7d9654',outline=ink,width=1);return
  if role in (23,33):
   d.polygon(((112,yy-3),(132,yy-3),(137,yy+20),(107,yy+20)),fill='#c7ae75',outline=ink);d.rectangle((119,yy-6,126,yy-2),fill='#927348')
   d.line((121,yy+14,121,yy+4),fill='#527554',width=2);d.ellipse((115,yy+5,121,yy+10),fill='#789260');d.ellipse((122,yy+2,129,yy+7),fill='#789260')
   d.line((145,yy+18,154+k,yy-12),fill=wood,width=4);d.polygon(((152+k,yy-15),(163+k,yy-13),(160+k,yy-5),(151+k,yy-8)),fill='#8b979e',outline=ink);return
  if role in (25,35):
   d.rectangle((112,yy-4,116,yy+17),fill='#514951');
   for tooth in range(6):d.line((116,yy-3+tooth*3,123,yy-3+tooth*3),fill='#514951',width=2)
   d.ellipse((131,yy+8,139,yy+16),outline='#a9b4bc',width=2);d.ellipse((140,yy+8,148,yy+16),outline='#a9b4bc',width=2)
   d.line((136,yy+10,147+k,yy-8),fill='#a9b4bc',width=3);d.line((144,yy+10,133-k,yy-8),fill='#a9b4bc',width=3);d.rectangle((138,yy+3,142,yy+7),fill=ink);return
  if role==28:
   d.line((119,yy+18,143+k,yy-6),fill='#a4acb3',width=7);d.ellipse((114,yy+11,125,yy+22),fill='#a4acb3',outline=ink,width=1);d.ellipse((118,yy+15,121,yy+18),fill=ink)
   d.polygon(((138+k,yy-12),(143+k,yy-8),(148+k,yy-13),(152+k,yy-9),(149+k,yy-1),(143+k,yy+2),(136+k,yy-4)),fill='#a4acb3',outline=ink);return
  # Reuse existing tool artwork with occupation semantics mapped explicitly.
  role={24:7,26:4,27:16,29:14,30:12,31:7,34:7,36:3,37:5,38:6,39:7,40:8}[role]
 if role in (1,2,6,7,8,14,15,16,20):
  d.rectangle((112,yy-3,143,yy+18),fill=ink);d.rectangle((115,yy,140,yy+15),fill=paper)
  if role==6:
   d.line((115,yy,127,yy+8,140,yy),fill='#ba7770',width=2)
  elif role==15:
   d.rectangle((126,yy+3,130,yy+13),fill='#c24e54');d.rectangle((122,yy+6,134,yy+10),fill='#c24e54')
  else:
   for n in range(3):d.line((119,yy+3+n*4,135,yy+3+n*4),fill='#969887',width=1)
   d.line((141,yy+4+k,146,yy-3+k),fill='#675b5b',width=3)
 elif role in (3,17):
  d.rectangle((117,yy+5,136,yy+18),fill='#f3ded0',outline=ink,width=2);d.rectangle((121,yy+2,133,yy+5),fill='#664139')
  d.arc((132,yy+6,143,yy+15),270,90,fill=ink,width=2);d.line((132+k,yy-4,126+k,yy+7),fill=wood,width=3)
 elif role in (4,13):
  d.rectangle((106,yy+18,150,yy+23),fill=wood,outline=ink,width=2);d.ellipse((113,yy+6,144,yy+18),fill='#edc995',outline='#b27848',width=2)
  if role==4:d.rectangle((111+k,yy+5,145+k,yy+9),fill='#996643',outline=ink,width=1)
  else:d.polygon(((139+k,yy-5),(147+k,yy-4),(141+k,yy+10)),fill='#f9eee0',outline=ink)
 elif role in (5,11):
  d.rectangle((109,yy+16,150,yy+21),fill=wood,outline=ink,width=2)
  if role==5:
   d.rectangle((117,yy+8,142,yy+15),fill='#e0b684',outline=ink,width=1);d.line((144,yy+11,148+k,yy-4-k),fill=wood,width=4);d.rectangle((141+k,yy-8-k,153+k,yy-3-k),fill='#8b989d',outline=ink,width=1)
  else:
   d.ellipse((110,yy+9,140,yy+17),fill='#535865',outline=ink,width=2);d.line((141+k,yy-2,130+k,yy+10),fill='#b0b7bb',width=3);d.rectangle((137+k,yy-5,146+k,yy),fill='#bac0c1',outline=ink,width=1)
 elif role==9:
  d.rectangle((115,yy+4,140,yy+20),fill='#608774',outline=ink,width=2);d.arc((119,yy-6,141,yy+11),180,360,fill=ink,width=3);d.polygon(((139,yy+8),(151+k,yy+2),(153+k,yy+5),(139,yy+14)),fill='#7d9f89',outline=ink)
 elif role==10:
  d.ellipse((113,yy-2,141,yy+23),fill='#af7548',outline=ink,width=2);d.ellipse((123,yy+5,132,yy+14),fill=ink);d.rectangle((138,yy-12,145,yy+8),fill=wood,outline=ink,width=1);d.line((137+k,yy+3,128+k,yy+12),fill='#e5b68e',width=3)
 elif role==12:
  d.polygon(((116,yy+2),(141,yy+2),(132,yy+23),(125,yy+23)),fill='#d6c5a5',outline=ink)
  for x,y,c in [(119,yy-1,'#eeaaad'),(129,yy-6,'#f5d373'),(140,yy-1,'#d9a2cc')]:
   d.line((x,y,129,yy+13),fill='#68885d',width=2);d.ellipse((x-4,y-4,x+4,y+4),fill=c,outline='#825968',width=1)
 elif role==18:
  d.ellipse((112,yy+4,143,yy+19),fill='#bf956b',outline=ink,width=2)
  for x,c in [(119,'#b35857'),(127,'#e4cc64'),(136,'#5d8caa')]:d.rectangle((x,yy+8,x+4,yy+12),fill=c)
  d.line((146+k,yy-3,137+k,yy+9),fill=wood,width=3);d.rectangle((142+k,yy-6,147+k,yy-2),fill='#656281')
 elif role==19:
  d.ellipse((115,yy+8,143,yy+18),fill='#8296a2',outline=ink,width=2);d.ellipse((117,yy+7,141,yy+12),fill='#76583f',outline=ink,width=1);d.line((145+k,yy-2,134+k,yy+8),fill='#d0d7d7',width=3)

def palette_frames(frames):
 # Reserve index 0 for transparency; all opaque colors mapped to indices 1..255.
 sample=Image.new('RGB',(SIZE*len(frames),SIZE),(0,0,0))
 for i,im in enumerate(frames):sample.paste(im.convert('RGB'),(i*SIZE,0))
 pal=sample.quantize(colors=255,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
 palette=pal.getpalette()[:765];full=[0,0,0]+palette
 full+=([0]*(768-len(full)))
 fixed=Image.new('P',(1,1));fixed.putpalette(palette+[0,0,0])
 result=[]
 for im in frames:
  q=np.array(im.convert('RGB').quantize(palette=fixed,dither=Image.Dither.NONE)).astype(np.uint16)+1
  q=np.minimum(q,255).astype(np.uint8);q[np.asarray(im)[:,:,3]<128]=0
  p=Image.fromarray(q,'P');p.putpalette(full);p.info['transparency']=0;result.append(p)
 return result

def save_gif(frames,path):
 fs=palette_frames(frames);fs[0].save(path,save_all=True,append_images=fs[1:],duration=MS,loop=0,transparency=0,disposal=2,optimize=False)
def save_atlas(frames,path):
 atlas=Image.new('RGBA',(SIZE*len(frames),SIZE))
 for i,im in enumerate(frames):atlas.paste(im,(i*SIZE,0))
 atlas.save(path)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--folders',nargs='+',help='character folder names; defaults to original 01..20');args=parser.parse_args()
 dirs=sorted((ROOT/'characters'/name for name in args.folders) if args.folders else (p for p in (ROOT/'characters').glob('[012][0-9]_*') if p.is_dir() and int(p.name[:2])<=20));report=[];show=[]
 for folder in dirs:
  role=int(folder.name[:2]);dest=folder/'animations';dest.mkdir(exist_ok=True)
  manifest={'version':1,'frameWidth':SIZE,'frameHeight':SIZE,'anchor':[.5,.9],'animations':{},'renderer':'nearest-neighbour anatomical weighted rigid deformation','sourcePreserved':True,'sourceSHA256':{}}
  if role>20:manifest['qualityNotes']=['Continuous anatomical rig derived from genuine front/left/back/wave/sit/cheer key poses','Work tools are occupational visual indications; tool interaction and vehicle physics are not simulated','Right view is a mirror of the left-view source']
  overview=[];samples={}
  for action in ACTIONS:
   source=folder/f'frame_{SOURCE[action]:02}.png'
   # frame_11/12 now mean back-walk steps for repaired original residents.
   # Keep the original cheer pose available for reproducible animation builds.
   if action=='cheer' and (folder/'legacy_actions/frame_11.png').exists():
    source=folder/'legacy_actions/frame_11.png'
   if not source.exists():
    if role>20:raise FileNotFoundError(f'{folder.name}: required pose {source.name} missing; refusing stand-in animation')
    source=folder/'frame_01.png'
   source_name=source.relative_to(folder).as_posix()
   manifest['sourceSHA256'][source_name]=hashlib.sha256(source.read_bytes()).hexdigest()
   src,box=normalize(source,action);frames=[frame(src,box,i,role,action) for i in range(N)]
   save_atlas(frames,dest/f'{action}.png');save_gif(frames,dest/f'{action}.gif');overview.extend(frames);samples[action]=frames
   gf=Image.open(dest/f'{action}.gif')
   unique=len(set(hashlib.sha256(im.tobytes()).hexdigest() for im in frames))
   manifest['animations'][action]={'atlas':f'animations/{action}.png','gif':f'animations/{action}.gif','frames':N,'frameMs':MS,'loop':True,'gifFrames':gf.n_frames,'source':source_name}
   report.append({'role':folder.name,'action':action,'frames':N,'gifFrames':gf.n_frames,'uniqueFrames':unique,'durationMs':sum(gf.seek(i) or gf.info.get('duration',0) for i in range(gf.n_frames)),'transparent':bool(gf.info.get('transparency')==0 or np.array(frames[0])[:,:,3].min()==0),'alphaValues':np.unique(np.asarray(frames[0])[:,:,3]).tolist()})
  if role>20:
   keydir=dest/'keyframes';keydir.mkdir(exist_ok=True)
   basic=Image.new('RGB',(256*4,280*3),(223,231,226));bd=ImageDraw.Draw(basic)
   for j,action in enumerate(ACTIONS):
    im=samples[action][4 if action!='idle' else 0];im.save(keydir/(action+'.png'))
    bx=(j%4)*256;by=(j//4)*280;basic.paste(im,(bx,by),im);bd.text((bx+8,by+258),action,fill=(31,47,42))
   basic.save(folder/'basic_actions.png');manifest['previewBoard']='basic_actions.png'
  save_gif(overview,folder/'overview.gif');(folder/'animation-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');(folder/'animation.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
  if (folder/'legacy_actions/frame_11.png').exists():
   from complete_back_walk import complete_folder
   complete_folder(folder)
  if (folder/'animations/daily/manifest.json').exists():
   from build_daily_actions import restore_daily_metadata
   restore_daily_metadata(folder)
  # Local labelled contact sheet makes four phases of real articulation reviewable.
  contact=Image.new('RGB',(128*8,148*3),(207,218,216));d=ImageDraw.Draw(contact)
  for row,action in enumerate(['walk_down','wave','work']):
   for col,k in enumerate(range(0,N,2)):
    im=samples[action][k].resize((128,128),Image.Resampling.NEAREST);contact.paste(im,(col*128,row*148),im);d.text((col*128+3,row*148+130),f'{action} {k}',fill=(30,45,42))
  contact.save(dest/'motion-preview.png');show.append(samples['walk_down']);print(f'{folder.name}: 11 animated actions + overview',flush=True)
 (ROOT/'tools'/('selected-animation-generation.json' if args.folders else 'existing-animation-generation.json')).write_text(json.dumps(report,indent=2)+'\n')
 overviewframes=[]
 for k in range(N):
  board=Image.new('RGBA',(128*5,128*max(1,math.ceil(len(show)/5))))
  for j,fs in enumerate(show):board.alpha_composite(fs[k].resize((128,128),Image.Resampling.NEAREST),((j%5)*128,(j//5)*128))
  overviewframes.append(board)
 # palette helper handles 256 canvases; create RGB GIF contact sheet directly.
 gifs=[]
 for im in overviewframes:
  bg=Image.new('RGB',im.size,(207,218,216));bg.paste(im,mask=im.getchannel('A'));gifs.append(bg.quantize(colors=255,dither=Image.Dither.NONE))
 gifs[0].save(ROOT/'tools'/('selected-cast-motion.gif' if args.folders else 'existing-cast-motion.gif'),save_all=True,append_images=gifs[1:],duration=MS,loop=0,optimize=False)
 print(f'Validation: {len(report)} actions / {len(dirs)} roles')
if __name__=='__main__':main()
