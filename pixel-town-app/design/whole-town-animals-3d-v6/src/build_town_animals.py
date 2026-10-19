"""Assemble the editable V6 town at an exported browser startup snapshot.

Reads Town-complete.blend and reference/runtime-spawn.json; never saves into a
source asset. Output: Town-with-animals.blend and qa/town-native-validation.json.
Run only after the final startup snapshot and navigation props are available.
"""
import bpy,json,math,hashlib,struct,time
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'Town-complete.blend'
SNAPSHOT=ROOT/'reference/runtime-spawn.json'
OUTPUT=ROOT/'Town-with-animals.blend'
REPORT=ROOT/'qa/town-native-validation.json'
NAV_HABITATS={}

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def xyz(p):return Vector((float(p[0]),-float(p[2]),float(p[1])))
def ensure(c,message):
 if not c:raise AssertionError(message)
def collection(name,parent):
 c=bpy.data.collections.new(name);parent.children.link(c);return c
def move(o,col):
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o)
def material(name,color,alpha=1):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,alpha);m.use_nodes=True
 m.node_tree.nodes.clear();p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.85;p.inputs['Alpha'].default_value=alpha
 if alpha<1 and hasattr(m,'surface_render_method'):m.surface_render_method='DITHERED'
 return m
def finish(o,name,ma,col):
 o.name=name;o.data.name=name+' Geometry';o.data.materials.append(ma);move(o,col)
 for p in o.data.polygons:p.use_smooth=True
 return o
def box(name,position,size,ma,col):
 bpy.ops.mesh.primitive_cube_add(size=1,location=xyz(position));o=bpy.context.object;o.scale=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,ma,col)
def cylinder(name,position,radius,height,ma,col,bottom=None,vertices=16):
 bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=bottom if bottom is not None else radius,radius2=radius,depth=height,location=xyz(position));return finish(bpy.context.object,name,ma,col)
def rod(name,start,end,radius,ma,col,vertices=12):
 a,b=xyz(start),xyz(end);d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=d.length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return finish(o,name,ma,col)
def line_net(name,lines,ma,col):
 cu=bpy.data.curves.new(name+' Geometry','CURVE');cu.dimensions='3D';cu.bevel_depth=.003;cu.bevel_resolution=0;cu.resolution_u=1
 for a,b in lines:
  sp=cu.splines.new('POLY');sp.points.add(1)
  for i,p in enumerate([a,b]):v=xyz(p);sp.points[i].co=(*v,1)
 ob=bpy.data.objects.new(name,cu);col.objects.link(ob);cu.materials.append(ma);return ob

def glb_metadata(p):
 b=p.read_bytes();ensure(b[:4]==b'glTF','Invalid GLB '+str(p));n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);return {'actions':[a['name'] for a in g.get('animations',[])],'meshCount':len(g.get('meshes',[])),'skins':len(g.get('skins',[]))}

def import_actor(identity,name,path,position,yaw,parent_col,kind):
 meta=glb_metadata(path);old_objects=set(bpy.data.objects);old_actions=set(bpy.data.actions);old_mats=set(bpy.data.materials);old_images=set(bpy.data.images)
 bpy.ops.import_scene.gltf(filepath=str(path))
 objects=[o for o in bpy.data.objects if o not in old_objects];actions=[a for a in bpy.data.actions if a not in old_actions];col=collection(identity+' · '+name,parent_col)
 prefix=identity+'__'
 # Imported bone-display helpers are hidden and carry no source skin or surface.
 for o in list(objects):
  if o.type=='MESH' and not any(m.type=='ARMATURE' for m in o.modifiers):
   bpy.data.objects.remove(o,do_unlink=True);objects.remove(o)
 wrapper=bpy.data.objects.new(prefix+'WORLD',None);col.objects.link(wrapper);wrapper['actor_id']=identity;wrapper['visible_name']=name;wrapper['kind']=kind;wrapper['source_file']=str(path.relative_to(ROOT));wrapper['source_sha256']=digest(path);wrapper['coordinate_contract']='glTF [x,y,z] -> Blender [x,-z,y]; yaw about +Z'
 for o in objects:
  original=o.name;o.name=prefix+original;o['actor_id']=identity;o['source_node']=original
  if o.data:o.data.name=prefix+o.data.name
  move(o,col)
 # Preserve every importer transform / inverse bind relationship before applying
 # the shared navigation wrapper. No source geometry or action is rewritten.
 for o in objects:
  if o.parent not in objects:
   w=o.matrix_world.copy();o.parent=wrapper;o.matrix_world=w
 wrapper.location=xyz(position);wrapper.rotation_euler.z=float(yaw)
 expected=set(meta['actions']);found={}
 for ac in actions:
  original=ac.name
  # Imported names are exact clip names because preceding actors are prefixed.
  ensure(original in expected,'Unexpected imported action '+identity+': '+original)
  found[original]=ac;ac.name=prefix+original;ac.use_fake_user=True
 ensure(set(found)==expected,'Clip mismatch '+identity)
 for ma in bpy.data.materials:
  if ma not in old_mats:ma.name=prefix+ma.name
 for im in bpy.data.images:
  if im not in old_images:im.name=prefix+im.name
 rigs=[o for o in objects if o.type=='ARMATURE'];ensure(len(rigs)==1,identity+' must contain one real rig')
 for rig in rigs:
  ensure(rig.animation_data is not None,identity+' missing animation data')
  for tr in rig.animation_data.nla_tracks:
   tr.mute=True
   if tr.strips and tr.strips[0].action:tr.name=tr.strips[0].action.name
  rig.animation_data.action=found['Idle']
  if found['Idle'].slots:rig.animation_data.action_slot=found['Idle'].slots[0]
 skinned=[o for o in objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
 ensure(skinned,identity+' has no skinned surface');ensure(len(skinned)==meta['meshCount'],identity+' source surface count mismatch');ensure(len(rigs[0].data.bones)>5,identity+' is not articulated')
 return {'id':identity,'name':name,'kind':kind,'wrapper':wrapper.name,'rig':rigs[0].name,'bones':len(rigs[0].data.bones),'skinnedMeshes':len(skinned),'meshObjects':len([o for o in objects if o.type=='MESH']),'clips':sorted(ac.name for ac in actions),'clipCount':len(actions),'positionThree':position,'positionBlender':list(wrapper.location),'yaw':float(yaw),'sourceSha256':digest(path)}

def ground_y(h,x,z):
 g=NAV_HABITATS.get(h['id'])
 if not g:return float(h['shelter'][1])
 step=g['spacing'];origin=g['origin'];c=math.floor((x-origin[0])/step+.5);r=math.floor((z-origin[1])/step+.5);index=r*g['cols']+c;valid=set(g['cells'])
 if c<0 or r<0 or c>=g['cols'] or r>=g['rows'] or index not in valid:
  index=min(g['cells'],key=lambda i:(origin[0]+i%g['cols']*step-x)**2+(origin[1]+i//g['cols']*step-z)**2)
 return float(g['heights'].get(str(index),g['center'][1]))

def habitat_props(h,parent):
 ident=h['id'];pre=ident+'__';col=collection(ident+' · habitat',parent);s=h['shelter'];canopy=h.get('shelterCanopy') or h.get('canopy');large=bool(h.get('large','pony' in ident))
 # runtime-spawn.json can provide explicit roof geometry. It also preserves all
 # final navigation habitat fields, so no hidden resampling happens here.
 bounds=canopy['bounds'] if canopy else h.get('shelterBounds')
 if bounds is None:
  slots=h.get('restSlots') or [s];points=[q.get('point',q) if isinstance(q,dict) else q for q in slots]
  margin=float(h.get('shelterMargin',.8 if large else .7));bounds=[min(q[0] for q in points)-margin,min(q[2] for q in points)-margin,max(q[0] for q in points)+margin,max(q[2] for q in points)+margin]
 x0,z0,x1,z1=bounds;cx,cz=(x0+x1)/2,(z0+z1)/2;ground=float(h.get('shelterGroundY',ground_y(h,cx,cz)));width,depth=x1-x0,z1-z0
 roofY=float(canopy['roofY'] if canopy else h.get('roofY',ground+(1.95 if large else 2.05 if h.get('perches') else .95)))
 wood=material(pre+'warm wood',(.49,.40,.27));roof=material(pre+'green roof',(.17,.24,.13));pad=material(pre+'resting pad',(.68,.60,.43));ceramic=material(pre+'ceramic',(.73,.68,.57));food=material(pre+'food',(.46,.27,.11));water=material(pre+'water',(.21,.49,.54))
 pad_center_y=float(canopy.get('floorY',ground+.012)) if canopy else ground+.012
 rest_points=[q.get('point',q) if isinstance(q,dict) else q for q in (h.get('restSlots') or [s])];minimum_rest_y=min(float(q[1]) for q in rest_points)
 box(pre+'resting pad',[cx,pad_center_y,cz],[width,.025,depth],pad,col);box(pre+'roof',[cx,roofY,cz],[width,.07,depth],roof,col)
 if canopy:
  for i,q in enumerate(canopy['posts']):
   if len(canopy['posts'])==4:cylinder(pre+'post '+str(i),[q[0],ground+(roofY-ground)/2,q[2]],float(canopy.get('postRadius',.023)),roofY-ground,wood,col,vertices=8)
   else:box(pre+'post '+str(i),[q[0],ground+(roofY-ground)/2,q[2]],[.035,roofY-ground,.035],wood,col)
 else:
  for i,x in enumerate([x0-.12,x1+.12]):box(pre+'post '+str(i),[x,ground+(roofY-ground)/2,z0-.12],[.035,roofY-ground,.035],wood,col)
 bowls=[]
 for kind in ['food','drink']:
  p=h[kind];y=float(h.get(kind+'GroundY',ground_y(h,p[0],p[2])));r=float(h.get('bowlRadius',.28 if large else .18));cylinder(pre+kind+' bowl',[p[0],y+.037,p[2]],r,.075,ceramic,col,bottom=r*.78,vertices=24);cylinder(pre+kind+' contents',[p[0],y+.078,p[2]],r*.81,.012,food if kind=='food' else water,col,bottom=r*.75,vertices=24);bowls.append({'kind':kind,'point':p,'radius':r})
 perches=h.get('perches',[])
 for i,q in enumerate(perches):
  y=float(h.get('perchGroundYs',[ground_y(h,q[0],q[2]) for q in perches])[i]);cylinder(pre+'perch post '+str(i),[q[0],y+(q[1]-y)/2,q[2]],.018,q[1]-y,wood,col,bottom=.022,vertices=8);rod(pre+'perch crossbar '+str(i),[q[0]-.275,q[1]-.01,q[2]],[q[0]+.275,q[1]-.01,q[2]],.021,wood,col,vertices=10)
 if perches:
  xa,za,xb,zb=h['bounds'];top=float(h.get('aviaryTopY',2.25));netmat=material(pre+'aviary net',(.26,.35,.24),.30)
  for x in [xa,xb]:
   for z in [za,zb]:cylinder(pre+'aviary corner '+str(x)+','+str(z),[x,top/2,z],.023,top,roof,col,vertices=8)
  lines=[];y=.3
  while y<=top:
   lines.extend([([xa,y,za],[xb,y,za]),([xb,y,za],[xb,y,zb]),([xb,y,zb],[xa,y,zb]),([xa,y,zb],[xa,y,za])]);y+=.32
  x=xa
  while x<=xb:lines.extend([([x,0,za],[x,top,za]),([x,0,zb],[x,top,zb])]);x+=.4
  z=za
  while z<=zb:lines.extend([([xa,0,z],[xa,top,z]),([xb,0,z],[xb,top,z])]);z+=.4
  line_net(pre+'aviary wire',lines,netmat,col)
 col['habitat_id']=ident;col['source']='runtime-spawn.json static initial visual geometry';return {'id':ident,'bounds':bounds,'roofY':roofY,'groundY':ground,'padCenterY':pad_center_y,'padTopY':pad_center_y+.0125,'minimumRestY':minimum_rest_y,'bowls':bowls,'perches':len(perches),'objects':len(col.objects)}

def validate(recs,props,source_sha,snapshot_sha):
 whole=bpy.data.scenes['01 Whole town'];bpy.context.window.scene=whole;whole.frame_set(0);bpy.context.view_layer.update();results=[]
 for rec in recs:
  ob=bpy.data.objects.get(rec['wrapper']);rig=bpy.data.objects.get(rec['rig']);ensure(ob and rig,rec['id']+' missing after reopen');ensure(rig.type=='ARMATURE',rec['id']+' has no armature')
  acs=[a for a in bpy.data.actions if a.name.startswith(rec['id']+'__')];ensure(len(acs)==rec['clipCount'],rec['id']+' clips missing after reopen');ensure(rig.animation_data.action.name==rec['id']+'__Idle',rec['id']+' initial pose not Idle')
  finite=all(math.isfinite(v) for b in rig.pose.bones for row in b.matrix for v in row);ensure(finite,rec['id']+' non-finite initial pose');ensure((ob.location-xyz(rec['positionThree'])).length<1e-6,rec['id']+' spawn position mismatch');ensure(abs(ob.rotation_euler.z-rec['yaw'])<1e-6,rec['id']+' spawn yaw mismatch')
  results.append({**rec,'reopened':True,'idlePoseFinite':True,'positionMatchesSnapshot':True,'clipCountReopened':len(acs)})
 for prop in props:
  pad=bpy.data.objects.get(prop['id']+'__resting pad');ensure(pad is not None,prop['id']+' resting pad missing');actual_top=max((pad.matrix_world@Vector(v)).z for v in pad.bound_box);ensure(abs(actual_top-prop['padTopY'])<1e-6,prop['id']+' pad top differs from canopy.floorY');ensure(actual_top<=prop['minimumRestY']+.001,prop['id']+' resting pad penetrates resting feet');prop['reopenedPadTopY']=actual_top;prop['padAtOrBelowRestGround']=True
 ensure(digest(SOURCE)==source_sha,'Source town was modified');ensure(digest(SNAPSHOT)==snapshot_sha,'Snapshot changed during assembly')
 return {'status':'PASS','sourceTownSha256':source_sha,'sourceTownUnchanged':True,'snapshotSha256':snapshot_sha,'output':OUTPUT.name,'selectedScene':whole.name,'animals':len([r for r in results if r['kind']=='animal']),'caretakers':len([r for r in results if r['kind']=='caretaker']),'animalClips':sum(r['clipCount'] for r in results if r['kind']=='animal'),'caretakerClips':sum(r['clipCount'] for r in results if r['kind']=='caretaker'),'habitatCount':len(props),'allPadsAtOrBelowRestGround':all(p['padAtOrBelowRestGround'] for p in props),'actors':results,'habitats':props,'imagesPacked':all(i.packed_file is not None for i in bpy.data.images if i.source=='FILE' and i.size[0]>8),'scope':'Editable static initial town layout with every actor animation retained. Browser behavior, paths, IK and weather are not baked.'}

if __name__=='__main__':
 started=time.time();ensure(SNAPSHOT.exists(),'Required final snapshot has not been written: '+str(SNAPSHOT));snapshot=json.loads(SNAPSHOT.read_text());NAV_HABITATS.update({h['id']:h for h in json.loads((ROOT/'reference/navigation.json').read_text())['habitats']});source_sha=digest(SOURCE);snapshot_sha=digest(SNAPSHOT);profiles=json.loads((ROOT/'animal-library/assets/manifest.json').read_text())['animals'];by_id={a['id']:a for a in profiles};spawns=snapshot['animals'];ensure(len(spawns)==20,'Expected 20 final animal spawns');ensure(set(a['id'] for a in spawns)==set(by_id),'Spawn identities mismatch');habitats=snapshot['habitats'];ensure(len(habitats)==11,'Expected 11 final habitats')
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.data.scenes['01 Whole town'];bpy.context.window.scene=scene;scene.render.fps=24;actors_col=collection('V6 Animals and caretaker',scene.collection);props_col=collection('V6 Animal habitats',scene.collection);recs=[]
 for spawn in spawns:
  p=by_id[spawn['id']];recs.append(import_actor(p['id'],p['name'],ROOT/'animal-library'/p['glb'],spawn['position'],spawn.get('yaw',0),actors_col,'animal'))
 caretaker=snapshot.get('caretaker',snapshot.get('human'));ensure(caretaker is not None,'Caretaker snapshot missing');recs.append(import_actor('Ache_caretaker','阿澈',ROOT/'assets/people/Ache-caretaker.glb',caretaker['position'],caretaker.get('yaw',0),actors_col,'caretaker'))
 props=[habitat_props(h,props_col) for h in habitats];scene['V6_snapshot']=snapshot_sha;scene['V6_scope']='Initial static animal layout; all articulated clips retained; no browser behavior baked';scene.frame_set(0);bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT),compress=True)
 bpy.ops.wm.open_mainfile(filepath=str(OUTPUT));report=validate(recs,props,source_sha,snapshot_sha);report['outputSha256']=digest(OUTPUT);report['elapsedSeconds']=round(time.time()-started,2);REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2));print('NATIVE_V6_COMPLETE',report['animals'],report['animalClips'],report['caretakerClips'],report['habitatCount'],flush=True)
