import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1];S=R.parent/'residential-3d-v1';m=json.loads((R/'manifest.json').read_text());checks=[]
def check(label,ok):
 checks.append({'check':label,'passed':bool(ok)})
 if not ok:raise AssertionError(label)
def overlap(a,b):return min(a[2],b[2])-max(a[0],b[0]),min(a[3],b[3])-max(a[1],b[1])
for key,s in m['sources'].items():
 for ext in ['blend','glb']:check(key+' source '+ext+' unchanged',hashlib.sha256((S/key/(key+'.'+ext)).read_bytes()).hexdigest()==s[ext+'Sha256'])
 check(key+' source triangles retained',s['sourceTriangles']==s['mergedTriangles'])
for zone,d in m['districts'].items():
 w,h=d['size'];plots=d['plots'];p=m['paths'][zone]
 check(zone+' plots contained',all(-w/2<=a[0]<a[2]<=w/2 and -h/2<=a[1]<a[3]<=h/2 for a in plots))
 check(zone+' private plots disjoint',all(min(overlap(a,b))<=0 for i,a in enumerate(plots) for b in plots[i+1:]))
 check(zone+' path tiles disjoint',all(min(overlap(a,b))<=1e-6 for i,a in enumerate(p) for b in p[i+1:]))
 seen={0};todo=[0]
 while todo:
  i=todo.pop()
  for j,b in enumerate(p):
   dx,dy=overlap(p[i],b)
   if j not in seen and dx>=-1e-6 and dy>=-1e-6 and max(dx,dy)>1e-5:seen.add(j);todo.append(j)
 check(zone+' paths form one connected network',len(seen)==len(p))
 for b in [b for b in m['buildings'] if b['zone']==zone]:
  x,y=b['entry'];check(b['id']+' entry meets connected path',any(a[0]-1e-6<=x<=a[2]+1e-6 and a[1]-1e-6<=y<=a[3]+1e-6 for a in p))
check('47 units including hero',sum(b['units'] for b in m['buildings'])==47)
check('GLB SHA256',hashlib.sha256((R/'AC-residential-districts.glb').read_bytes()).hexdigest()==m['sha256'])
bpy.ops.wm.open_mainfile(filepath=str(R/'AC-residential-districts.blend'))
check('5 saved camera scenes',len(bpy.data.scenes)==5)
for b in m['buildings']:
 root=bpy.data.objects.get(b['id']);check(b['id']+' root at original scale / planned position',root is not None and all(abs(v-1)<1e-5 for v in root.scale) and all(abs(root.location[i]-b['worldCenter'][i])<1e-4 for i in [0,1]))
 objs=list(root.children);tri=0
 for o in objs:
  if o.type=='MESH':o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
 check(b['id']+' geometry count preserved',tri==m['sources'][b['model']]['sourceTriangles'])
 check(b['id']+' all floors retained',all(any(o.name==b['id']+'__L%02d_Floor'%i for o in objs) for i in range(1,b['floors']+1)))
 # Actual mesh bounds must remain within district; foliage may overhang its private plot.
 ox,oy=m['districts'][b['zone']]['offset'];w,h=m['districts'][b['zone']]['size'];pts=[root.matrix_basis @ o.matrix_basis @ Vector(v) for o in objs if o.type=='MESH' for v in o.bound_box]
 check(b['id']+' geometry within district boundary',all(ox-w/2-.001<=v.x<=ox+w/2+.001 and oy-h/2-.001<=v.y<=oy+h/2+.001 for v in pts))
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'AC-residential-districts.glb'))
tri=0;meshes=[o for o in bpy.data.objects if o.type=='MESH']
for o in meshes:o.data.calc_loop_triangles();tri+=len(o.data.loop_triangles)
check('GLB reimport triangles',tri==m['triangles'])
check('GLB all building roots present',all(bpy.data.objects.get(b['id']) is not None for b in m['buildings']))
check('GLB district roots present',all(bpy.data.objects.get(k) is not None for k in ['A_District','C_District','Context']))
result={'passed':True,'checks':checks,'glbMeshObjects':len(meshes),'glbTriangles':tri,'note':'GLB material primitives can split mesh objects; triangle totals remain identical. Path checks validate static geometry layout, not runtime navigation.'}
(R/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('PASSED',len(checks),tri)
