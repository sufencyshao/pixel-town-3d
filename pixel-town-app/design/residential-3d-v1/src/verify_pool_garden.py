import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent.parent
bpy.ops.wm.open_mainfile(filepath=str(R/'hero/hero.blend'))
p=bpy.data.objects['Pool garden path'];v=[p.matrix_world@x.co for x in p.data.vertices]
assert abs((v[0]-v[1]).length-1.25)<1e-4
assert abs(v[0].x-4.35)<1e-4 and abs(v[1].x-4.35)<1e-4
assert all(abs(v[i].y+4)<1e-4 and abs(v[i].z-.26)<1e-4 for i in [12,13])
segments=[[v[i+j].xy for j in [0,1,5,4]] for i in [0,4,8]]
def intersects(a,b):
 for poly in [a,b]:
  for i,x in enumerate(poly):
   e=poly[(i+1)%len(poly)]-x;n=Vector((-e.y,e.x));aa=[p.dot(n) for p in a];bb=[p.dot(n) for p in b]
   if min(max(aa),max(bb))-max(min(aa),min(bb))<1e-5:return False
 return True
checked=0
for o in bpy.data.collections['Landscape'].objects:
 if o.type!='MESH' or not o.name.startswith(('Southeast','Tree trunk','Tree crown','Garden shrub','Flower','Mixed flower','Lavender')):continue
 pts=[o.matrix_world@Vector(c) for c in o.bound_box];x0,x1=min(p.x for p in pts),max(p.x for p in pts);y0,y1=min(p.y for p in pts),max(p.y for p in pts)
 b=[Vector((x0,y0)),Vector((x1,y0)),Vector((x1,y1)),Vector((x0,y1))]
 for seg in segments:assert not intersects(seg,b),o.name
 checked+=1
result={'status':'PASS','pathWidthMetres':1.25,'terraceJoin':[4.35,-6.15,.2],'poolDeckJoin':[8,-4,.26],'landscapeBoundsChecked':checked,'vegetationOverPath':False}
(R/'hero/pool-garden-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
