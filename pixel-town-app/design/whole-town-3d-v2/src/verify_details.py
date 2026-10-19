import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent.parent
m=json.loads((R/'manifest.json').read_text());d=m['streetDetails'];checks=[]
def ck(value,label):
    assert value,label
    checks.append(label)
for name,digest in json.loads((R/'reference/v1-hashes.json').read_text()).items():
    ck(hashlib.sha256((R.parent/'whole-town-3d-v1'/name).read_bytes()).hexdigest()==digest,'V1 unchanged '+name)
bpy.ops.wm.open_mainfile(filepath=str(R/'Town-complete.blend'));bpy.context.window.scene=bpy.data.scenes['01 Whole town'];bpy.context.view_layer.update()
for key,n in [('lamps',53),('benches',16),('crosswalks',48),('signalCrossings',2),('utilityPoles',17),('wireSpans',48),('bins',6),('wayfinding',6),('bollards',8)]:ck(len(d[key])==n,key+' inventory')
ck(len(d['junctions'])==4,'Four asphalt street junctions')
ck(len(d['arrows'])>=40,'Lane direction arrows present')
ck(d['counts']['stoneJointSegments']>500,'Stone path joint geometry present')
for p in d['crosswalks']:
    ck(p['stripeLongAxis']==('y' if p['walkAxis']=='x' else 'x'),'Zebra bars parallel to vehicle travel '+str(p['center']))
    ck(p['stripeLength']>p['stripeWidth'] and p['stripeCount']>=7,'Zebra bars span the road '+str(p['center']))
for p in d['wireSpans']:ck(p['minimumZ']>=6.7,'Wire sag remains above 6.7m')
for p in d['signalCrossings']:ck(p['state']=='vehicle red; pedestrian green; static','No conflicting static signal phases')
# Inspect the actual exported white-bar face dimensions, not only their placement metadata.
zebra=bpy.data.objects['T__Crosswalks'];white_faces=0
for face in zebra.data.polygons:
    if zebra.data.materials[face.material_index].name!='paint' or face.normal.z<.99:continue
    points=[zebra.matrix_world@zebra.data.vertices[i].co for i in face.vertices]
    x=sum(p.x for p in points)/len(points);y=sum(p.y for p in points)/len(points)
    dx=max(p.x for p in points)-min(p.x for p in points);dy=max(p.y for p in points)-min(p.y for p in points)
    nearest=min(d['crosswalks'],key=lambda p:math.hypot(x-p['center'][0],y-p['center'][1]))
    ck((dy>dx if nearest['walkAxis']=='x' else dx>dy),'Actual white stripe direction')
    ck(abs(max(dx,dy)-2.8)<.001 and abs(min(dx,dy)-.4)<.001,'Actual stripe proportions')
    white_faces+=1
ck(white_faces==sum(p['stripeCount'] for p in d['crosswalks']),'Every crossing has its complete white-bar array')
# Test new pole shafts against pre-existing above-ground geometry, using actual triangles.
vs=[];fs=[]
old={'T__Planting'}
for o in bpy.context.scene.objects:
    if o.type!='MESH' or not (o.name[0] in 'ABCDEFGHI' or o.name in old):continue
    me=o.data;me.calc_loop_triangles();verts=[o.matrix_world@v.co for v in me.vertices]
    for t in me.loop_triangles:
        points=[verts[i] for i in t.vertices]
        if max(p.z for p in points)<.25:continue
        off=len(vs);vs.extend(points);fs.append((off,off+1,off+2))
tree=BVHTree.FromPolygons(vs,fs,all_triangles=True)
for p in d['lamps']:
    x,y,z=p['base']
    ck(all(tree.find_nearest(Vector((x,y,h)),.20)[0] is None for h in [.5,1,1.5,2,2.5,3,3.5,4]),'Lamp shaft clear of existing geometry '+str([x,y]))
for x,y,z in d['utilityPoles']:
    ck(all(tree.find_nearest(Vector((x,y,h)),.18)[0] is None for h in [.5,1,2,3,4,5,6]),'Utility pole clear '+str([x,y]))
for b in d['benches']:
    x,y=b['center'];a=b['angle']
    ck(all(tree.find_nearest(Vector((x+q*math.cos(a),y+q*math.sin(a),.7)),.42)[0] is None for q in [-.7,0,.7]),'Bench clear of source geometry '+str([x,y]))
for x,y in d['bins']:
    ck(all(abs(y-b['center'][1])>.8 or abs(x-b['center'][0])>.95+.44+.1 for b in d['benches']),'Bins do not overlap benches '+str([x,y]))
report={'status':'PASS','checks':len(checks),'items':checks,'counts':d['counts'],'scope':'Inventory, original preservation, sampled pole and bench geometry clearance; complements full-town public-route validation.'}
(R/'qa/detail-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print('DETAIL VALIDATION PASS',len(checks),flush=True)
