import bpy,sys,json,math,hashlib,os
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent));import model_helpers as h
R=Path(__file__).resolve().parent.parent;S=R.parent/'residential-3d-v1'
h.init();box,cyl,leaf=h.box,h.cyl,h.leaf
PLAN=json.loads((S/'housing-capacity.json').read_text());OFF={'A':0,'C':165.625}
DROOT={};PROTOTYPES={};SOURCES={};BUILDINGS=[]
for zone in ['A','C']:
 root=bpy.data.objects.new(zone+'_District',None);h.col(zone+'_Buildings').objects.link(root);DROOT[zone]=root
# Merge objects only inside their original named layer; preserve every face/material.
# Linked copies share geometry. Original single-building source files remain untouched.
for key in ['courtyard','hero','apartment-3','apartment-4','apartment-5']:
 f=S/key/(key+'.blend');before=hashlib.sha256(f.read_bytes()).hexdigest()
 with bpy.data.libraries.load(str(f),link=False) as (src,dst):
  names=[n for n in src.collections if n!='Studio'];dst.collections=list(names)
 cols=list(dst.collections);parts=[];source_tri=0;merged_tri=0;allcoords=[]
 for name,c in zip(names,cols):
  vs=[];faces=[];mi=[];mats=[]
  for o in c.objects:
   if o.type!='MESH':continue
   offset=len(vs);transform=o.matrix_basis
   vs.extend([tuple(transform@v.co) for v in o.data.vertices])
   for poly in o.data.polygons:
    mat=o.data.materials[poly.material_index]
    if mat not in mats:mats.append(mat)
    faces.append(tuple(offset+i for i in poly.vertices));mi.append(mats.index(mat))
   o.data.calc_loop_triangles();source_tri+=len(o.data.loop_triangles)
  if not vs:continue
  mesh=bpy.data.meshes.new(key+'_'+name);mesh.from_pydata(vs,[],faces)
  for mat in mats:mesh.materials.append(mat)
  mesh.polygons.foreach_set('material_index',mi);mesh.update();mesh.calc_loop_triangles();merged_tri+=len(mesh.loop_triangles)
  allcoords.extend(vs);parts.append((name,mesh))
 assert merged_tri==source_tri,(key,merged_tri,source_tri)
 for c in cols:
  for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(c)
 meta=json.loads((S/key/'manifest.json').read_text());bounds=[max(p[i] for p in allcoords)-min(p[i] for p in allcoords) for i in range(3)]
 assert all(abs(bounds[i]-meta['bounds'][i])<.001 for i in range(3)),(key,bounds,meta['bounds'])
 PROTOTYPES[key]=parts;SOURCES[key]={'blendSha256':before,'glbSha256':hashlib.sha256((S/key/(key+'.glb')).read_bytes()).hexdigest(),'sourceTriangles':source_tri,'mergedTriangles':merged_tri,'bounds':bounds,'groups':len(parts)}

def instance(zone,id,key,x,y,floors,units):
 root=bpy.data.objects.new(id,None);h.col(zone+'_Buildings').objects.link(root);root.parent=DROOT[zone];root.location=(OFF[zone]+x,y,0)
 for name,mesh in PROTOTYPES[key]:
  o=bpy.data.objects.new(id+'__'+name,mesh);h.col(zone+'_Buildings').objects.link(o);o.parent=root
 w,d=(24,24) if key=='hero' else (20,18) if key=='courtyard' else (25,17)
 yc=y if not key.startswith('apartment') else y-.2
 b={'id':id,'zone':zone,'model':key,'center':[x,y],'worldCenter':[OFF[zone]+x,y],'rotation':0,'scale':1,'floors':floors,'units':units,'plot':[x-w/2,yc-d/2,x+w/2,yc+d/2]}
 BUILDINGS.append(b)
for v in PLAN['courtyardVillas']:instance('A',v['id'],v['model'],*v['center'],2,1)
instance('A','A07','hero',0,-16,2,1)
for b in PLAN['apartmentBlocks']:
 x=13.625 if b['center'][0]>0 else -13.625
 instance('C',b['id'],b['model'],x,b['center'][1],b['floors'],b['units'])

PATHS={};LAYOUT={}
def site(zone,w,d,rects):
 ox=OFF[zone];plots=[b['plot'] for b in BUILDINGS if b['zone']==zone]
 # Fill only land outside existing private plots; no duplicate lawn faces or filled pool.
 xs=sorted(set([-w/2,w/2]+[v for a in plots for v in [a[0],a[2]]]))
 ys=sorted(set([-d/2,d/2]+[v for a in plots for v in [a[1],a[3]]]))
 for x0,x1 in zip(xs,xs[1:]):
  for y0,y1 in zip(ys,ys[1:]):
   x,y=(x0+x1)/2,(y0+y1)/2
   if any(a<=x<=c and b<=y<=dd for a,b,c,dd in plots):continue
   box(zone+' shared ground',ox+x,y,-.15,x1-x0,y1-y0,.30,'grass',zone+'_Landscape')
 # Union all public road rectangles into disjoint, coplanar strips.
 xs=sorted(set(round(v,5) for a in rects for v in [a[0],a[2]]));ys=sorted(set(round(v,5) for a in rects for v in [a[1],a[3]]));tiles=[]
 for ya,yb in zip(ys,ys[1:]):
  runs=[]
  for xa,xb in zip(xs,xs[1:]):
   x,y=(xa+xb)/2,(ya+yb)/2
   if any(a<=x<=c and b<=y<=d for a,b,c,d in rects):
    if runs and abs(runs[-1][1]-xa)<1e-5:runs[-1]=(runs[-1][0],xb)
    else:runs.append((xa,xb))
  for xa,xb in runs:
   top=.07 if zone=='A' else .055
   box(zone+' shared walk',ox+(xa+xb)/2,(ya+yb)/2,top/2,xb-xa,yb-ya,top,'stone',zone+'_Paths');tiles.append([xa,ya,xb,yb])
 PATHS[zone]=tiles;LAYOUT[zone]={'size':[w,d],'offset':[ox,0],'plots':plots}
# A: 2 m cross lanes between rows, 2 m side spines, a separate central garden loop.
a=[(-14.25,-31.25,-12.25,31.25),(12.25,-31.25,14.25,31.25),(-37.5,9,37.5,11),(-37.5,-11,-12.25,-9),(12.25,-11,37.5,-9),(-37.5,-31.25,37.5,-29),(-37.5,29,37.5,31.25),(-2.85,-29,-1.15,-28),(-1,-3,1,9),(-1,11,1,29),(-12.25,-3,12.25,-1),(-12.25,25,12.25,27)]
site('A',75,62.5,a)
# C: 2.25 m spine; transverse lanes join every south-facing entry.
c=[(-1.125,-31.25,1.125,31.25),(-26.875,9,26.875,11),(-26.875,-11,1.125,-9),(-26.875,-31.25,26.875,-29),(-26.875,29,26.875,31.25),(1.125,-1.1,26.875,1.1)]
for b in BUILDINGS:
 if b['zone']!='C':continue
 x,y=b['center'];start=y-8.1;end=11 if y==20 else -9 if y==0 else -29
 c.append((x-1.1,end,x+1.1,start))
site('C',53.75,62.5,c)

def tree(zone,x,y,s=1):
 x+=OFF[zone];c=zone+'_Landscape';cyl('Shared tree trunk',x,y,1.1*s,.12*s,2.2*s,'wood',c)
 for dx,dy,dz in [(0,0,2.3),(.5,0,2),(-.5,.25,2.15),(0,-.5,2)]:leaf('Shared tree crown',x+dx*s,y+dy*s,dz*s,(.85*s,.8*s,.85*s),'leaf' if dx else 'leafLight',c)
def flower(zone,cx,cy,i):
 c=zone+'_Landscape';cx+=OFF[zone]
 for j in range(4):
  a=j*2.4+i;x,y=cx+.28*math.cos(a),cy+.28*math.sin(a);z=.40+.08*(i%3)
  cyl('Shared flower stem',x,y,z/2,.013,z,'leaf',c)
  for k in range(5):
   a=k*math.tau/5;leaf('Shared flower petal',x+.085*math.cos(a),y+.085*math.sin(a),z,(.09,.085,.05),['white','flowerPink','flowerYellow','lavender'][i%4],c)
def bench(zone,x,y,w=2.8):
 x+=OFF[zone];c=zone+'_Furniture'
 box('Shared bench seat',x,y,.54,w,.65,.12,'wood',c);box('Shared bench back',x,y+.3,.9,w,.08,.65,'sage',c)
 for dx in [-w*.35,w*.35]:box('Shared bench support',x+dx,y,.27,.10,.50,.48,'darkgreen',c)
def pergola(zone,x,y):
 x+=OFF[zone];c=zone+'_Furniture';box('Shared pergola deck',x,y,.07,6,5,.14,'lightwood',c)
 for dx in [-2.7,2.7]:
  for dy in [-2.2,2.2]:box('Shared pergola post',x+dx,y+dy,1.55,.12,.12,3.0,'wood',c)
 for i in range(10):box('Shared pergola lath',x-2.9+i*.645,y,3.1,.075,5.2,.09,'wood',c)
 cyl('Shared picnic tabletop',x,y,.94,.9,.12,'lightwood',c);cyl('Shared table base',x,y,.49,.13,.8,'wood',c)
 for dx in [-1.6,1.6]:box('Shared garden seat',x+dx,y,.48,.5,1.5,.65,'sage',c)
# A central green is deliberately distributed on both sides of the middle path.
pergola('A',-6,19);bench('A',6,23);bench('A',6,16)
for x,y,s in [(-9.5,27.8,.7),(9.3,27.6,.75),(-9,13,1),(9.3,13,1),(-7,5,1.25),(7,5,1.1),(-7,-.1,.8),(7,-.1,.8)]:tree('A',x,y,s)
for i,(x,y) in enumerate([(-10,22),(-10,16),(3,21),(9.5,19),(-9,1),(8,1),(3,12),(-3,12)]):flower('A',x,y,i)
# C east centre remains a shared courtyard, with the through path kept clear.
pergola('C',13.6,4.6);bench('C',8,-4.5);bench('C',17,-4.5)
for x,y,s in [(4.3,5.4,1),(23,5.5,1.1),(4.5,-6.1,.9),(23,-6.1,1),(19.8,-5.7,.65)]:tree('C',x,y,s)
for i,(x,y) in enumerate([(5.7,2.8),(22,2.7),(6.3,-5.4),(12,-6.5),(23,-3.5)]):flower('C',x,y,i)
# Discrete building IDs at each gateway, facing south and outside clear entry strips.
for b in BUILDINGS:
 x,y=b['worldCenter'];key=b['model'];c=b['zone']+'_Signs'
 gatex=x-2 if key=='hero' else x;gatey=y-(12 if key=='hero' else 9 if key=='courtyard' else 8.1)
 # mounted beside entry rather than across the walkway
 sx=gatex+1.55
 box('Address post '+b['id'],sx,gatey+.55,.51,.08,.08,1.02,'wood',c)
 h.sign(b['id'],sx,gatey+.55,1.13,.66,c)
 b['entry']=[gatex-OFF[b['zone']],gatey];b['group']=b['id'];b['sourceHash']=SOURCES[key]['blendSha256']
# Explicit context preserves the A/B/C distances from the masterplan.
box('B reserved plot',87.5,0,-.19,85,62.5,.24,'stone','Context')
o=h.text('B reserved label','B  公共服务区\n本轮保留',87.5,0,-.062,3.3,'darkgreen','Context');o.rotation_euler=(0,0,0)
for y in [-38.75,36.25]:box('Town shared road',77.5,y,-.02,240,5.25,.10,'stone','Context')
for x,w in [(41.25,6),(134.375,6.5)]:box('Town north south connector',x,-1.25,-.02,w,72.75,.10,'stone','Context')
for zone in ['A','C']:
 ox=OFF[zone]
 box('District south connector '+zone,ox,-33.5,.015,2.25,4.5,.03,'stone','Context')
 box('District north connector '+zone,ox,32.4375,.015,2.25,2.375,.03,'stone','Context')
 # District A central north garden path meets this road; C spine does too.
 o=h.text(zone+' district label',zone+' 区',ox,-43,.03,2.3,'darkgreen','Context');o.rotation_euler=(0,0,0)
# Parent all district scene additions; preserve root building transforms.
for n,c in list(h.C.items()):
 if not (n.startswith('A_') or n.startswith('C_')) or n.endswith('_Buildings'):continue
 root=bpy.data.objects.new(n,None);c.objects.link(root);root.parent=DROOT[n[0]]
 for o in list(c.objects):
  if o!=root:o.parent=root
# Context group for toggling in focused previews.
c=h.C['Context'];cr=bpy.data.objects.new('Context',None);c.objects.link(cr)
for o in list(c.objects):
 if o!=cr:o.parent=cr
bpy.context.view_layer.update()
# All plots remain contained and disjoint; count and source hashes match the intended plan.
for zone,(w,d) in [('A',(75,62.5)),('C',(53.75,62.5))]:
 bs=[b for b in BUILDINGS if b['zone']==zone]
 for b in bs:
  x0,y0,x1,y1=b['plot'];assert x0>=-w/2 and x1<=w/2 and y0>=-d/2 and y1<=d/2
 for i,b in enumerate(bs):
  for k in bs[i+1:]:
   a,c=b['plot'],k['plot'];assert min(a[2],c[2])-max(a[0],c[0])<=0 or min(a[3],c[3])-max(a[1],c[1])<=0
assert sum(b['units'] for b in BUILDINGS)==47
for key,v in SOURCES.items():assert hashlib.sha256((S/key/(key+'.blend')).read_bytes()).hexdigest()==v['blendSha256']
scene=bpy.context.scene;scene.name='01 A garden neighbourhood';scene.unit_settings.system='METRIC'
bpy.ops.object.select_all(action='SELECT');asset=R/'AC-residential-districts.glb';bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
meshes=[o for o in bpy.data.objects if o.type=='MESH'];tri=0
for o in meshes:o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
meta={'title':'A + C 住宅区实景落位','date':'2026-10-13','sources':SOURCES,'buildings':BUILDINGS,'districts':LAYOUT,'paths':PATHS,'residentUnits':46,'heroUnits':1,'totalBuildings':12,'meshObjects':len(meshes),'triangles':tri,'sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'units':'metres','sourceAxes':'Z up, north +Y','glbAxes':'Y up, north -Z','status':'design-review','AtoCOffset':165.625,'changesToPriorPlacement':'C columns moved from +/-13 to +/-13.625 metres; source models unscaled and unrotated'}
(R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
# Studio outside export. Scene exclusions leave the other district out of close-up renders.
h.studio(scene);bpy.data.objects['Studio ground'].location.z=-1.5;bpy.data.objects['Studio ground'].scale=(3,3,1);scene.cycles.samples=20;scene.render.resolution_x=1600;scene.render.resolution_y=1200
views=[]
for idx,(name,zone,loc,target,scale,file) in enumerate([
 ('01 A garden neighbourhood','A',(78,-90,83),(0,0,1),99,'A-overview.png'),
 ('02 C riverside neighbourhood','C',(OFF['C']+69,-85,72),(OFF['C'],0,5),88,'C-overview.png'),
 ('03 A plan','A',(0,-.001,110),(0,0,0),86,'A-plan.png'),
 ('04 C plan','C',(OFF['C'],-.001,110),(OFF['C'],0,0),90,'C-plan.png'),
 ('05 Town placement','all',(154,-232,246),(77.5,0,0),255,'AC-placement.png')]):
 sc=scene if idx==0 else scene.copy();sc.name=name;sc.use_fake_user=True
 for child in sc.view_layers[0].layer_collection.children:
  n=child.name
  if n=='Studio':continue
  child.exclude=(zone!='all' and (n=='Context' or n.startswith(('C_' if zone=='A' else 'A_'))))
 sc.camera=h.camera(name+' camera',loc,target,scale);views.append((sc,file))
bpy.context.window.scene=scene
for scr in bpy.data.screens:
 for ar in scr.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.overlay.show_overlays=False;ar.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'AC-residential-districts.blend'))
for sc,file in views:
 if os.environ.get('AC_SKIP_RENDERS'):continue
 sc.render.filepath=str(R/file);bpy.ops.render.render(write_still=True,scene=sc.name);print('RENDERED',file,flush=True)
print('COMPLETE',len(meshes),tri,flush=True)
