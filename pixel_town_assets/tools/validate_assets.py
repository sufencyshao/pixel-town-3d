#!/usr/bin/env python3
"""Validate ready/pending town entities without concealing unfinished assets.
Creates machine-readable JSON and a concise Markdown QA report. GIF frame merges
are permitted only when total timing agrees; they are reported as warnings.
"""
from pathlib import Path
import argparse,json,hashlib
from collections import Counter
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]

def components(mask):
 # 8-neighbour components on a 64px silhouette; ignore single logical pixels.
 mask=np.asarray(Image.fromarray(mask.astype('uint8')*255).resize((64,64),Image.Resampling.NEAREST))>0
 seen=np.zeros(mask.shape,bool);areas=[]
 for y,x in zip(*np.where(mask)):
  if seen[y,x]:continue
  q=[(int(y),int(x))];seen[y,x]=1;area=0
  while q:
   yy,xx=q.pop();area+=1
   for dy,dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
    ny,nx=yy+dy,xx+dx
    if 0<=ny<64 and 0<=nx<64 and mask[ny,nx] and not seen[ny,nx]:seen[ny,nx]=1;q.append((ny,nx))
  if area>=3:areas.append(area)
 return sorted(areas,reverse=True)

def inspect(folder,group):
 result={'category':group,'id':folder.name,'status':'ready','errors':[],'warnings':[],'animations':[]}
 error=result['errors'].append;warn=result['warnings'].append
 for n in ('profile.md','profile.json'):
  if not (folder/n).is_file():error(f'missing {n}')
 try:
  profile=json.loads((folder/'profile.json').read_text())
  if not profile.get('presets'):warn('no selectable presets found in profile.json')
 except Exception as e:error(f'profile parse: {e}');profile={}
 mfpath=next((folder/n for n in ('animation.json','animations/manifest.json','manifest.json') if (folder/n).is_file()),None)
 if not mfpath:
  result['status']='pending';result['warnings'].append('animation manifest not yet supplied');return result
 try:mf=json.loads(mfpath.read_text())
 except Exception as e:error(f'manifest parse: {e}');result['status']='invalid';return result
 fw=mf.get('frameWidth');fh=mf.get('frameHeight')
 if (fw,fh)!=(256,256):error(f'unsupported cell {fw}x{fh}');result['status']='invalid';return result
 if len(mf.get('anchor',[]))!=2:error('missing anchor')
 for name,sha in mf.get('sourceSHA256',{}).items():
  if not (folder/name).exists() or hashlib.sha256((folder/name).read_bytes()).hexdigest()!=sha:error(f'source hash mismatch: {name}')
 basics=sorted(folder.glob('frame_*.png'))
 if group=='characters' and len(basics)<16:error(f'only {len(basics)} of 16 basic PNGs')
 if group=='pets' and len(basics)<2:error('missing basic action PNGs')
 if group=='codexmini' and not (folder/'basic_actions.png').is_file():error('missing basic_actions.png')
 for p in basics:
  try:
   im=Image.open(p);im.load()
   if im.mode!='RGBA' or im.size!=(fw,fh):error(f'{p.name}: invalid mode/size')
   elif im.getchannel('A').getextrema()[0]!=0:error(f'{p.name}: no transparency')
  except Exception as e:error(f'{p.name}: {e}')
 if not (folder/'overview.gif').exists():error('missing overview.gif')
 for action,a in mf.get('animations',{}).items():
  row={'action':action,'atlasFrames':a.get('frames'),'gifFrames':None,'totalMs':None,'alpha':[],'canvasEdges':False,'maximumSignificantComponents':None}
  result['animations'].append(row)
  ap=folder/a.get('atlas','');gp=folder/a.get('gif','')
  if not ap.is_file():error(f'{action}: missing atlas');continue
  try:
   image=Image.open(ap);image.load()
   count=a['frames'];row['alpha']=np.unique(np.asarray(image)[:,:,3]).tolist() if image.mode=='RGBA' else []
   if image.mode!='RGBA' or image.size!=(fw*count,fh):error(f'{action}: invalid RGBA atlas size');continue
   arr=np.asarray(image);frames=[arr[:,i*fw:(i+1)*fw] for i in range(count)]
   if 0 not in row['alpha'] or 255 not in row['alpha']:error(f'{action}: missing transparent or opaque pixels')
   if row['alpha']!=[0,255]:warn(f'{action}: partial alpha retained')
   row['canvasEdges']=bool(any(np.any(f[0,:,3]) or np.any(f[-1,:,3]) or np.any(f[:,0,3]) or np.any(f[:,-1,3]) for f in frames))
   if row['canvasEdges']:warn(f'{action}: opaque pixels on canvas edge; visual review required')
   if any(not f[:,:,3].any() for f in frames):error(f'{action}: empty frame')
   if group=='pets':
    counts=[len(components(f[:,:,3]>0)) for f in frames];row['maximumSignificantComponents']=max(counts)
    if max(counts)>1:warn(f'{action}: {max(counts)} significant disconnected silhouette pieces; inspect anatomy')
   row['uniqueFrames']=len({hashlib.sha256(f.tobytes()).hexdigest() for f in frames})
  except Exception as e:error(f'{action}: atlas read {e}');continue
  if not gp.is_file():error(f'{action}: missing GIF');continue
  try:
   gf=Image.open(gp);gf.load();row['gifFrames']=gf.n_frames;row['gifLoop']=gf.info.get('loop')
   elapsed=0;gdur=[];trans=True
   for i in range(gf.n_frames):
    gf.seek(i);dur=gf.info.get('duration',0);elapsed+=dur;gdur.append(dur)
    rg=gf.convert('RGBA');trans=trans and rg.getchannel('A').getextrema()[0]==0
   row['totalMs']=elapsed;row['gifDurations']=gdur;row['gifTransparent']=bool(trans)
   expected=sum(a['durations']) if 'durations' in a else a['frames']*a['frameMs']
   if elapsed!=expected:error(f'{action}: GIF duration {elapsed} != expected {expected}')
   if not trans:error(f'{action}: GIF lacks transparent background')
   if gf.n_frames!=count:warn(f'{action}: GIF merged/reduced {count} atlas frames to {gf.n_frames}; total timing checked')
   if a.get('loop',True) and row['gifLoop']!=0:error(f'{action}: infinite GIF loop flag missing')
   if not a.get('loop',True) and row['gifLoop']==0:warn(f'{action}: one-shot manifest action previews as looping GIF')
  except Exception as e:error(f'{action}: GIF read {e}')
 if not mf.get('animations'):error('empty animation manifest')
 if result['errors']:result['status']='invalid'
 return result

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',default='validation');args=parser.parse_args();dest=ROOT/args.output;dest.mkdir(exist_ok=True)
 rows=[]
 for group in ('characters','pets','codexmini'):
  for f in sorted((ROOT/group).iterdir()):
   if f.is_dir() and ((f/'profile.md').exists() or (f/'profile.json').exists()):
    rows.append(inspect(f,group));print(group+'/'+f.name+': '+rows[-1]['status'],flush=True)
 summary={'entities':len(rows),'categories':dict(Counter(r['category'] for r in rows)),'status':dict(Counter(r['status'] for r in rows)),'animations':sum(len(r['animations']) for r in rows),'errors':sum(len(r['errors']) for r in rows),'warnings':sum(len(r['warnings']) for r in rows)}
 (dest/'asset-validation.json').write_text(json.dumps({'summary':summary,'entities':rows},ensure_ascii=False,indent=2)+'\n')
 lines=['# 小镇素材统一检查','',f"对象：{summary['entities']}；动画：{summary['animations']}；技术错误：{summary['errors']}；提示：{summary['warnings']}。",'',f"状态：{summary['status']}。状态 ready 仅表示文件与动画格式检查通过，不能代替逐帧视觉和动作语义验收。",'', '| 类别 | 对象 | 状态 | 动作 | 问题 |','|---|---|---|---:|---|']
 for r in rows:lines.append('| '+r['category']+' | '+r['id']+' | '+r['status']+' | '+str(len(r['animations']))+' | '+'；'.join(r['errors'] or r['warnings'][:2] or ['通过文件检查'])+' |')
 lines+=['','视觉记录另见 `visual-review.md` 和 `pets-visual-page-*.png`。新增人物缺素材时保留 pending，不将预设资料目录算作完整美术交付。','', 'GIF 合并连续重复帧只记录提示，仍逐动画核对总时长。Codexmini 原始不等时长通过 durations 数组核对；源素材保留半透明边缘时提示，不重绘原作。']
 (dest/'asset-validation.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps(summary,ensure_ascii=False,indent=2))
 return 0 if summary['errors']==0 else 1
if __name__=='__main__':raise SystemExit(main())
