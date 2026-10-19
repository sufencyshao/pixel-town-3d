"""Resident hair library: Quaternius CC0 source meshes plus solid sculpted additions.
Coordinates stay in the unmodified seed's local metre space, Z up, front -Y.
create_hair(rig, features, head_bounds, material_factory, bind_fn) -> mesh objects.
No source seed, source material, animation, or application state is modified.
"""
import bpy, bmesh, json, math
from pathlib import Path
from mathutils import Vector
_LIB=None
R=Path(__file__).resolve().parent

def _library():
 global _LIB
 if _LIB is None:_LIB=json.loads((R/'hair-library.json').read_text())
 return _LIB

def _rgb(value):
 if isinstance(value,str):return tuple((lambda c:c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4)(int(value.lstrip('#')[i:i+2],16)/255) for i in (0,2,4))
 return tuple(value[:3])

def create_hair(rig, features, head_bounds, material_factory, bind_fn):
 """Build one identity's hair. All returned objects are real meshes; the scalp shell is closed.
 Bounds must describe the complete canonical head (including ears), not scalp only.
 Any long rear locks are rigid Head-bound in this preview; no hair physics is claimed.
 """
 style=str(features.get('hairStyle','short')).lower().replace('_','-')
 detail=str(features.get('hairDetail','')).lower()
 if 'twin round buns' in detail:style='twin-buns'
 if 'curl' in detail and style in ('short','swept'):style='curly'
 aliases={'twinbuns':'twin-buns','twin-braid':'twinbraid','single-braid':'singlebraid','side-part':'sidepart','ponytail-high':'ponytail'};style=aliases.get(style,style)
 lo=Vector(head_bounds['min']);hi=Vector(head_bounds['max']);top=hi.z
 width=hi.x-lo.x;depth=hi.y-lo.y
 # Ear-inclusive source head widths are 0.25--0.27 m. Retain scalp dimensions,
 # rather than treating ear tips as the scalp and making a spherical helmet.
 s=max(.72,min(1.35,width/.25));sx=width/.25;sy=max(.78,min(1.25,depth/.245))
 cx=(hi.x+lo.x)/2;cy=.016*sy
 color=features.get('hairColor','#302821');rgb=_rgb(color)
 material=material_factory('Hair '+style,color,.78)
 accent=material_factory('Hair subtle strand '+style,tuple(min(1,v*1.13+.007) for v in rgb),.76)
 output=[]
 def mesh(name,verts,faces,mat=material):
  me=bpy.data.meshes.new(name+' mesh');me.from_pydata(verts,[],faces);me.update();me.materials.append(mat)
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
  ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob)
  for poly in me.polygons:poly.use_smooth=True
  bind_fn(ob,'Head');output.append(ob);ob['hair_style']=style;return ob
 def tube(name,points,radii,mat=material,sides=10):
  pts=[Vector(p) for p in points];verts=[];faces=[]
  if isinstance(radii,(float,int)):radii=[radii]*len(pts)
  for i,p in enumerate(pts):
   tangent=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized()
   ref=Vector((0,0,1)) if abs(tangent.z)<.9 else Vector((1,0,0))
   side=tangent.cross(ref).normalized();up=side.cross(tangent).normalized()
   rr=radii[i];ra,rb=(rr,rr) if isinstance(rr,(float,int)) else rr
   for j in range(sides):verts.append(tuple(p+side*(ra*math.cos(j*math.tau/sides))+up*(rb*math.sin(j*math.tau/sides))))
  for i in range(len(pts)-1):
   for j in range(sides):a=i*sides+j;b=i*sides+(j+1)%sides;faces.append((a,b,b+sides,a+sides))
  faces.append(tuple(reversed(range(sides))));faces.append(tuple((len(pts)-1)*sides+j for j in range(sides)))
  return mesh(name,verts,faces,mat)
 def ellipsoid(name,center,scale,mat=material,segments=20,rings=12):
  verts=[(center[0],center[1],center[2]+scale[2])];faces=[]
  for i in range(1,rings):
   th=math.pi*i/rings
   for j in range(segments):
    ph=math.tau*j/segments;verts.append((center[0]+scale[0]*math.sin(th)*math.cos(ph),center[1]+scale[1]*math.sin(th)*math.sin(ph),center[2]+scale[2]*math.cos(th)))
  bottom=len(verts);verts.append((center[0],center[1],center[2]-scale[2]))
  for j in range(segments):faces.append((0,1+j,1+(j+1)%segments))
  for i in range(rings-2):
   for j in range(segments):a=1+i*segments+j;b=1+i*segments+(j+1)%segments;faces.append((a,b,b+segments,a+segments))
  last=1+(rings-2)*segments
  for j in range(segments):faces.append((last+j,bottom,last+(j+1)%segments))
  return mesh(name,verts,faces,mat)
 def scalp():
  # Copy the actual mature head surface, then close a 4 mm shell around it.
  # A simple ellipsoid fits neither the flat forehead nor the temples and can
  # expose skin through its crown. This cap preserves the seed's real cranium.
  candidates=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers) and ('body' in o.name.lower() or 'skin' in o.name.lower())]
  if candidates:
   original=max(candidates,key=lambda o:len(o.data.vertices));bm=bmesh.new();bm.from_mesh(original.data)
   bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00002);bm.normal_update()
   keep=set()
   for f in bm.faces:
    p=f.calc_center_median();ph=math.atan2((p.y-cy)/(.115*sy),(p.x-cx)/(.108*sx));limit=top-(.140+.065*math.sin(ph))*s
    if p.z>limit and (abs(p.x-cx)<.109*sx or p.z>top-.078*s):keep.add(f)
   # Keep the crown component only; no incidental floating eyebrow/ear patch.
   components=[]
   while keep:
    first=keep.pop();stack=[first];component={first}
    while stack:
     f=stack.pop()
     for edge in f.edges:
      for other in edge.link_faces:
       if other in keep:keep.remove(other);component.add(other);stack.append(other)
    components.append(component)
   chosen=max(components,key=len) if components else set()
   if chosen:
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f not in chosen],context='FACES')
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    # Smooth just the jagged selection boundary, preserving the mature crown.
    boundary={v for e in bm.edges if e.is_boundary for v in e.verts}
    for repeat in range(3):
     positions={v:sum((e.other_vert(v).co for e in v.link_edges if e.is_boundary),Vector())/sum(1 for e in v.link_edges if e.is_boundary) for v in boundary}
     for v,p in positions.items():v.co=v.co.lerp(p,.24)
    bm.normal_update();bm.verts.ensure_lookup_table();bm.verts.index_update()
    count=len(bm.verts);outer=[tuple(v.co+v.normal*((.022+.005*math.sin(v.co.x*115)*math.sin(v.co.y*93+v.co.z*52)) if style=='curly' and 'voluminous' in detail else .006)*s) for v in bm.verts];inner=[tuple(v.co+v.normal*.002*s) for v in bm.verts]
    faces=[tuple(v.index for v in f.verts) for f in bm.faces]
    faces+=[tuple(v.index+count for v in reversed(f.verts[:])) for f in bm.faces]
    for edge in bm.edges:
     if edge.is_boundary:
      loop=edge.link_loops[0];a=loop.vert.index;b=loop.link_loop_next.vert.index;faces.append((b,a,a+count,b+count))
    bm.free();return mesh('Continuous scalp cap',outer+inner,faces)
   bm.free()
  # Fallback for callers that provide a rig without its seed body.
  # A thick continuous cap, sealed at its hairline. It covers crown/back/temples;
  # front edge follows the forehead, leaving eyes and eyebrows unobstructed.
  n=40;rings=12;rx=.113*sx;ry=.124*sy;rz=.142*s;cz=top-.133*s
  verts=[];faces=[]
  for layer in [0,1]:
   shrink=.0035 if layer else 0
   verts.append((cx,cy,cz+rz-shrink))
   for k in range(1,rings+1):
    for j in range(n):
     ph=j*math.tau/n;theta=(1.58+.43*math.sin(ph))*k/rings
     ripple=.0015*math.sin(3*ph+theta*4)*math.sin(theta)
     verts.append((cx+(rx-shrink+ripple)*math.sin(theta)**.45*math.cos(ph),cy+(ry-shrink+ripple)*math.sin(theta)**.45*math.sin(ph),cz+(rz-shrink)*math.cos(theta)))
   start=layer*(1+rings*n)
   for j in range(n):faces.append((start,start+1+(j+1)%n,start+1+j) if layer else (start,start+1+j,start+1+(j+1)%n))
   for k in range(rings-1):
    for j in range(n):
     a=start+1+k*n+j;b=start+1+k*n+(j+1)%n;c=b+n;d=a+n;faces.append((d,c,b,a) if layer else (a,b,c,d))
  offset=1+rings*n
  for j in range(n):a=1+(rings-1)*n+j;b=1+(rings-1)*n+(j+1)%n;faces.append((a,b,b+offset,a+offset))
  return mesh('Continuous scalp cap',verts,faces)
 def source(name,length=1.,wavy=False,swept=False,spiky=False):
  data=_library()[name];is_female=name in ['Hair_Long','Hair_Buns','Hair_BuzzedFemale']
  ref_top=1.766643524 if is_female else 1.810076833
  ref_ear=ref_top-.125;verts=[]
  for row in data['vertices']:
   p=Vector(row);x=cx+p.x*sx;y=cy+(p.y-.014)*sy;z=top+(p.z-ref_top)*s
   if name=='Hair_Long' and p.z>ref_ear:
    crown=max(0,min(1,(p.z-ref_ear)/.12));z+=.008*s*crown;x=cx+(x-cx)*(1+.025*crown);y=cy+(y-cy)*(1+.025*crown)
   if p.z<ref_ear:z=top+(ref_ear-ref_top)*s+(p.z-ref_ear)*s*length
   if wavy and p.z<ref_ear:
    t=(ref_ear-p.z)*length;x+=.008*s*math.sin(t*37+abs(p.x)*22);y+=.006*s*math.sin(t*31+p.x*17)
   if swept:
    f=max(0,min(1,(p.z-(ref_top-.07))/.10));z+=.021*s*f;y+=.008*s*f
   if spiky:
    f=max(0,min(1,(p.z-(ref_top-.09))/.12));z+=.012*s*f*(.3+.7*math.sin(p.x*71+p.y*53)**2)
   verts.append((x,y,z))
  return mesh('Quaternius '+name.removeprefix('Hair_'),verts,data['faces'])
 def fringe(straight=False,part=False,short=False):
  count=7 if straight else (4 if part else 5)
  for i in range(count):
   xx=(-.072+i*.144/(count-1))*sx
   shift=.028*sx if part else .006*sx*math.sin(i*2.1)
   low=top-(.075 if straight else .065+.010*((i+1)%3))*s
   curve=.021*s*(xx/(.078*sx))**2
   pts=[(cx+xx-shift,cy-.042*sy,top+.020*s-curve),(cx+xx-shift*.4,cy-.078*sy,top-.031*s-curve*.45),(cx+xx,cy-.092*sy,low+.020*s),(cx+xx+shift*.22,cy-.092*sy,low)]
   radii=[(.018*s,.006*s),(.022*s,.007*s),(.020*s,.006*s),(.007*s,.003*s)]
   tube('Soft fringe lock',pts,radii,material,12)
 def side_locks(length=.18):
  for side in [-1,1]:
   pts=[(cx+side*.080*sx,cy-.035*sy,top-.065*s),(cx+side*.091*sx,cy-.044*sy,top-.145*s),(cx+side*.092*sx,cy-.018*sy,top-(.10+length)*s)]
   tube('Temple lock',pts,[(.021*s,.012*s),(.019*s,.012*s),(.007*s,.006*s)])
 def braid(side=False,twin=False):
  sides=[-1,1] if twin else [-1 if side else 0]
  for sign in sides:
   pts=[];count=55
   for i in range(count):
    t=i/(count-1)
    x=cx+sign*(.075+.023*t)*sx
    y=cy+(.071-.145*t if sign else .115+.012*math.sin(t*math.pi))*sy
    z=top-(.18+.37*t)*s;pts.append(Vector((x,y,z)))
   for strand in range(3):
    arr=[];rr=[]
    for i,p in enumerate(pts):
     t=i/(count-1);angle=t*math.tau*6+strand*math.tau/3;rad=.011*s*(1-.28*t)
     arr.append(p+Vector((rad*math.cos(angle),rad*math.sin(angle),.003*s*math.sin(angle))))
     rr.append(.010*s*(1-.48*t))
    tube('Woven braid strand',arr,rr,material,8)
   p=pts[-1];tie=material_factory('Braid tie',features.get('hairtieColor',features.get('bowColor','#AD8461')),.8)
   ellipsoid('Braid tie',p,(.014*s,.014*s,.008*s),tie,16,8)
   tube('Braid soft tail',[p,p+Vector((sign*.003,-.002,-.035*s))],[.012*s,.003*s])
 def ponytail():
  high=('high' in detail or 'half-up' in detail);small=('small' in detail or 'short' in detail or 'half-up' in detail);curly='curl' in detail
  sign=-1 if 'side' in detail else 0
  root=Vector((cx+sign*.045*sx,cy+.087*sy,top-(.085 if high else .175)*s))
  length=.17 if small else (.30 if curly else .29)
  pts=[];radii=[]
  for i in range(17):
   t=i/16;pts.append(root+Vector((sign*.088*sx*math.sin(t*math.pi/2),(.07*math.sin(t*math.pi)-.008*t)*sy,(-length*t+.025*math.sin(t*math.pi))*s)))
   radii.append((.034*s*(1-.72*t)+.004*s*math.sin(t*13),.027*s*(1-.75*t)))
  tube('Gathered ponytail',pts,radii,material,16)
  if curly:
   volume=[];sizes=[]
   for i in range(29):
    t=i/28;volume.append(root+Vector((sign*.12*sx*math.sin(t*math.pi/2),(.04+.018*math.sin(t*math.tau*2))*sy,-length*t*s)));sizes.append(((.048+.007*math.sin(t*math.tau*5))*s*(1-.48*t),(.040+.006*math.cos(t*math.tau*4))*s*(1-.55*t)))
   tube('Curly ponytail volume',volume,sizes,material,16)
  tie=material_factory('Ponytail tie',features.get('hairtieColor','#725738'),.55)
  ellipsoid('Ponytail tie',root,(.030*s,.025*s,.014*s),tie,20,10)
  # Surface strands give a natural silhouette without a segmented ball-chain.
  if curly:
   for n in range(9):
    arr=[]
    for i in range(25):
     t=i/24;angle=t*math.tau*(2.2+n*.13)+n*math.tau/9
     arr.append(root+Vector(((sign*.12*math.sin(t*math.pi/2)+(.045+.009*math.sin(t*17+n))*math.cos(angle))*sx,(.04+.047*math.sin(angle))*sy,(-length*t+.017*math.cos(angle))*s)))
    tube('Ponytail curl',arr,[.012*s*(1-.65*i/24) for i in range(25)],accent if n%4==0 else material,8)
 def curls(voluminous=False):
  # Small solid S curls distributed over crown/sides, no spikes near the face.
  n=36 if voluminous else 26
  for i in range(n):
   ph=i*2.39996323;theta=.22+(i/(n-1))*1.40
   if math.sin(ph)<-.5 and theta>1.15:theta=1.06
   base=Vector((cx+(.120 if voluminous else .105)*sx*math.sin(theta)*math.cos(ph),cy+(.133 if voluminous else .118)*sy*math.sin(theta)*math.sin(ph),top-.132*s+(.168 if voluminous else .152)*s*math.cos(theta)))
   radial=Vector((math.cos(ph),math.sin(ph),.45)).normalized();tangent=Vector((-math.sin(ph),math.cos(ph),0))
   r=(.022 if voluminous else .012)*s
   arr=[base+radial*(r*.65*math.cos(j*math.tau/16))+tangent*(r*math.sin(j*math.tau/16))+Vector((0,0,.004*s*j/16)) for j in range(17)]
   tube('Soft sculpted curl',arr,.008*s if voluminous else .0065*s,accent if i%7==0 else material,8)
 scalp()
 if style in ('short','sidepart','swept','spiky'):
  source('Hair_SimpleParted',swept=style=='swept',spiky=style=='spiky')
  # Mature parted crown already contains its own soft fringe; a duplicate
  # row of tubes would make a rigid horizontal hairline.
 elif style=='curly':
  source('Hair_BuzzedFemale' if top<1.80 else 'Hair_Buzzed');curls(voluminous='voluminous' in detail)
 elif style=='bob':
  source('Hair_Long',length=.97,wavy='wave' in detail);fringe(straight='straight' in detail or 'pale lavender' in detail)
  for side in [-1,1]:ellipsoid('Rounded bob side curtain',(cx+side*.092*sx,cy+.014*sy,top-.161*s),(.030*sx,.068*sy,.101*s),material,20,16)
 elif style=='long':
  # The musician's medium long hair remains at shoulder level. Partners and
  # explicit long waves reach the mid-back; this is geometry, not a recolour.
  medium='shoulder-length' in detail or ('中长' in ''.join(features.get('distinctive',[])))
  length=1.4 if medium else 2.9
  source('Hair_Long',length=length,wavy='wave' in detail or 'curl' in detail)
  side_locks(.23 if medium else .38)
  fringe(straight='straight fringe' in detail,part='side-part' in detail)
  if 'curl' in detail:
   for side in [-1,1]:
    for k in range(3):
     pts=[]
     for i in range(36):
      t=i/35;theta=t*math.tau*2+k*.7
      pts.append((cx+side*(.090+.012*math.sin(theta))*sx,cy+(.03+k*.025+.012*math.cos(theta))*sy,top-(.11+.43*t)*s))
     tube('Long soft curl',pts,[.012*s*(1-.7*i/35) for i in range(36)],material,8)
 elif style=='ponytail':
  if 'bob' in detail or 'half-up' in detail:source('Hair_Long',length=.85)
  else:source('Hair_BuzzedFemale');side_locks(.10)
  fringe(part=True);ponytail()
 elif style in ('singlebraid','twinbraid'):
  source('Hair_BuzzedFemale');fringe(part=True);side_locks(.08);braid(side='side' in detail and 'centered' not in detail,twin=style=='twinbraid')
 elif style=='twin-buns':
  source('Hair_Buns');fringe(straight=False)
 elif style=='bun':
  source('Hair_BuzzedFemale');fringe(part=True)
  center=(cx,cy+.104*sy,top-(.195 if 'low' in detail else .09)*s)
  ellipsoid('Gathered low bun' if 'low' in detail else 'Gathered bun',center,(.050*s,.041*s,.038*s))
  for j in range(4):
   pts=[]
   for i in range(25):
    ph=i*math.tau/24;pts.append((center[0]+(.041-j*.005)*s*math.cos(ph),center[1]+.032*s*math.sin(ph),center[2]+(j-1.5)*.008*s))
   tube('Bun swept strand',pts,.003*s,accent,6)
 else:source('Hair_SimpleParted');fringe()
 # White/lavender tips are actual material regions on the existing continuous
 # mesh. They retain the exact silhouette and are not extra bead accessories.
 if features.get('hairTipColor'):
  tip=material_factory('Hair tips',features['hairTipColor'],.78)
  threshold=top-.205*s
  for ob in output:
   ob.data.materials.append(tip);idx=len(ob.data.materials)-1
   for poly in ob.data.polygons:
    if sum(ob.data.vertices[i].co.z for i in poly.vertices)/len(poly.vertices)<threshold:poly.material_index=idx
 return output

def create_facial_hair(rig,features,head_bounds,material_factory,bind_fn):
 """Optional, separate helper: source beard or a solid two-sided moustache."""
 acc=features.get('accessories',[])
 if not any(x in acc for x in ['beard','moustache']):return []
 color=features.get('facialHairColor',features.get('hairColor','#33251F'));mat=material_factory('Facial hair',color,.85)
 top=head_bounds['max'][2];sx=(head_bounds['max'][0]-head_bounds['min'][0])/.25;out=[]
 if 'beard' in acc:
  data=_library()['Hair_Beard'];verts=[(v[0]*sx,v[1],top+(v[2]-1.810076833)) for v in data['vertices']]
  me=bpy.data.meshes.new('Source beard mesh');me.from_pydata(verts,[],data['faces']);me.materials.append(mat);ob=bpy.data.objects.new('Quaternius full beard',me);bpy.context.collection.objects.link(ob);bind_fn(ob,'Head');out.append(ob)
 else:
  for side in [-1,1]:
   bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=(side*.020*sx,-.094,top-.173));ob=bpy.context.object;ob.name='Curved moustache';ob.scale=(.025*sx,.008,.005);ob.rotation_euler[1]=side*-.18;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);ob.data.materials.append(mat);bind_fn(ob,'Head');out.append(ob)
 for ob in out:
  for p in ob.data.polygons:p.use_smooth=True
 return out
