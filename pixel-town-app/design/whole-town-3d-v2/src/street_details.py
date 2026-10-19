"""Street furniture and markings, all in metre-scale shared town collections."""
import bpy, math
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def build(h, roads, plots, portals, shore):
    box,cyl,beam=h.box,h.cyl,h.beam
    data={'lamps':[],'benches':[],'crosswalks':[],'signalCrossings':[],'utilityPoles':[],'wireSpans':[],'bins':[],'wayfinding':[],'bollards':[],'drainage':[],'arrows':[],'junctions':[]}
    # Use the original road top: material replacement, not a second overlapping surface.
    for o in h.C['T_Paths'].objects:
        x,y,z=o.location
        if x<-127.49 or y>107.49 or y<-103.49 or abs(x+46.25)<2.751 or abs(x-46.875)<2.751 or abs(y-35)<3.001 or abs(y+36.25)<3.001:
            o.data=o.data.copy();o.data.materials.clear();o.data.materials.append(h.M['asphalt'])
    for mat,strength in [('lamp',1.1),('signalRed',.7),('signalGreen',.6)]:
        bs=h.M[mat].node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=h.M[mat].diffuse_color;bs.inputs['Emission Strength'].default_value=strength

    def rect(n,x,y,w,d,mat,c,z=.098):return box(n,x,y,z,w,d,.008,mat,c)
    def roadpaint(x,y,w,d,mat='paint'):return rect('Road marking',x,y,w,d,mat,'T_Road_Markings')
    # Zebra directions refer to pedestrian movement. Paired stop bars keep traffic before the crossing.
    def crossing(x,y,axis,signal=False,width=5):
        data['crosswalks'].append({'center':[x,y],'walkAxis':axis,'roadWidth':width,'width':2.8,'signal':signal})
        # Individual white bars run parallel to vehicle travel; their array spans the road.
        stripe_count=math.floor((width-.4)/.65)
        for i in range(stripe_count):
            offset=(i-(stripe_count-1)/2)*.65
            rect('Zebra white stripe',x+offset if axis=='x' else x,y if axis=='x' else y+offset,.40 if axis=='x' else 2.8,2.8 if axis=='x' else .40,'paint','T_Crosswalks')
        data['crosswalks'][-1].update({'stripeCount':stripe_count,'stripeLongAxis':'y' if axis=='x' else 'x','stripeLength':2.8,'stripeWidth':.4})
        for side in [-1,1]:
            roadpaint(x+side*2.5 if axis=='y' else x+side*1.2,y+side*1.2 if axis=='y' else y-side*2.5,.18 if axis=='y' else 2.05,2.05 if axis=='y' else .18)
            # Tactile waiting panel is outside the vehicle strip, with modelled ribs.
            px=x+side*(width/2+.4) if axis=='x' else x;py=y if axis=='x' else y+side*(width/2+.4)
            rect('Crossing waiting pad',px,py,1 if axis=='x' else 2.8,2.8 if axis=='x' else 1,'path','T_Rest_Paths',.082)
            for j in range(6):
                q=(j-2.5)*.22
                rect('Tactile rib',px if axis=='x' else px+q,py+q if axis=='x' else py,.5 if axis=='x' else .055,.055 if axis=='x' else .5,'yellowline','T_Crosswalks',.094)
        if signal:
            data['signalCrossings'].append({'center':[x,y],'state':'vehicle red; pedestrian green; static'})
            for side in [-1,1]:
                # Both vehicles stop; pedestrian heads face across the road, away from each pole.
                px=x+side*3.15 if axis=='x' else x+side*2.9
                py=y+side*2.9 if axis=='x' else y+side*3.15
                cyl('Signal base',px,py,.14,.22,.28,'stone','T_Signals')
                cyl('Signal post',px,py,1.72,.065,3.3,'darkgreen','T_Signals')
                box('Traffic signal housing',px,py,3.0,.35,.28,.95,'dark','T_Signals')
                for dz,mat in [(.28,'signalRed'),(0,'signalOff'),(-.28,'signalOff')]:
                    if axis=='x':
                        o=cyl('Traffic lens',px,py-side*.16,3+dz,.105,.035,mat,'T_Signals',12);o.rotation_euler.x=math.pi/2
                    else:
                        o=cyl('Traffic lens',px-side*.2,py,3+dz,.105,.035,mat,'T_Signals',12);o.rotation_euler.y=math.pi/2
                box('Pedestrian signal housing',px,py,2.15,.26,.25,.46,'dark','T_Signals')
                if axis=='x':
                    o=cyl('Walk green lens',px-side*.15,py,2.15,.085,.03,'signalGreen','T_Signals',12);o.rotation_euler.y=math.pi/2
                else:
                    o=cyl('Walk green lens',px,py-side*.15,2.15,.085,.03,'signalGreen','T_Signals',12);o.rotation_euler.x=math.pi/2
                box('Pedestrian push button',px,py-.1,1.05,.12,.08,.18,'gold','T_Signals')
    for y in [83.75,35,-2.5,-36.25,-97.5]:crossing(-130,y,'x',y==-2.5)
    for x in [-87.5,-41.25,-11.75,15.5,51.875,78.125]:crossing(x,110,'y')
    for x in [-90.5,-41.25,0,51.875,78.125]:crossing(x,-106,'y',x==51.875)
    def nearcross(x,y,r=4):return any(abs(x-a['center'][0])<r and abs(y-a['center'][1])<r for a in data['crosswalks'])
    # Four main junctions: crossings on each arm and signals at four outside corners.
    for x in [-46.25,46.875]:
        for y in [35,-36.25]:
            data['junctions'].append([x,y])
            for side in [-1,1]:
                crossing(x,y+side*5,'x',width=5.5)
                crossing(x+side*5,y,'y',width=6)
            for sx,sy in [(-1,-1),(-1,1),(1,1),(1,-1)]:
                px,py=x+sx*3.5,y+sy*3.8
                cyl('Junction signal base',px,py,.14,.20,.28,'stone','T_Signals')
                cyl('Junction signal post',px,py,1.8,.065,3.5,'darkgreen','T_Signals')
                box('Junction head',px,py,3.10,.35,.30,.95,'dark','T_Signals')
                # Two faces serve the two perpendicular approaches; static vehicle red.
                for dz,mat in [(.28,'signalRed'),(0,'signalOff'),(-.28,'signalOff')]:
                    o=cyl('Junction north south lens',px,py-sy*.17,3.1+dz,.105,.03,mat,'T_Signals',12);o.rotation_euler.x=math.pi/2
                    o=cyl('Junction east west lens',px-sx*.19,py,3.1+dz,.105,.03,mat,'T_Signals',12);o.rotation_euler.y=math.pi/2
                box('Pedestrian junction head',px,py,2.1,.26,.26,.44,'dark','T_Signals')
                o=cyl('Pedestrian green lens',px,py-sy*.15,2.1,.08,.03,'signalGreen','T_Signals',12);o.rotation_euler.x=math.pi/2
    # Direct building-to-building pedestrian links across the main streets.
    for y,xs in [(35,[-88,0,78.125]),(-36.25,[-89.75,0,83.625])]:
        for x in xs:crossing(x,y,'y',width=6)
    for x,ys in [(-46.25,[-97.5,-73.25,-2.5,68.75,83.75]),(46.875,[-74,-62,-1.25,68.75,83.75])]:
        for y in ys:crossing(x,y,'x',width=5.5)
    def junction_gap(x,y):return any(abs(x-a)<7 and abs(y-b)<7 for a,b in data['junctions'])
    # All main routes have explicit centre and edge lines; crossing zones stay clear.
    for x,width in [(-130,5),(-46.25,5.5),(46.875,5.5)]:
        for y in range(-101,107,5):
            if not nearcross(x,y) and not junction_gap(x,y):roadpaint(x,y,.16,2.4,'yellowline')
        for y in range(-101,107,3):
            if not nearcross(x,y,2.5) and not junction_gap(x,y):
                for side in [-1,1]:roadpaint(x+side*(width/2-.25),y,.12,2)
    for y,width in [(-106,5),(110,5),(35,6),(-36.25,6)]:
        for x in range(-121,99,5):
            if not nearcross(x,y) and not junction_gap(x,y):roadpaint(x,y,2.4,.16,'yellowline')
        for x in range(-122,99,3):
            if not nearcross(x,y,2.5) and not junction_gap(x,y):
                for side in [-1,1]:roadpaint(x,y+side*(width/2-.25),2,.12)
    def arrow(x,y,angle):
        # A single seven-vertex silhouette, lifted 9 mm above the pavement.
        points=[(-.12,-.85),(.12,-.85),(.12,.22),(.40,.22),(0,.90),(-.40,.22),(-.12,.22)]
        vs=[(x+a*math.cos(angle)-b*math.sin(angle),y+a*math.sin(angle)+b*math.cos(angle),.108) for a,b in points]
        me=bpy.data.meshes.new('Direction arrow');me.from_pydata(vs,[],[tuple(range(7))]);me.materials.append(h.M['paint']);me.update();o=bpy.data.objects.new('Direction arrow',me);h.col('T_Road_Markings').objects.link(o);data['arrows'].append({'center':[x,y],'angle':angle})
    for x in [-130,-46.25,46.875]:
        for y in [-58,12,62]:arrow(x+1.25,y,0);arrow(x-1.25,y,math.pi)
    for y in [-106,110,35,-36.25]:
        for x in [-105,-68,-25,28,85]:
            if not nearcross(x,y,4):arrow(x,y-1.25,-math.pi/2);arrow(x,y+1.25,math.pi/2)
    arrow(98.7,-88,0);arrow(102.9,-88,math.pi)
    # Low street lanterns, outside both the source plots and the connecting road rectangles.
    def safe(x,y,r=.35):
        return not any(a-r<x<c+r and b-r<y<d+r for a,b,c,d in roads+plots) and all(math.hypot(x-p['point'][0],y-p['point'][1])>1.4 for p in portals)
    def lamp(x,y,angle=0,height=4.7):
        if not safe(x,y,.24):return
        data['lamps'].append({'base':[x,y,0],'height':height})
        cyl('Lamp plinth',x,y,.12,.20,.24,'stone','T_Street_Lamps')
        cyl('Lamp shaft',x,y,height/2,.065,height,'darkgreen','T_Street_Lamps',12)
        cyl('Lamp foot collar',x,y,.4,.10,.36,'gold','T_Street_Lamps',12)
        dx,dy=.58*math.cos(angle),.58*math.sin(angle)
        beam('Lamp curved arm', (x,y,height-.18),(x+dx,y+dy,height),.065,'darkgreen','T_Street_Lamps')
        cyl('Lantern cap',x+dx,y+dy,height-.08,.27,.12,'darkgreen','T_Street_Lamps',12)
        cyl('Warm lantern diffuser',x+dx,y+dy,height-.29,.17,.28,'lamp','T_Lamp_Glow',12)
        cyl('Lantern base',x+dx,y+dy,height-.46,.22,.07,'darkgreen','T_Street_Lamps',12)
        for a in [0,math.pi/2,math.pi,math.pi*1.5]:beam('Lantern frame',(x+dx+.18*math.cos(a),y+dy+.18*math.sin(a),height-.43),(x+dx+.18*math.cos(a),y+dy+.18*math.sin(a),height-.14),.025,'darkgreen','T_Street_Lamps')
    for x in [-117,-99,-77,-57,-30,-10,12,33,60,81,97]:
        lamp(x,38.3,-math.pi/2);lamp(x,-39.5,math.pi/2)
    for y in [-88,-57,-16,16,54,92]:lamp(-43.25,y,math.pi);lamp(49.9,y,math.pi)
    for x in [-115,-68,-28,34,90]:lamp(x,106.3,math.pi/2);lamp(x,-102.1,-math.pi/2)
    for y in [-82,-52,12,60,96]:lamp(-126.4,y,math.pi)
    for y in [-92,-59,59,92]:lamp(shore(y)-5.0,y,0,3.7)

    def bench(x,y,angle=0):
        data['benches'].append({'center':[x,y],'angle':angle,'length':1.9})
        def b(n,dx,dy,z,w,d,hgt,mat):
            o=box(n,x+dx*math.cos(angle)-dy*math.sin(angle),y+dx*math.sin(angle)+dy*math.cos(angle),z,w,d,hgt,mat,'T_Benches');o.rotation_euler.z=angle
        for dx in [-.70,.70]:
            b('Bench leg',dx,0,.28,.085,.48,.40,'darkgreen');b('Bench arm',dx,0,.76,.055,.58,.055,'darkgreen');b('Bench arm support',dx,.15,.64,.045,.045,.28,'darkgreen')
        for dy in [-.22,-.11,0,.11,.22]:b('Bench seat slat',0,dy,.53,1.9,.085,.07,'wood')
        for z in [.75,.88,1.01]:b('Bench back slat',0,.27,z,1.9,.065,.09,'wood')
        for dx in [-.70,.70]:b('Bench back support',dx,.29,.79,.045,.045,.55,'darkgreen')
    def binpair(x,y):
        data['bins'].append([x,y])
        for dx,mat in [(-.24,'sage'),(.24,'blue')]:
            box('Sorting bin shell',x+dx,y,.5,.4,.43,.80,mat,'T_Bins')
            box('Bin top',x+dx,y,.92,.44,.47,.07,'darkgreen','T_Bins')
            box('Bin opening',x+dx,y-.223,.78,.25,.025,.12,'dark','T_Bins')
            box('Bin label',x+dx,y-.224,.48,.19,.018,.14,'white','T_Bins')
    for y in [40.0,-41.2]:
        for x in [-108,-68,-25,25,64,89]:
            # Pads connect directly to the street. Seat back faces the adjacent district.
            edge=38 if y>0 else -39.25;outer=y+.65 if y>0 else y-.65
            rect('Street rest bay',x,(edge+outer)/2,4.3,abs(outer-edge),'path','T_Rest_Paths',.082)
            bench(x,y,0 if y>0 else math.pi)
            if x in [-108,-25,64]:binpair(x+1.55,y)
    for y in [-85,-62,62,86]:
        x=shore(y)-5.3
        rect('Riverside rest bay',x+.55,y,3.3,3.5,'path','T_Rest_Paths',.082)
        bench(x-.3,y,math.pi/2)
    # Wayfinding is concentrated at corridor corners, readable at street scale.
    for x,y,label in [(-40,39.4,'公共服务  ↑'),(40,39.4,'河岸公园  →'),(-40,-41.2,'手作工坊  ↑'),(40,-41.2,'商店 · 旅店  ↓'),(-118,-41.2,'田园温室  ↓'),(91,39.4,'河岸步道  →')]:
        data['wayfinding'].append({'position':[x,y],'label':label})
        cyl('Wayfinding post',x,y,1.28,.055,2.56,'darkgreen','T_Wayfinding')
        box('Wayfinding sign',x,y,2.25,1.65,.10,.42,'darkgreen','T_Wayfinding')
        h.text('Direction label',label,x,y-.058,2.25,.20,'white','T_Wayfinding')
    # The timber bridges remain slow pedestrian crossings; main street mouths stay open.
    for x in [100.1,149.2]:
        for y in [35,-36.25]:
            for dy in [-1.65,1.65]:
                py=y+dy;data['bollards'].append([x,py]);cyl('Bridge bollard',x,py,.66,.09,.75,'darkgreen','T_Bollards',12);cyl('Bollard reflective band',x,py,.92,.094,.07,'paint','T_Bollards',12)
    # Thin grout joints on the actual existing district paving, never on grass or buildings.
    joint_vs=[];joint_fs=[]
    for obj in [o for o in bpy.context.scene.objects if o.type=='MESH' and o.name[0] in 'ABCDEFGHI' and (o.name.endswith('__Paths') or o.name=='E__Paving')]:
        me=obj.data;me.calc_loop_triangles();pv=[];pf=[]
        for t in me.loop_triangles:
            points=[obj.matrix_world@me.vertices[i].co for i in t.vertices]
            if min(p.z for p in points)<.03 or max(p.z for p in points)>.18 or (points[1]-points[0]).cross(points[2]-points[0]).z<=0:continue
            off=len(pv);pv.extend(points);pf.append((off,off+1,off+2))
        if not pf:continue
        surface=BVHTree.FromPolygons(pv,pf,all_triangles=True)
        def hit(x,y):
            p=surface.ray_cast(Vector((x,y,.25)),Vector((0,0,-1)),.24)[0]
            return p.z if p is not None else None
        x0,x1=min(p.x for p in pv),max(p.x for p in pv);y0,y1=min(p.y for p in pv),max(p.y for p in pv)
        for axis in [0,1]:
            fixed0,fixed1=(x0,x1) if axis==0 else (y0,y1);move0,move1=(y0,y1) if axis==0 else (x0,x1);spacing=2 if axis==0 else 1
            for k in range(math.ceil(fixed0/spacing),math.floor(fixed1/spacing)+1):
                fixed=k*spacing;run=None;last=None;level=None
                def emit(a,b,z):
                    if a is None or b-a<.3:return
                    coords=[(fixed-.009,a),(fixed+.009,a),(fixed+.009,b),(fixed-.009,b)] if axis==0 else [(a,fixed-.009),(b,fixed-.009),(b,fixed+.009),(a,fixed+.009)]
                    off=len(joint_vs);joint_vs.extend((x,y,z+.003) for x,y in coords);joint_fs.append((off,off+1,off+2,off+3))
                for step in range(math.floor((move1-move0)/.4)+1):
                    pos=move0+step*.4;x,y=(fixed,pos) if axis==0 else (pos,fixed);z=hit(x,y)
                    if z is not None and (level is None or abs(z-level)<.002):
                        if run is None:run=pos;level=z
                        last=pos
                    else:
                        emit(run,last,level);run=None;last=None;level=None
                emit(run,last,level)
    me=bpy.data.meshes.new('District stone grout');me.from_pydata(joint_vs,[],joint_fs);me.materials.append(h.M['joint']);me.update();o=bpy.data.objects.new('District stone grout',me);h.col('T_Stone_Joints').objects.link(o)
    # Utility line stays on the outer west and north verges, with three sagging conductors.
    poles=[(-133.6,y) for y in [-105,-78,-51,-24,3,30,57,88,113.6]]+[(x,113.6) for x in [-106,-78,-50,-22,6,34,62,90]]
    for i,(x,y) in enumerate(poles):
        data['utilityPoles'].append([x,y,7.3]);cyl('Utility pole',x,y,3.65,.12,7.3,'wood','T_Utilities',12);cyl('Utility pole shoe',x,y,.35,.16,.70,'darkgreen','T_Utilities',12)
        west=i<9
        box('Utility crossarm',x,y,7.15,1.6 if west else .12,.12 if west else 1.6,.11,'darkgreen','T_Utilities')
        for d in [-.65,0,.65]:cyl('Ceramic insulator',x+d if west else x,y if west else y+d,7.35,.065,.25,'white','T_Utilities',10)
        if i in [3,12]:box('Pole service cabinet',x+.23,y,2.9,.38,.45,.65,'metal','T_Utilities')
    for i,(a,b) in enumerate(zip(poles,poles[1:])):
        for offset in [-.65,0,.65]:
            ax,ay=a;bx,by=b
            if i<8:ax+=offset
            else:ay+=offset
            if i+1<9:bx+=offset
            else:by+=offset
            length=math.hypot(bx-ax,by-ay);sag=min(.70,length*.025);data['wireSpans'].append({'a':[ax,ay,7.48],'b':[bx,by,7.48],'sag':sag,'minimumZ':7.48-sag})
            pts=[(ax+(bx-ax)*j/16,ay+(by-ay)*j/16,7.48-4*sag*(j/16)*(1-j/16)) for j in range(17)]
            for aa,bb in zip(pts,pts[1:]):beam('Sagging utility cable',aa,bb,.025,'wire','T_Wires')
    # Flush inspection covers and drain grates give the vehicle street a useful surface scale.
    for x,y in [(-130,62),(-130,-55),(-68,110),(38,110),(-65,-106),(20,-106),(91,-106)]:
        data['drainage'].append([x,y]);cyl('Inspection cover',x,y,.10,.32,.012,'dark','T_Drainage',16)
        for dx in [-.12,0,.12]:rect('Cover groove',x+dx,y,.025,.42,'metal','T_Drainage',.109)
    for x in [-110,-70,-20,25,67,94]:
        for y in [-108.2,112.2]:
            rect('Storm drain frame',x,y,.65,.36,'dark','T_Drainage',.104)
            for j in range(6):rect('Storm drain slot',x-.25+j*.1,y,.035,.28,'metal','T_Drainage',.112)
    data['counts']={k:len(v) for k,v in data.items()}
    data['counts']['stoneJointSegments']=len(joint_fs)
    data['notes']='Static low-speed street design. Main streets use asphalt, 5.5m north-south and 6m east-west; district paths use stone joints; bridges remain pedestrian; signal heads are fixed to vehicle red/pedestrian green.'
    return data
