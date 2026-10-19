import bpy,json,math,hashlib,os
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
results={}
def bounds(o):
 vs=[o.matrix_world@v.co for v in o.data.vertices]
 return [(min(v[i] for v in vs),max(v[i] for v in vs)) for i in range(3)]
def intersects(a,b):return all(min(a[i][1],b[i][1])-max(a[i][0],b[i][0])>1e-4 for i in range(3))
for k in os.environ.get('RESIDENTIAL_KEYS','courtyard,hero,apartment-3,apartment-4,apartment-5').split(','):
 p=ROOT/k;m=json.loads((p/'manifest.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(p/(k+'.blend')))
 assert len(bpy.data.scenes)==1+2*m['floors']
 for f in range(1,m['floors']+1):
  sc=bpy.data.scenes['%02d Floor %d Interior'%(f+1,f)];children=sc.view_layers[0].layer_collection.children
  assert children['Roof'].exclude
  assert children['L%02d_Front'%f].exclude
  if f<m['floors']:assert children['L%02d_Floor'%(f+1)].exclude
  if f<m['floors']:
   stairs=[o for o in bpy.data.collections['L%02d_Stairs'%f].objects if o.type=='MESH' and (o.name.startswith('Stair tread') or o.name.startswith('Stair west') or o.name.startswith('Stair east'))]
   assert len(stairs)==18
   slabs=[o for o in bpy.data.collections['L%02d_Floor'%(f+1)].objects if o.type=='MESH']
   for st in stairs:
    for slab in slabs:assert not intersects(bounds(st),bounds(slab)),(k,st.name,slab.name)
   expected=f*m['floorHeight']+.18
   assert abs(max(bounds(o)[2][1] for o in stairs)-expected)<1e-4
  if f<m['floors']:
   walls=[o for o in bpy.data.collections['L%02d_Front'%f].objects if o.type=='MESH' and o.name.startswith(('Front wall','Suite front','Stair core front'))]
   nextfloors=[o for o in bpy.data.collections['L%02d_Floor'%(f+1)].objects if o.type=='MESH']
   assert abs(max(bounds(o)[2][1] for o in walls)-min(bounds(o)[2][0] for o in nextfloors))<1e-4, (k,f,'wall/slab seam')
  floorobjs=[o for o in bpy.data.collections['L%02d_Floor'%f].objects if o.type=='MESH']
  floorTop=max(bounds(o)[2][1] for o in floorobjs)
  walls=[o for o in bpy.data.collections['L%02d_Front'%f].objects if o.type=='MESH' and o.name.startswith(('Front wall','Suite front','Stair core front')) and 'sill' not in o.name and 'lintel' not in o.name]
  # Ground villa has a thin finish; upper levels are joined at the structural datum.
  if f>1:assert abs(min(bounds(o)[2][0] for o in walls)-floorTop)<1e-4,(k,f,'upper wall/slab seam')
  balconies=[o for o in bpy.data.collections['L%02d_Front'%f].objects if o.name.startswith('Balcony slab')]
  for balcony in balconies:
   b=bounds(balcony);assert abs(b[2][1]-((f-1)*m['floorHeight']+.18))<1e-4
   assert abs(b[1][1]-(-5.64 if k.startswith('apartment') else -4.62))<1e-4
  if k.startswith('apartment'):
   beds=[o for o in bpy.data.collections['L%02d_Interior'%f].objects if o.name.startswith('Bed frame')]
   assert len(beds)==2
   # Keep a standing-person-width passage immediately before and behind each bedroom door.
   z=(f-1)*m['floorHeight']
   for side in [-1,1]:
    x=side*10.1;passage=[(x-.35,x+.35),(.9,2.6),(z+.25,z+2.0)]
    for o in bpy.data.collections['L%02d_Interior'%f].objects:
     if o.type=='MESH' and o.name.startswith(('Kitchen cabinets','Fridge','Wardrobe','Bed frame','Study desk')):
      assert not intersects(passage,bounds(o)),(k,f,'Bedroom passage blocked',o.name)

 if k=='hero':
  landscaping=bpy.data.collections['Landscape'].objects
  vegetable=[o for o in landscaping if o.name.startswith('Vegetable soil bed')]
  flowers=[o for o in landscaping if o.name.startswith('Front garden planting mound')]
  assert len(vegetable)==3 and len(flowers)==2
  path=bounds(bpy.data.objects['Entry path'])
  for o in flowers:
   b=bounds(o);assert not all(min(path[i][1],b[i][1])-max(path[i][0],b[i][0])>1e-4 for i in range(2))
  water=bpy.data.objects['Pool water'];bottom=bpy.data.objects['Pool basin floor']
  assert water.location.z-bottom.location.z>1.2
  for o in bpy.data.collections['Landscape'].objects:
   if o.type=='MESH' and o.name.startswith(('Garden base','Pool deck')):assert not intersects(bounds(water),bounds(o))
 sceneNames=list(bpy.data.scenes.keys());bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/(k+'.glb')))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];tri=0
 for o in meshes:
  assert len(o.data.materials)>0;o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
  for v in o.data.vertices:assert all(math.isfinite(x) for x in v.co)
 assert len(meshes)==m['meshObjects'];assert tri==m['triangles'];assert m['degenerateTriangles']==0
 results[k]={'status':'PASS','blender':bpy.app.version_string,'scenes':sceneNames,'meshObjects':len(meshes),'triangles':tri,'sha256':hashlib.sha256((p/(k+'.glb')).read_bytes()).hexdigest(),'stairsAndFloorSlabs':'no volume intersections','unitCount':m['units'],'wallSlabJoints':'continuous within 0.1 mm numerical tolerance','balconyJoints':'same level and edge-to-edge'}
 print('PASS',k,flush=True)
(ROOT/('validation-partial.json' if os.environ.get('RESIDENTIAL_KEYS') else 'validation.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2));print('ALL VALIDATION PASS',flush=True)
