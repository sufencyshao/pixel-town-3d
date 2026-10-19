"""Read-only geometry sampler for V6 animal habitats and public human routes.

Run with Blender --background --python this_file.py. No source .blend is saved.
World JSON is glTF Y-up (x, Blender z, -Blender y), in metres.
This is a sampled runtime graph, not an exhaustive or continuous town navmesh.
"""
import bpy
import hashlib
import json
import math
import sys
import time
from collections import Counter, deque
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent.parent
SPACING = .5
PREVIOUS = json.loads((ROOT/'reference/navigation.json').read_text()) if (ROOT/'reference/navigation.json').exists() else None
PREVIOUS_HABITATS = {h['id']:h for h in PREVIOUS['habitats']} if PREVIOUS else {}
MANIFEST_PATH=(ROOT.parent/'animal-assets-3d-v1/assets/manifest.json') if (ROOT.parent/'animal-assets-3d-v1/assets/manifest.json').exists() else (ROOT/'animal-library/assets/manifest.json')
ANIMAL_MANIFEST = json.loads(MANIFEST_PATH.read_text())
PROFILES = {a['id']:a for a in ANIMAL_MANIFEST['animals']}
# Bounds, seeds and anchors below are all glTF X,Z. Cells use origin+i*spacing.
LAYOUT = [
    dict(id='a-garden-cats', name='住宅共享花园', zone='A', bounds=[-98,-100,-77,-78], seed=[-88,-91], petIds=['01_cat_tabby','05_cat_maine'], style='garden-refuge'),
    dict(id='b-library-cat', name='图书馆前庭', zone='B', bounds=[-3,-80,7,-76], seed=[1,-78], petIds=['04_cat_siamese'], style='reading-refuge'),
    dict(id='h-florist-courtyard', name='花店前庭', zone='H', bounds=[-2,76.5,6,80.5], seed=[1,78], petIds=['02_cat_calico','10_dog_dachshund'], style='shop-refuge'),
    dict(id='i-inn-garden', name='旅店北侧花园', zone='I', bounds=[60,47,75,53.5], seed=[68,50], petIds=['03_cat_british_blue','11_dog_poodle'], style='inn-refuge'),
    dict(id='f-dog-meadow', name='河岸公园宠物草地', zone='F', bounds=[55.5,4.5,73,21.5], seed=[64,13], petIds=['06_dog_corgi','07_dog_shiba','09_dog_golden'], style='dog-meadow'),
    dict(id='f-bird-sanctuary', name='公园安静鸟舍', zone='F', bounds=[83,-24,89,-17.5], seed=[87,-21], petIds=['12_bird_budgie_green','13_bird_budgie_blue','14_bird_cockatiel','15_bird_canary'], style='protected-aviary'),
    dict(id='g-orchard-dog', name='果园照护草道', zone='G', bounds=[-64.5,54.5,-61,66.5], seed=[-63,61], petIds=['08_dog_border'], style='dog-refuge'),
    dict(id='g-rabbit-garden', name='果园西侧兔园', zone='G', bounds=[-86.5,49.5,-81,59], seed=[-84,54], petIds=['16_rabbit_lop','17_rabbit_dutch'], style='rabbit-garden'),
    dict(id='g-guinea-garden', name='果园安静小围栏', zone='G', bounds=[-86,63,-81,69], seed=[-83,66], petIds=['18_guineapig_rosette'], style='small-mammal-garden'),
    dict(id='g-tortoise-garden', name='果园日照与遮阴角', zone='G', bounds=[-60.5,67,-53.5,70.5], seed=[-57,68.5], petIds=['19_tortoise_hermann'], style='tortoise-garden'),
    dict(id='g-pony-paddock', name='果树间矮马牧栏', zone='G', bounds=[-76.5,53.5,-71.5,67.5], seed=[-74,61], petIds=['20_pony_shetland'], style='pony-paddock', clearance=.6),
]

started = time.time()
source = ROOT / 'Town-complete.blend'
before = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
bpy.context.window.scene = bpy.data.scenes['01 Whole town']
bpy.context.view_layer.update()
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not any(c.name == 'Studio' for c in o.users_collection)]

support_vertices, support_faces, public_vertices, public_faces = [], [], [], []
solid_vertices, solid_faces = [], []
surface_names = Counter()
inventory = []

def append_triangle(vertices, faces, points):
    off = len(vertices)
    vertices.extend(points)
    faces.append((off, off+1, off+2))

for o in meshes:
    me = o.data
    me.calc_loop_triangles()
    vs = [o.matrix_world @ v.co for v in me.vertices]
    is_ground = any(s in o.name for s in ['__Ground','__Landscape','__Paths','__Paving','__Pet_Lawn','__Riverside_Paths','__Transitions','__Bridges','__Far_Bank','__Inn_Terrace'])
    is_public = any(s in o.name for s in ['__Paths','__Paving','__Bridges','__Riverside_Paths','__Transitions','__Far_Bank'])
    if any(o.name.startswith(z+'__') for z in 'ABFGHI') and (is_ground or any(k in o.name for k in ['Fence','Equipment','Orchard','Habitat'])):
        inventory.append({'name':o.name,'boundsBlender':[[round(min(v[i] for v in vs),4) for i in range(3)],[round(max(v[i] for v in vs),4) for i in range(3)]],'materials':[m.name for m in me.materials]})
    for t in me.loop_triangles:
        ps = [vs[i] for i in t.vertices]
        lo, hi = min(p.z for p in ps), max(p.z for p in ps)
        if lo > 2.8 or hi < -.02:
            continue
        normal = (ps[1]-ps[0]).cross(ps[2]-ps[0])
        top = normal.length > 1e-9 and normal.z/normal.length > .90
        ground = is_ground and top and -.005 <= lo and hi <= .31
        if ground:
            append_triangle(support_vertices,support_faces,ps)
            surface_names[o.name] += 1
            if is_public and lo >= .03:
                if o.name != 'F__Far_Bank' or all(abs(p.z-.13)<1e-4 for p in ps):
                    append_triangle(public_vertices,public_faces,ps)
        # Upward ground is support, not an obstacle. Low paving sides below 14cm
        # are step transitions. Planting, fences, equipment and walls stay solid.
        if not ground and hi >= .14:
            append_triangle(solid_vertices,solid_faces,ps)

print('GEOMETRY',len(support_faces),len(public_faces),len(solid_faces),flush=True)
support_bvh = BVHTree.FromPolygons(support_vertices,support_faces,all_triangles=True)
public_bvh = BVHTree.FromPolygons(public_vertices,public_faces,all_triangles=True)
solid_bvh = BVHTree.FromPolygons(solid_vertices,solid_faces,all_triangles=True)

def ground_at(x,z,public=False):
    bvh = public_bvh if public else support_bvh
    # Ground-only triangles ensure roofs/trees cannot hide the lawn below them.
    hit = bvh.ray_cast(Vector((x,-z,.6)),Vector((0,0,-1)),.62)[0]
    if hit is None:
        # Jitter only resolves exact triangle-edge arithmetic; it is <.1mm.
        hits = [bvh.ray_cast(Vector((x+dx,-z+dy,.6)),Vector((0,0,-1)),.62)[0] for dx,dy in [(4e-5,0),(-4e-5,0),(0,4e-5),(0,-4e-5)]]
        hits = [h for h in hits if h is not None]
        return max(h.z for h in hits) if hits else None
    return hit.z

clear_cache = {}
def clear(x,z,radius=.42,public=False):
    key = (round(x,5),round(z,5),radius,public)
    if key in clear_cache:
        return clear_cache[key]
    h = ground_at(x,z,public)
    if h is None:
        clear_cache[key] = None
        return None
    # Centre and eight perimeter supports prevent steps into water/lawn holes.
    for a in range(8):
        hh = ground_at(x+radius*math.cos(a*math.pi/4),z+radius*math.sin(a*math.pi/4),public)
        if hh is None or abs(hh-h) > .13:
            clear_cache[key] = None
            return None
    # Overlapping spheres form a conservative capsule from small animal height
    # to human head height. Ground triangles were excluded above.
    for hh in [.14,.38,.67,.96,1.25,1.54,1.83]:
        if solid_bvh.find_nearest(Vector((x,-z,h+hh)),radius)[0] is not None:
            clear_cache[key] = None
            return None
    clear_cache[key] = round(h,5)
    return round(h,5)

def connected_component(cells,cols,rows,start):
    seen={start}; queue=deque([start])
    while queue:
        i=queue.popleft(); col,row=i%cols,i//cols
        for dc,dr in [(1,0),(-1,0),(0,1),(0,-1)]:
            c,r=col+dc,row+dr; n=r*cols+c
            if 0<=c<cols and 0<=r<rows and n in cells and n not in seen:
                seen.add(n);queue.append(n)
    return seen

def cell_position(habitat,index):
    return [round(habitat['origin'][0]+(index%habitat['cols'])*SPACING,5),habitat['heights'][str(index)],round(habitat['origin'][1]+(index//habitat['cols'])*SPACING,5)]

def bird_prop_bvh(h):
    """Runtime bird props mirrored exactly from the agreed JSON contract."""
    vertices,faces=[],[]
    def blender(p):return Vector((p[0],-p[2],p[1]))
    def box(center,size):
        off=len(vertices)
        vertices.extend(blender([center[0]+sx*size[0]/2,center[1]+sy*size[1]/2,center[2]+sz*size[2]/2]) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)])
        for a,b,c,d in [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]:faces.extend([(off+a,off+b,off+c),(off+a,off+c,off+d)])
    def cylinder(start,end,radius):
        start,end=blender(start),blender(end);axis=(end-start).normalized();up=Vector((0,0,1)) if abs(axis.z)<.9 else Vector((1,0,0));u=axis.cross(up).normalized();v=axis.cross(u).normalized();off=len(vertices);count=24
        for p in [start,end]:
            vertices.extend(p+(u*math.cos(i*math.tau/count)+v*math.sin(i*math.tau/count))*radius for i in range(count))
        for i in range(count):
            j=(i+1)%count;faces.extend([(off+i,off+j,off+count+j),(off+i,off+count+j,off+count+i)])
        for i in range(1,count-1):faces.extend([(off,off+i+1,off+i),(off+count,off+count+i,off+count+i+1)])
    canopy=h['shelterCanopy'];xa,za,xb,zb=canopy['bounds']
    box([(xa+xb)/2,canopy['roofY'],(za+zb)/2],[xb-xa,canopy['thickness'],zb-za])
    for p in canopy['posts']:cylinder([p[0],ground_at(p[0],p[2]),p[2]],p,canopy['postRadius'])
    # Original round resting pad, whose top is 3.5cm above ground.
    p=h['shelter'];cylinder(p,[p[0],p[1]+.035,p[2]],.72)
    for p in h['perches']:
        cylinder([p[0],ground_at(p[0],p[2]),p[2]],p,.023)
        cylinder([p[0]-.275,p[1]-.01,p[2]],[p[0]+.275,p[1]-.01,p[2]],.021)
    for p in [h['food'],h['drink']]:cylinder(p,[p[0],p[1]+.084,p[2]],.18)
    xa,za,xb,zb=h['bounds']
    for x in [xa,xb]:
        for z in [za,zb]:cylinder([x,0,z],[x,2.25,z],.023)
    return BVHTree.FromPolygons(vertices,faces,all_triangles=True)

def add_validated_bird_routes(h,retained):
    x0,z0=h['origin'];cols=h['cols']
    # Distinct ground refuge positions keep four birds under the same canopy
    # without occupying one another's body disc.
    candidates=sorted(retained,key=lambda i:math.dist(cell_position(h,i)[::2],h['shelter'][::2]))
    slots=[]
    for pet_id in h['petIds']:
        radius=PROFILES[pet_id]['radius']
        chosen=next(i for i in candidates if all(math.dist(cell_position(h,i)[::2],s['point'][::2])>=radius+PROFILES[s['petId']]['radius']+.12 for s in slots) and all(math.dist(cell_position(h,i)[::2],p[::2])>=.35 for p in h['perches']))
        p=cell_position(h,chosen);p[1]=round(p[1]+.035,5)
        slots.append({'id':'rest-'+str(len(slots)),'petId':pet_id,'point':p,'radius':radius})
    h['restSlots']=slots
    margin=.5+h['maxAnimalRadius'];xa=min(s['point'][0] for s in slots)-margin;xb=max(s['point'][0] for s in slots)+margin;za=min(s['point'][2] for s in slots)-margin;zb=max(s['point'][2] for s in slots)+margin
    roof_y=round(h['shelter'][1]+2.05,5)
    h['shelterCanopy']={'bounds':[round(v,5) for v in [xa,za,xb,zb]],'roofY':roof_y,'thickness':.07,'postRadius':.023,'posts':[[round(x,5),roof_y,round(z,5)] for x in [xa,xb] for z in [za,zb]],'padTopY':round(h['shelter'][1]+.035,5)}
    food=h['food'];h['feederPoint']=[round(food[0]-.35,5),ground_at(food[0]-.35,food[2]),food[2]]
    water=h['drink'];h['drinkingPoint']=[round(water[0]-.35,5),ground_at(water[0]-.35,water[2]),water[2]]
    h['foodRoute']='food';h['waterRoute']='water'
    nodes=[{'id':'perch-'+str(i),'kind':'perch','point':p} for i,p in enumerate(h['perches'])]+[{'id':'food','kind':'food','point':h['feederPoint']},{'id':'water','kind':'water','point':h['drinkingPoint']}]+[{'id':s['id'],'kind':'rest','petId':s['petId'],'point':s['point']} for s in slots]
    h['flightNodes']=nodes
    props=bird_prop_bvh(h)
    def grid_index(p):return round((p[2]-z0)/SPACING)*cols+round((p[0]-x0)/SPACING)
    cruise=1.5
    def flight_clear(p):
        center=Vector((p[0],-p[2],p[1]+.2))
        return solid_bvh.find_nearest(center,.18)[0] is None and props.find_nearest(center,.18)[0] is None
    flight_cells={i for i in retained if flight_clear([cell_position(h,i)[0],cruise,cell_position(h,i)[2]])}
    def route(pa,pb):
        ia,ib=grid_index(pa),grid_index(pb);q=deque([ia]);parent={ia:None}
        assert ia in flight_cells and ib in flight_cells
        while q and ib not in parent:
            i=q.popleft()
            for n in [i-1,i+1,i-cols,i+cols]:
                if n not in flight_cells or n in parent or (abs(n-i)==1 and n//cols!=i//cols):continue
                a,b=cell_position(h,i),cell_position(h,n)
                if not flight_clear([(a[0]+b[0])/2,cruise,(a[2]+b[2])/2]):continue
                parent[n]=i;q.append(n)
        assert ib in parent
        path=[];i=ib
        while i is not None:path.append(i);i=parent[i]
        path.reverse()
        points=[pa,[pa[0],cruise,pa[2]]]+[[cell_position(h,i)[0],cruise,cell_position(h,i)[2]] for i in path]+[[pb[0],cruise,pb[2]],pb]
        points=[p for i,p in enumerate(points) if i==0 or math.dist(p,points[i-1])>1e-5]
        samples=0
        for p1,p2 in zip(points,points[1:]):
            n=max(1,math.ceil(math.dist(p1,p2)/.1))
            for k in range(n+1):
                p=[p1[j]+(p2[j]-p1[j])*k/n for j in range(3)];center=Vector((p[0],-p[2],p[1]+.2))
                assert solid_bvh.find_nearest(center,.18)[0] is None,(h['id'],'Town flight collision',p)
                assert props.find_nearest(center,.18)[0] is None,(h['id'],'Runtime bird prop flight collision',p)
                samples+=1
        return {'radius':.18,'bodyOffset':[0,.2,0],'points':points,'geometrySamples':samples,'runtimePropsValidated':True,'bidirectional':True}
    h['flightRoutes']=[]
    for a in range(len(h['perches'])):
        for b in range(a+1,len(h['perches'])):h['flightRoutes'].append({'from':a,'to':b,**route(h['perches'][a],h['perches'][b])})
    h['accessFlightRoutes']=[]
    for p in nodes[:4]:
        for target in nodes[4:]:h['accessFlightRoutes'].append({'from':p['id'],'to':target['id'],**route(p['point'],target['point'])})
    h['accessFlightRoutes'].append({'from':'food','to':'water',**route(h['feederPoint'],h['drinkingPoint'])})
    for source in nodes[4:6]:
        for target in nodes[6:]:h['accessFlightRoutes'].append({'from':source['id'],'to':target['id'],**route(source['point'],target['point'])})
    h['flightPolicy']='All routes are bidirectional, preserve every point. Perch route numeric IDs map to perch-N nodes. Access routes use string node IDs. Swept body sphere root+[0,.20,0], radius .18; static town plus declared bird props validated at <=.10m samples.'

habitats=[]; habitat_report=[]
for spec in LAYOUT:
    x0,z0,x1,z1=spec['bounds'];cols=round((x1-x0)/SPACING)+1;rows=round((z1-z0)/SPACING)+1
    maximum_radius=max(PROFILES[p]['radius'] for p in spec['petIds'])
    radius=max(spec.get('clearance',.42),math.ceil((maximum_radius+.03)*100)/100);heights={}
    for row in range(rows):
        for col in range(cols):
            x,z=x0+col*SPACING,z0+row*SPACING
            # Body remains inside the authored activity bounds, including turn.
            if x<x0+radius or x>x1-radius or z<z0+radius or z>z1-radius:continue
            h=clear(x,z,radius)
            if h is not None:heights[row*cols+col]=h
    assert heights, 'No legal habitat cells '+spec['id']
    seed=min(heights,key=lambda i:(x0+(i%cols)*SPACING-spec['seed'][0])**2+(z0+(i//cols)*SPACING-spec['seed'][1])**2)
    component=connected_component(heights,cols,rows,seed)
    # Remove any cell with an unsafe traversable half-edge. This makes the
    # runtime's cardinal grid adjacency valid without a separate blocked-edge map.
    bad=set();edge_tests=0
    for i in component:
        for n in [i+1,i+cols]:
            if n not in component or (n==i+1 and n//cols!=i//cols):continue
            x=(x0+(i%cols)*SPACING+x0+(n%cols)*SPACING)/2
            z=(z0+(i//cols)*SPACING+z0+(n//cols)*SPACING)/2
            edge_tests+=1
            if clear(x,z,radius) is None:bad.add(max(i,n))
    retained=component-bad
    if seed not in retained:seed=min(retained,key=lambda i:abs(i-seed))
    retained=connected_component(retained,cols,rows,seed)
    assert len(retained)>=20,(spec['id'],len(retained))
    h={k:v for k,v in spec.items() if k!='seed'}
    h.update(origin=[x0,z0],cols=cols,rows=rows,spacing=SPACING,clearance=radius,maxAnimalRadius=maximum_radius,staticRadiusMargin=round(radius-maximum_radius,5),cells=sorted(retained),heights={str(i):heights[i] for i in sorted(retained)},neighborMode='cardinal',maxStep=.13,style=spec['style'])
    h['center']=cell_position(h,seed)
    def nearest(target,excluded=(),distance=.9):
        candidates=[i for i in retained if all(math.dist(cell_position(h,i)[::2],p[::2])>=distance for p in excluded)]
        if not candidates:candidates=list(retained)
        i=min(candidates,key=lambda i:(cell_position(h,i)[0]-target[0])**2+(cell_position(h,i)[2]-target[1])**2)
        return cell_position(h,i)
    h['shelter']=nearest([x0+1.4,z0+1.4])
    h['drink']=nearest([x1-1.4,z0+1.5],[h['shelter']],1.8)
    h['food']=nearest([x1-1.4,z1-1.4],[h['shelter'],h['drink']],1.8)
    h['humanSpawn']=nearest([x0+2,(z0+z1)/2],[h['shelter'],h['drink'],h['food']],1.8)
    # Preserve authored ranges, anchors and public approach entry contract while
    # shrinking only animal-local cells according to final asset dimensions.
    previous=PREVIOUS_HABITATS.get(h['id'])
    if previous:
        assert previous['bounds']==h['bounds']
        for key in ['center','shelter','drink','food','humanSpawn']:
            p=previous[key];index=round((p[2]-z0)/SPACING)*cols+round((p[0]-x0)/SPACING)
            assert index in retained,(h['id'],'Existing anchor cannot fit final animal radius',key,p,radius)
            h[key]=p
    h['perches']=[]
    if spec['style']=='protected-aviary':
        if previous and previous.get('perches'):h['perches']=previous['perches']
        else:
            used=[]
            for target in [[x0+1.5,z0+1.5],[x1-1.5,z0+1.5],[x0+1.5,z1-1.5],[x1-1.5,z1-1.5]]:
                p=nearest(target,used+[h['shelter'],h['drink'],h['food']],.9);used.append(p)
                h['perches'].append([p[0],round(p[1]+1.25+.2*(len(used)%2),5),p[2]])
        h['flightBounds']=[x0+.8,z0+.8,x1-.8,z1-.8]
        h['flightRoutes']=[]
        for a in range(len(h['perches'])):
            for b in range(a+1,len(h['perches'])):
                pa,pb=h['perches'][a],h['perches'][b]
                ia=round((pa[2]-z0)/SPACING)*cols+round((pa[0]-x0)/SPACING)
                ib=round((pb[2]-z0)/SPACING)*cols+round((pb[0]-x0)/SPACING)
                q=deque([ia]);parent={ia:None}
                while q and ib not in parent:
                    i=q.popleft()
                    for n in [i-1,i+1,i-cols,i+cols]:
                        if n in retained and n not in parent and (abs(n-i)!=1 or n//cols==i//cols):parent[n]=i;q.append(n)
                assert ib in parent
                route=[];i=ib
                while i is not None:route.append(i);i=parent[i]
                route.reverse();points=[]
                for k,i in enumerate(route):
                    p=cell_position(h,i);p[1]=round(pa[1]+(pb[1]-pa[1])*k/max(1,len(route)-1),5);points.append(p)
                # Validate the entire swept bird volume at <=15cm intervals.
                samples=0
                for p1,p2 in zip(points,points[1:]):
                    n=max(1,math.ceil(math.dist(p1,p2)/.15))
                    for k in range(n+1):
                        p=[p1[j]+(p2[j]-p1[j])*k/n for j in range(3)]
                        assert solid_bvh.find_nearest(Vector((p[0],-p[2],p[1])),.18)[0] is None,(spec['id'],'flight collision',p)
                        samples+=1
                h['flightRoutes'].append({'from':a,'to':b,'radius':.18,'points':points,'geometrySamples':samples})
        h['flightPolicy']='Use authored bidirectional flightRoutes, preserving cardinal waypoints. Additional shortcuts need runtime obstacle raycasts; props require dynamic exclusion.'
        add_validated_bird_routes(h,retained)
    habitats.append(h)
    habitat_report.append(dict(id=h['id'],cells=len(retained),candidateCells=len(heights),discardedComponents=len(heights)-len(component),removedUnsafeEdges=len(bad),edgeSamples=edge_tests,finalMaximumAnimalRadius=maximum_radius,sampledClearance=radius,heightRange=[min(h['heights'].values()),max(h['heights'].values())],center=h['center']))
    print('HABITAT',h['id'],len(retained),h['center'],flush=True)

navigation={'version':'1.0','spacing':SPACING,'axes':'glTF Y up; north -Z','units':'metres','neighborMode':'cardinal','sourceBlendSha256':before,'scope':'Geometry-sampled local activity graphs plus public pedestrian graph; not a continuous whole-town navmesh. Runtime dynamic separation remains required.','habitats':habitats}
(ROOT/'reference').mkdir(exist_ok=True);(ROOT/'qa').mkdir(exist_ok=True)
if not PREVIOUS:
    (ROOT/'reference/navigation.json').write_text(json.dumps(navigation,ensure_ascii=False,separators=(',',':')))
    (ROOT/'reference/habitats.json').write_text(json.dumps({'version':'1.0','axes':navigation['axes'],'habitats':[{k:v for k,v in h.items() if k not in ['cells','heights']} for h in habitats]},ensure_ascii=False,indent=2))
print('LOCAL_GRAPHS_SAVED',flush=True)

# Public streets are sampled separately and joined to activity areas using
# real traversable lawn/paving connectors, never an across-town straight line.
ox,oz=-135.,-115.;cols,rows=601,451
global_heights={}
for row in range(rows):
    z=oz+row*SPACING
    for col in range(cols):
        x=ox+col*SPACING
        # Cheap centre support gate prevents perimeter/BVH checks over buildings.
        if ground_at(x,z,True) is None:continue
        h=clear(x,z,.42,True)
        if h is not None:global_heights[row*cols+col]=h
    if row%100==0:print('PUBLIC_ROW',row,len(global_heights),flush=True)

def global_index(x,z):
    return round((z-oz)/SPACING)*cols+round((x-ox)/SPACING)

public_only=set(global_heights)
connection_report=[]
for h in habitats:
    for local in h['cells']:
        p=cell_position(h,local);global_heights[global_index(p[0],p[2])]=p[1]
    # Flood fill up to 12m beyond the habitat bounding box over actual lawn,
    # connecting its safe human spawn to the nearest public graph node.
    start=global_index(h['humanSpawn'][0],h['humanSpawn'][2]);q=deque([start]);prev={start:None};target=None
    x0,z0,x1,z1=h['bounds'];expansion=12
    while q:
        i=q.popleft();x=ox+(i%cols)*SPACING;z=oz+(i//cols)*SPACING
        if i in public_only:target=i;break
        for dc,dr in [(1,0),(-1,0),(0,1),(0,-1)]:
            c,r=i%cols+dc,i//cols+dr;n=r*cols+c
            xx,zz=ox+c*SPACING,oz+r*SPACING
            if n in prev or not(0<=c<cols and 0<=r<rows and x0-expansion<=xx<=x1+expansion and z0-expansion<=zz<=z1+expansion):continue
            height=clear(xx,zz,.42)
            if height is None or clear((x+xx)/2,(z+zz)/2,.42) is None:continue
            prev[n]=i;q.append(n)
    if target is not None:
        path=[];i=target
        while i is not None:
            x,z=ox+(i%cols)*SPACING,oz+(i//cols)*SPACING
            global_heights[i]=clear(x,z,.42);path.append([round(x,5),global_heights[i],round(z,5)]);i=prev[i]
        path.reverse();h['publicEntry']=path[-1];h['humanApproach']=path
        connection_report.append({'id':h['id'],'connectedToPublic':True,'connectorCells':len(path),'publicEntry':path[-1]})
    else:
        nearest=min(public_only,key=lambda i:(ox+(i%cols)*SPACING-h['humanSpawn'][0])**2+(oz+(i//cols)*SPACING-h['humanSpawn'][2])**2)
        point=[ox+(nearest%cols)*SPACING,global_heights[nearest],oz+(nearest//cols)*SPACING]
        h['publicEntry']=point;h['humanApproach']=[]
        connection_report.append({'id':h['id'],'connectedToPublic':False,'nearestPublicEntry':point})
    print('CONNECT',h['id'],target is not None,flush=True)

# Cardinal edges are sampled independently of endpoint legality. Prune an
# endpoint when its edge crosses a thin obstacle, hole or excessive floor step.
human_edge_samples=0;unsafe_human=set()
for i,h0 in list(global_heights.items()):
    for n in [i+1,i+cols]:
        if n not in global_heights or (n==i+1 and n//cols!=i//cols):continue
        x1,z1=ox+(i%cols)*SPACING,oz+(i//cols)*SPACING
        x2,z2=ox+(n%cols)*SPACING,oz+(n//cols)*SPACING
        human_edge_samples+=1
        if abs(h0-global_heights[n])>.13 or clear((x1+x2)/2,(z1+z2)/2,.42) is None:unsafe_human.add(max(i,n))
for i in unsafe_human:global_heights.pop(i,None)

# The public mesh contains disconnected private/roof islands. Keep the largest
# ground route component and explicitly report each habitat's reachability.
remaining=set(global_heights);components=[]
while remaining:
    c=connected_component(remaining,cols,rows,next(iter(remaining)));components.append(c);remaining-=c
reachable=max(components,key=len)
for record,h in zip(connection_report,habitats):
    record['reachableFromMainPublicNetwork']=global_index(h['humanSpawn'][0],h['humanSpawn'][2]) in reachable
    h['humanNetworkReachable']=record['reachableFromMainPublicNetwork']
human={'origin':[ox,oz],'cols':cols,'rows':rows,'spacing':SPACING,'clearance':.42,'neighborMode':'cardinal','maxStep':.13,'cells':sorted(reachable),'heights':{str(i):global_heights[i] for i in sorted(reachable)},'scope':'Public paving plus validated habitat connectors; no roads traffic simulation, indoor or upper-floor navigation.'}
preserved_human=False
if PREVIOUS and PREVIOUS.get('humanNavigation'):
    human=PREVIOUS['humanNavigation'];preserved_human=True
    global_heights={int(i):v for i,v in human['heights'].items()};reachable=set(human['cells'])
    connection_report=[]
    for h in habitats:
        previous=PREVIOUS_HABITATS[h['id']]
        h['publicEntry']=previous['publicEntry'];h['humanApproach']=previous['humanApproach'];h['humanNetworkReachable']=global_index(h['humanSpawn'][0],h['humanSpawn'][2]) in reachable
        connection_report.append({'id':h['id'],'connectedToPublic':True,'connectorCells':len(h['humanApproach']),'publicEntry':h['publicEntry'],'reachableFromMainPublicNetwork':h['humanNetworkReachable'],'originalEntryPreserved':True})
navigation['humanNavigation']=human
navigation['habitats']=habitats
def atomic_json(path,value,compact=False):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':') if compact else None,indent=None if compact else 2));temporary.replace(path)
atomic_json(ROOT/'reference/navigation.json',navigation,True)
atomic_json(ROOT/'reference/habitats.json',{'version':'1.1','axes':navigation['axes'],'habitats':[{k:v for k,v in h.items() if k not in ['cells','heights']} for h in habitats]})

# Independent acceptance assertions on output representation and every local
# traversable edge, plus every anchor, not merely successful file creation.
checks=[]
def check(v,message):
    assert v,message
    checks.append(message)
ids=[pet for h in habitats for pet in h['petIds']]
roster=json.loads((ROOT.parents[2]/'pixel_town_assets/roster.json').read_text()) if (ROOT.parents[2]/'pixel_town_assets/roster.json').exists() else json.loads((ROOT.parents[3]/'pixel_town_assets/roster.json').read_text())
check(set(ids)=={p['id'] for p in roster['pets']} and len(ids)==20,'All 20 original animal identities assigned exactly once')
all_edge_samples=0
for h in habitats:
    cells=set(h['cells']);seed=h['cells'][0]
    check(h['maxAnimalRadius']<=h['clearance'],h['id']+' final animal body radius covered by sampled clearance')
    check(connected_component(cells,h['cols'],h['rows'],seed)==cells,h['id']+' single cardinal connected component')
    for label in ['center','shelter','drink','food','humanSpawn']:
        p=h[label];check(clear(p[0],p[2],h['clearance']) is not None,h['id']+' '+label+' grounded and body clear')
    for i in cells:
        p=cell_position(h,i)
        check(clear(p[0],p[2],h['clearance']) is not None,h['id']+' legal cell '+str(i))
        for n in [i+1,i+h['cols']]:
            if n not in cells or (n==i+1 and n//h['cols']!=i//h['cols']):continue
            p2=cell_position(h,n)
            check(abs(p[1]-p2[1])<=.13,h['id']+' step '+str(i)+'-'+str(n))
            check(clear((p[0]+p2[0])/2,(p[2]+p2[2])/2,h['clearance']) is not None,h['id']+' edge midpoint '+str(i)+'-'+str(n))
            all_edge_samples+=1
    check(h['humanNetworkReachable'],h['id']+' human spawn reaches main public graph')
    for p in h['humanApproach']:
        check(global_index(p[0],p[2]) in reachable,h['id']+' approach point retained in human graph')
    for p in h['perches']:
        check(solid_bvh.find_nearest(Vector((p[0],-p[2],p[1])),.18)[0] is None,h['id']+' perch volume clear')
check(hashlib.sha256(source.read_bytes()).hexdigest()==before,'Input Blender file unchanged')
if preserved_human:check(human==PREVIOUS['humanNavigation'],'Original public human graph preserved exactly')
check(len(human['cells'])>10000,'Public human graph contains substantial street network')
all_bird_routes=[p for h in habitats for key in ['flightRoutes','accessFlightRoutes'] for p in h.get(key,[])]
report={'status':'PASS','date':'2026-10-17','version':'1.1-final-animal-radii-and-bird-access','sourceBlendSha256':before,'sourceUnchanged':True,'spacing':SPACING,'minimumBodyClearance':.42,'finalAnimalManifestSha256':hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest(),'ponyClearance':next(h['clearance'] for h in habitats if h['id']=='g-pony-paddock'),'supportTriangles':len(support_faces),'publicSupportTriangles':len(public_faces),'solidTriangles':len(solid_faces),'habitats':habitat_report,'connections':connection_report,'allHabitatsMainNetworkReachable':all(r['reachableFromMainPublicNetwork'] for r in connection_report),'publicHumanGraphPreserved':preserved_human,'publicHumanGraphSha256':hashlib.sha256(json.dumps(human,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'publicCells':len(public_only),'humanReachableCells':len(reachable),'publicComponents':len(components),'localEdgeMidpointSamples':all_edge_samples,'humanEdgeMidpointSamples':human_edge_samples,'removedUnsafeHumanCells':len(unsafe_human),'flightRoutes':len(all_bird_routes),'birdRestSlots':sum(len(h.get('restSlots',[])) for h in habitats),'flightVolumeSamples':sum(p['geometrySamples'] for p in all_bird_routes),'birdRuntimePropsValidated':all(p.get('runtimePropsValidated') for p in all_bird_routes),'assertions':len(checks),'sampleMethod':'Final asset maximum animal radius plus >=3cm margin; actual upward ground triangles, perimeter support, 7 overlapping body-height sphere samples, four-neighbor connected components and half-edge samples. Bird flight body root+[0,.20,0] radius .18 at <=10cm samples, including declared canopy, perch posts and crossbars, aviary corner posts, bowls and resting pad.','limitations':['Sampled graph, not continuous navmesh or exhaustive collision proof.','Runtime must use cardinal cells or validate additional shortcuts; arbitrary diagonal/string-pulled paths can cross obstacles.','Ground-agent dynamic avoidance and additional props need runtime validation. Bird props must match shelterCanopy and flightNodes contract.','No indoor/stair routing, road traffic logic, true species welfare or social inference.'],'elapsedSeconds':round(time.time()-started,2),'geometryInventory':inventory,'supportObjects':dict(surface_names)}
atomic_json(ROOT/'qa/navigation-validation.json',report)
print('NAVIGATION_PASS',len(checks),len(human['cells']),round(time.time()-started,2),flush=True)
