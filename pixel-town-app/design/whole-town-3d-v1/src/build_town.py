import bpy,sys,json,math,hashlib,os,bmesh
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).parent));import model_helpers as h
R=Path(__file__).resolve().parent.parent;BASE=R.parent
h.PALETTE.update({'path':'ddd6c3','road':'bbb9ac','sand':'ded3b7','meadow':'acc18c','river':'85b8bf'})
h.init();box,cyl,leaf=h.box,h.cyl,h.leaf
PLAN=json.loads((R/'reference/masterplan.json').read_text());ZONES={}
for z in PLAN['zones']:
 x,y,w,d=z['rect'];ZONES[z['id']]={'id':z['id'],'name':z['name'],'center':[(x+w/2-620)/4,(540-y-d/2)/4],'size':[w/4,d/4]}
SPECS=[('AC','residential-districts','AC-residential-districts'),('B','public-services-district','B-public-services'),('D','craft-workshops','D-craft-workshops'),('E','town-square','E-town-square'),('F','river-park','F-river-park'),('G','garden-greenhouse','G-garden-greenhouse'),('H','daily-shops','H-daily-shops'),('I','arrival-guard','I-arrival-guard')]
SOURCES={};PARTS=[];SOURCE_STATS={};REMOVED=[]
def merge(name,objects,collection,shift=(0,0,0)):
 vs=[];fs=[];mis=[];mats=[];uv=[];smooth=[];hasuv=False;tri=0;dep=bpy.context.evaluated_depsgraph_get()
 for o in objects:
  me=o.data;ev=None
  if o.modifiers:ev=o.evaluated_get(dep);me=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dep)
  off=len(vs);mat=Matrix.Translation(Vector(shift))@o.matrix_world
  vs.extend(tuple(mat@v.co) for v in me.vertices);me.calc_loop_triangles();tri+=len(me.loop_triangles)
  remap=[]
  for material in me.materials:
   if material not in mats:mats.append(material)
   remap.append(mats.index(material))
  layer=me.uv_layers.active
  if layer:hasuv=True
  for p in me.polygons:
   fs.append(tuple(off+i for i in p.vertices));mis.append(remap[p.material_index] if remap else 0);smooth.append(p.use_smooth)
   uv.extend(tuple(layer.data[i].uv) if layer else (0,0) for i in p.loop_indices)
  if ev:ev.to_mesh_clear()
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs)
 for mat in mats:me.materials.append(mat)
 if fs:me.polygons.foreach_set('material_index',mis);me.polygons.foreach_set('use_smooth',smooth)
 if hasuv:
  layer=me.uv_layers.new(name='UVMap');layer.data.foreach_set('uv',[v for p in uv for v in p])
 me.update();me.calc_loop_triangles();assert len(me.loop_triangles)==tri,(name,tri,len(me.loop_triangles))
 o=bpy.data.objects.new(name,me);h.col(collection).objects.link(o)
 PARTS.append({'name':name,'zone':collection if len(collection)==1 else 'T','sourceObjects':len(objects),'triangles':tri,'textured':hasuv})
 return o
for key,folder,stem in SPECS:
 path=BASE/(folder+'-3d-v1');f=path/(stem+'.blend');meta=json.loads((path/'manifest.json').read_text());(R/'reference'/(key+'-manifest.json')).write_text(json.dumps(meta,ensure_ascii=False,indent=2))
 SOURCES[key]={'folder':folder+'-3d-v1','blend':f.name,'blendSha256':hashlib.sha256(f.read_bytes()).hexdigest(),'glbSha256':hashlib.sha256((path/(stem+'.glb')).read_bytes()).hexdigest(),'metaMeshObjects':meta['meshObjects'],'metaTriangles':meta['triangles']}
 with bpy.data.libraries.load(str(f),link=False) as (src,dst):
  names=[n for n in src.collections if n!='Studio' and (key!='AC' or n.startswith(('A_','C_')))];dst.collections=names.copy()
 cols=list(dst.collections)
 for c in cols:bpy.context.scene.collection.children.link(c)
 bpy.context.view_layer.update();groups={};originals=set()
 for old,c in zip(names,cols):
  for o in c.objects:
   if o.type!='MESH' or o in originals:continue
   originals.add(o)
   if key=='F' and o.name.startswith(('West terrain edge','Core terrain edge','Bridge approach terrain edge','Terrain cut edge','Far terrain edge')):REMOVED.append({'zone':'F','object':o.name,'reason':'Standalone terrain cut cap removed at assembly seam'});continue
   if key=='AC':zone=old[0];part=o.name if old.endswith('_Buildings') else old[2:]
   else:zone=key;part=old
   groups.setdefault((zone,part),[]).append(o)
 # Capture resolved source matrices before detaching or deleting any linked hierarchy.
 for (zone,part),objects in groups.items():
  shift=tuple(ZONES['A']['center'])+(0,) if key=='AC' else tuple(ZONES[zone]['center'])+(0,)
  merge(zone+'__'+part,objects,zone,shift)
  SOURCE_STATS.setdefault(zone,{'sourceObjects':0,'triangles':0,'parts':0});v=SOURCE_STATS[zone];v['sourceObjects']+=len(objects);v['triangles']+=PARTS[-1]['triangles'];v['parts']+=1
 # Delete source objects only after all their transforms and meshes were copied.
 for o in originals:bpy.data.objects.remove(o,do_unlink=True)
 for c in cols:
  for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(c)
 print('ASSEMBLED',key,flush=True)
# Continuous terrain around the nine retained district plots. No plane covers private gardens or pools.
def mesh(n,vs,fs,mat,c):
 me=bpy.data.meshes.new(n);me.from_pydata(vs,[],fs);me.materials.append(h.M[mat]);me.update();o=bpy.data.objects.new(n,me);h.col(c).objects.link(o);return o
rects=[]
for z in ZONES.values():
 x,y=z['center'];w,d=z['size'];rects.append([x-w/2,y-d/2,x+w/2,y+d/2])
xs=sorted(set([-135,105]+[v for r in rects for v in [r[0],r[2]]]+[99.625]));ys=sorted(set([-110,115,-40,40]+[v for r in rects for v in [r[1],r[3]]]))
for xa,xb in zip(xs,xs[1:]):
 for ya,yb in zip(ys,ys[1:]):
  x,y=(xa+xb)/2,(ya+yb)/2
  if any(a<x<c and b<y<d for a,b,c,d in rects) or (-40<y<40 and x>99.625):continue
  box('Interdistrict meadow',x,y,-.20,xb-xa,yb-ya,.4,'grass','T_Land')
# Preserve F's existing river and extend its shoreline continuously to the north and south.
def shore(y):
 return 78.125+(32.5+6.5*(y/40)**2 if abs(y)<=40 else 39+11.375*math.sin((abs(y)-40)/35))
def strip(n,pts,width,z,mat,c):
 vs=[]
 for i,(x,y) in enumerate(pts):
  d=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(0,i-1)]);d.normalize();nx,ny=-d.y*width/2,d.x*width/2;vs.extend([(x+nx,y+ny,z),(x-nx,y-ny,z)])
 return mesh(n,vs,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(pts)-1)],mat,c)
for lo,hi in [(-110,-40),(40,115)]:
 Y=[lo+i*.5 for i in range(int((hi-lo)*2)+1)]
 for ya,yb in zip(Y,Y[1:]):
  a,b=shore(ya),shore(yb)
  mesh('River extension',[(a+.8,ya,-.75),(a+20,ya,-.75),(b+20,yb,-.75),(b+.8,yb,-.75)],[(0,1,2,3)],'river','T_River')
  mesh('Town west bank',[(a,ya,0),(a+.8,ya,-.8),(b+.8,yb,-.8),(b,yb,0)],[(0,1,2,3)],'sand','T_Riverbank')
  mesh('Town east bank',[(a+20,ya,-.8),(a+21.4,ya,.08),(b+21.4,yb,.08),(b+20,yb,-.8)],[(0,1,2,3)],'sand','T_Riverbank')
  mesh('Riverside meadow',[(105,ya,0),(a,ya,0),(b,yb,0),(105,yb,0)],[(0,1,2,3)],'grass','T_Land')
  mesh('Far meadow',[(a+21.4,ya,.08),(165,ya,.08),(165,yb,.08),(b+21.4,yb,.08)],[(0,1,2,3)],'meadow','T_Land')
 strip('Extended riverside walk',[(shore(y)-3,y) for y in Y],2.4,.10,'path','T_Riverside_Paths')
 # Match the original far trail at both seams; widen gently into the new landscape.
 endpoint=78.125+66+.8*math.sin((lo if lo==40 else hi)/12)
 pts=[(endpoint+(155-endpoint)*(1-math.exp(-abs(abs(y)-40)/28)),y) for y in Y]
 strip('Extended far nature trail',pts,1.8,.13,'sand','T_Riverside_Paths')
box('Central far meadow',157.5625,0,-.16,14.875,80,.48,'meadow','T_Land')
# Base remains below the river surface and existing lowest garden geometry.
box('Town solid base',15,2.5,-1.2,300,225,.5,'earth','T_Base')
# Public connector network outside districts, with short level transitions at each portal.
ROAD=[];CONNECTIONS=[];PORTALS=[]
def rectpath(x0,y0,x1,y1):ROAD.append([min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1)])
# Walkable avenue network. Vehicle access stays west/south/north; eastern park remains a promenade.
for x in [-46.25,46.875]:rectpath(x-2,-106,x+2,110)
for y in [35,-36.25]:rectpath(-130,y-2.25,102.5,y+2.25)
rectpath(-132.5,-106,-127.5,110);rectpath(-130,107.5,105,112.5);rectpath(-130,-108.5,105,-103.5)
# Arrival east vehicle lane joins the southern town road at its original width.
rectpath(96.625,-106,105,-100)
# A/C portals are inferred directly from their already-built path edges.
PORTDEF={'A':{'south':([0,-31.25],2.25,.07),'north':([0,31.25],2,.07),'east':([37.5,10],2,.07),'west':([-37.5,10],2,.07)},'C':{'south':([0,-31.25],2.25,.055),'north':([0,31.25],2.25,.055),'west':([-26.875,10],2,.055),'east':([26.875,0],2.2,.055)}}
for key,folder,stem in SPECS:
 if key=='AC':continue
 m=json.loads((R/'reference'/(key+'-manifest.json')).read_text());pd=m.get('portals',m.get('pedestrianPortals',{}));top={'B':.09,'D':.09,'E':.09,'F':.10,'G':.10,'H':.09,'I':.13}[key];PORTDEF[key]={n:(p,2 if key=='B' and n.startswith('north') else 2.4,top) for n,p in pd.items()}
# Height transition strips end exactly at source paving; main rectangle union ends at opposite ramp edge.
for zid,defs in PORTDEF.items():
 z=ZONES[zid];cx,cy=z['center'];w,d=z['size']
 for name,(p,width,top) in defs.items():
  x,y=cx+p[0],cy+p[1]
  if abs(p[0]-w/2)<.01:direction=(1,0);target=(-46.25 if zid in 'ADG' else 108 if zid in 'CFI' else 46.875,y)
  elif abs(p[0]+w/2)<.01:direction=(-1,0);target=(-130 if zid in 'ADG' else -46.25 if zid in 'BEH' else 46.875,y)
  elif abs(p[1]-d/2)<.01:direction=(0,1);target=(x,110 if zid in 'ABC' else 35 if zid in 'DEF' else -36.25)
  else:direction=(0,-1);target=(x,35 if zid in 'ABC' else -36.25 if zid in 'DEF' else -106)
  # Eastern C path meets the curving promenade; F north/south connect to bridge avenues.
  if zid=='C' and direction==(1,0):target=(shore(y)-3,y)
  dx,dy=direction;a=(x+dx,y+dy);tx,ty=target
  vs=[(x-dy*width/2,y+dx*width/2,top),(x+dy*width/2,y-dx*width/2,top),(a[0]+dy*width/2,a[1]-dx*width/2,.09),(a[0]-dy*width/2,a[1]+dx*width/2,.09)]
  mesh(zid+' '+name+' transition',vs,[(0,1,2,3)],'path','T_Transitions')
  if dx:rectpath(min(a[0],tx),y-width/2,max(a[0],tx),y+width/2)
  else:rectpath(x-width/2,min(a[1],ty),x+width/2,max(a[1],ty))
  PORTALS.append({'zone':zid,'name':name,'point':[x,y,top],'width':width,'target':[tx,ty,.09]})
# Bridge approaches rise from town paving to existing 0.28m bridge decks at x=102.5.
for y in [35,-36.25]:
 # Last 2m of the horizontal avenue is the rise; trim union to avoid an overlapping flat face.
 for r in ROAD:
  if r[0]==-130 and abs((r[1]+r[3])/2-y)<.01:r[2]=100.5
 mesh('Bridge approach ramp',[(100.5,y-2.25,.09),(102.5,y-2.25,.28),(102.5,y+2.25,.28),(100.5,y+2.25,.09)],[(0,1,2,3)],'lightwood','T_Transitions')
# Both longitudinal bank paths rise to the existing bridge deck at each crossing.
for by in [35,-36.25]:
 for bank in ['west','far']:
  top=.10 if bank=='west' else .13;width=2.4 if bank=='west' else 1.8
  def trailx(y):return shore(y)-3 if bank=='west' else 78.125+66+.8*math.sin(y/12)
  for side in [-1,1]:
   ya=by+side*2.375;yb=ya+side*1.5;xa,xb=trailx(ya),trailx(yb)
   verts=[(xa-width/2,ya,.28),(xa+width/2,ya,.28),(xb+width/2,yb,top),(xb-width/2,yb,top)]
   mesh('Bank path bridge transition',verts,[(0,1,2,3) if side>0 else (3,2,1,0)],'lightwood','T_Transitions')
# Union road rectangles, with no paving inside retained district plots.
xs=sorted({round(r[i],6) for r in ROAD for i in [0,2]});ys=sorted({round(r[i],6) for r in ROAD for i in [1,3]});TILES=[]
for ya,yb in zip(ys,ys[1:]):
 runs=[]
 for xa,xb in zip(xs,xs[1:]):
  x,y=(xa+xb)/2,(ya+yb)/2
  if any(a<x<c and b<y<d for a,b,c,d in ROAD):
   assert not any(a+.001<x<c-.001 and b+.001<y<d-.001 for a,b,c,d in rects),('Road intrudes district',x,y)
   if runs and abs(runs[-1][1]-xa)<1e-5:runs[-1]=(runs[-1][0],xb)
   else:runs.append((xa,xb))
 for xa,xb in runs:box('Town public avenue',(xa+xb)/2,(ya+yb)/2,.045,xb-xa,yb-ya,.09,'path','T_Paths');TILES.append([xa,ya,xb,yb])
# Green breaks along connector avenues, kept outside path footprint and existing zones.
def free(x,y,r=1.8):
 return not any(a-r<x<c+r and b-r<y<d+r for a,b,c,d in rects+ROAD) and x<shore(y)-5 and -130<x<103
for row,y in enumerate([31,-31.5,103.5,-101]):
 for i in range(20):
  x=-121+i*11.1
  if not free(x,y):continue
  cyl('Avenue tree trunk',x,y,1.5,.17,3,'wood','T_Planting')
  for dx,dy,z in [(0,0,3.7),(-.8,.1,3.1),(.7,.2,3.2),(0,-.8,3.0)]:leaf('Avenue tree canopy',x+dx,y+dy,z,(1.2,1.15,1.2),'leafLight' if dx==0 else 'leaf','T_Planting')
  for j in range(3):leaf('Natural underplanting',x+1.3*math.cos(j*2.4),y+1.1*math.sin(j*2.4),.4,(.6,.5,.4),'leafLight','T_Planting')
for y in range(-98,110,13):
 for x in [-134,161]:
  cyl('Outer tree trunk',x,y,1.25,.14,2.5,'wood','T_Planting');leaf('Outer tree crown',x,y,3.1,(1.1,1.05,1.5),'leafLight','T_Planting')
# Natural river extension accents, avoiding the promenade.
for y in list(range(-102,-42,10))+list(range(46,110,10)):
 x=shore(y)+.3;leaf('Bank stone',x,y,-.2,(.55,.7,.4),'stone','T_Planting')
 for j in range(3):leaf('River reed',x+.5+j*.13,y,.25,(.07,.08,.7),'sage','T_Planting')
# Merge new shared groups for a responsive full-town viewer.
for name,c in list(h.C.items()):
 if not name.startswith('T_'):continue
 obs=[o for o in c.objects if o.type=='MESH'];bpy.context.view_layer.update();merge('T__'+name[2:],obs,'T')
 for o in obs:bpy.data.objects.remove(o,do_unlink=True)
 bpy.data.collections.remove(c);del h.C[name]
scene=bpy.context.scene;scene.name='01 Whole town';scene.unit_settings.system='METRIC';bpy.context.view_layer.update()
for im in bpy.data.images:
 if im.has_data and not im.packed_file:im.pack()
# All asset parts are explicit, editable zone collections. No source studios or placeholders exported.
CLEANUP={}
for o in [o for o in scene.objects if o.type=='MESH']:
 o.data.calc_loop_triangles();before=len(o.data.loop_triangles)
 bm=bmesh.new();bm.from_mesh(o.data);bad=[f for f in bm.faces if f.calc_area()<1e-10]
 if bad:
  bmesh.ops.delete(bm,geom=bad,context='FACES_ONLY');bm.to_mesh(o.data);o.data.update();o.data.calc_loop_triangles();CLEANUP[o.name]=before-len(o.data.loop_triangles)
 bm.free()
meshes=[o for o in scene.objects if o.type=='MESH'];tri=0
for o in meshes:o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
asset=R/'Town-complete.glb';bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(asset),export_format='GLB',use_selection=True,export_cameras=False,export_lights=False)
meta={'title':'溪畔日常 · 九区完整小镇','date':'2026-10-15','plot':[300,225],'worldBounds':[-135,-110,165,115],'zones':ZONES,'sources':SOURCES,'sourceStats':SOURCE_STATS,'parts':PARTS,'removed':REMOVED,'degenerateCleanup':CLEANUP,'portals':PORTALS,'roadTiles':TILES,'roadRectangles':ROAD,'meshObjects':len(meshes),'triangles':tri,'sha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'units':'metres','sourceAxes':'Z up; north +Y','glbAxes':'Y up; north -Z','status':'design-review','residentialCapacity':{'residentHomes':46,'heroHome':1,'hotelRooms':6},'assemblyChanges':['Removed AC B reserved placeholder and duplicate road context','Removed standalone F terrain end caps','Extended F river and both bank paths without rescaling district geometry','Connected every declared district portal through town avenues and height transition strips','Vehicles use western/southern/northern access; east park stays pedestrian']}
(R/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
h.studio(scene);scene.cycles.samples=12;scene.render.resolution_x=1800;scene.render.resolution_y=1350;bpy.data.objects['Studio ground'].location.z=-1.6;bpy.data.objects['Studio ground'].dimensions=(1600,1600,.12)
views=[]
for idx,(name,loc,target,scale,file) in enumerate([('01 Whole town',(320,-380,360),(8,0,2),375,'overview.png'),('02 Town plan',(15,-.001,500),(15,2.5,0),320,'plan.png'),('03 From the river',(410,260,300),(10,0,3),365,'riverside-town.png'),('04 Town centre',(160,-195,175),(0,-12,1),205,'town-centre.png')]):
 sc=scene if idx==0 else scene.copy();sc.name=name;sc.use_fake_user=True;sc.camera=h.camera(name+' camera',loc,target,scale);sc.camera.data.clip_end=2000;views.append((sc,file))
bpy.context.window.scene=scene
for scr in bpy.data.screens:
 for ar in scr.areas:
  if ar.type=='VIEW_3D':ar.spaces.active.shading.type='MATERIAL';ar.spaces.active.overlay.show_overlays=False;ar.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Town-complete.blend'))
for sc,file in views:
 if os.getenv('TOWN_SKIP_RENDERS'):continue
 if os.getenv('TOWN_RENDER') and file not in os.getenv('TOWN_RENDER').split(','):continue
 sc.render.filepath=str(R/file);bpy.ops.render.render(write_still=True,scene=sc.name);print('RENDERED',file,flush=True)
print('COMPLETE',len(meshes),tri,flush=True)
