"""Split transparent generated atlases by connected sprites, avoiding grid cuts."""
from collections import deque
import numpy as np
from PIL import Image, ImageFilter

def tiles(path, count=20, columns=5, filter_size=5):
 im=Image.open(path).convert('RGBA')
 mask=np.array(im.getchannel('A').point(lambda x:255 if x>=128 else 0).filter(ImageFilter.MaxFilter(filter_size)))>0
 h,w=mask.shape; labels=np.zeros((h,w),np.int32);parts=[];ident=0
 for y,x in zip(*np.nonzero(mask)):
  y,x=int(y),int(x)
  if labels[y,x]:continue
  ident+=1;q=deque([(y,x)]);labels[y,x]=ident
  loX=hiX=x;loY=hiY=y;area=0
  while q:
   yy,xx=q.popleft();area+=1
   loX=min(loX,xx);hiX=max(hiX,xx);loY=min(loY,yy);hiY=max(hiY,yy)
   for ny,nx in ((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
    if 0<=ny<h and 0<=nx<w and mask[ny,nx] and not labels[ny,nx]:
     labels[ny,nx]=ident;q.append((ny,nx))
  if area>1500:parts.append((ident,(loX,loY,hiX+1,hiY+1)))
 # Generated neighbours can touch by one stray outline pixel. Split only a
 # genuinely double-width component, at the sparsest central vertical seam.
 while len(parts)<count:
  candidates=[p for p in parts if p[1][2]-p[1][0]>w/columns*1.65]
  if not candidates:break
  old,box=max(candidates,key=lambda p:p[1][2]-p[1][0]);bx,by,ex,ey=box
  span=ex-bx;lo=bx+round(span*.35);hi=bx+round(span*.65)
  projection=np.sum(labels[by:ey,lo:hi]==old,axis=0)
  seam=lo+int(np.argmin(projection));ident+=1
  region=labels[by:ey,seam:ex];region[region==old]=ident
  parts.remove((old,box));parts.extend([(old,(bx,by,seam,ey)),(ident,(seam,by,ex,ey))])
 if len(parts)!=count:raise ValueError(f'Expected {count} whole sprites, detected {len(parts)}. Inspect atlas before slicing.')
 parts.sort(key=lambda p:(p[1][1]+p[1][3])/2)
 ordered=[]
 for start in range(0,count,columns):ordered.extend(sorted(parts[start:start+columns],key=lambda p:p[1][0]))
 result=[]
 for ident,box in ordered:
  arr=np.array(im.crop(box));region=labels[box[1]:box[3],box[0]:box[2]]
  arr[:,:,3]=np.where((region==ident)&(arr[:,:,3]>=128),255,0)
  result.append(Image.fromarray(arr))
 return result
