import bpy,math,json,hashlib,random,bmesh
from pathlib import Path
from mathutils import Vector,Quaternion
BASE=Path(__file__).resolve().parents[1]
ROSTER=json.loads((BASE.parents[2]/'pixel_town_assets/roster.json').read_text())['pets'] if False else json.loads(Path('/Users/summerwindy/Desktop/AI Chat/pixel_town_assets/roster.json').read_text())['pets']
random.seed(39)
MAN=[];REPORT=[]

def mat(name,col):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col[:3],1);m.use_nodes=True;m.node_tree.nodes.clear();p=m.node_tree.nodes.new('ShaderNodeBsdfPrincipled');out=m.node_tree.nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(p.outputs['BSDF'],out.inputs['Surface']);p.inputs['Base Color'].default_value=(*col[:3],1);p.inputs['Metallic'].default_value=0;p.inputs['Roughness'].default_value=.83;return m

def reset():bpy.ops.wm.read_factory_settings(use_empty=True)
def meshpart(name,loc,scale,material,bone=None,kind='UV',rot=None):
 if kind=='ICO':bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=loc)
 elif kind=='CONE':bpy.ops.mesh.primitive_cone_add(vertices=10,radius1=1,radius2=.025,depth=2,location=loc)
 else:bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,radius=1,location=loc)
 o=bpy.context.object;o.name=name;o.scale=scale
 if rot:o.rotation_euler=rot
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 if material:o.data.materials.append(material)
 for p in o.data.polygons:p.use_smooth=True
 if bone:o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE')
 return o

def segment(name,a,b,r1,r2,ma,bone):
 d=Vector(b)-Vector(a);mid=(Vector(a)+Vector(b))/2
 bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=r1,radius2=r2,depth=d.length,location=mid)
 o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);o.data.materials.append(ma)
 for p in o.data.polygons:p.use_smooth=True
 o.vertex_groups.new(name=bone).add(list(range(len(o.data.vertices))),1,'REPLACE');return o

def rig_from_defs(defs):
 ar=bpy.data.armatures.new('AnimalSkeleton');ob=bpy.data.objects.new('AnimalRig',ar);bpy.context.collection.objects.link(ob);bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
 for n,a,b,pa in defs:
  e=ar.edit_bones.new(n);e.head=a;e.tail=b
  if pa:e.parent=ar.edit_bones[pa]
 bpy.ops.object.mode_set(mode='OBJECT');ob.select_set(False);return ob

def skin_parts(parts,rig):
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name='AnimalSurface';m=o.modifiers.new('Bone articulation','ARMATURE');m.object=rig;o.parent=rig;return o

def rot_world(pb,axis,angle):
 ax=pb.bone.matrix_local.to_quaternion().inverted()@(pb.id_data.matrix_world.to_3x3().inverted()@Vector(axis)).normalized();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(ax,angle)
def translate_world(pb,v):pb.location=pb.bone.matrix_local.to_quaternion().inverted()@(pb.id_data.matrix_world.to_3x3().inverted()@Vector(v))
def action(rig,name,pose,frames=48):
 rig.animation_data_create();rig.animation_data.action=None
 ac=bpy.data.actions.new(name);rig.animation_data.action=ac
 for f in range(0,frames+1,4):
  for b in rig.pose.bones:b.location=(0,0,0);b.rotation_mode='QUATERNION';b.rotation_quaternion=(1,0,0,0);b.scale=(1,1,1)
  pose(f/frames,rig)
  for b in rig.pose.bones:
   b.keyframe_insert('location',frame=f);b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('scale',frame=f)
 ac.use_fake_user=True;rig.animation_data.action=None;return ac

def native_actions(rig,kind):
 bones=set(rig.pose.bones.keys());amp=.07 if kind=='tortoise' else .22
 def pose(t,r,name):
  s=math.sin(t*2*math.pi);c=math.cos(t*2*math.pi)
  def rr(n,ax,a):
   if n in bones:rot_world(r.pose.bones[n],ax,a)
  def tr(n,v):
   if n in bones:translate_world(r.pose.bones[n],v)
  rr('head',(1,0,0),.04*s);rr('neck',(0,0,1),.03*s)
  if name in ('Walk','Run','Hop'):
   speed=2 if name=='Run' else 1;ang=t*2*math.pi*speed
   for side in ['L','R']:
    phase=0 if side=='L' else math.pi
    for limb in ['front','back']:
     phase2=phase+(math.pi if limb=='back' else 0);u=math.sin(ang+phase2)
     if name=='Hop':u=math.sin(ang) if limb=='front' else -math.sin(ang)
     rr(limb+'_upper.'+side,(1,0,0),amp*u*(1.5 if name in ('Run','Hop') else 1))
     rr(limb+'_lower.'+side,(1,0,0),-max(0,u)*amp*1.3)
   tr('body',(0,0,(.015 if kind!='tortoise' else .0015)*abs(s)))
   if name=='Hop':tr('body',(0,0,.065*max(0,s)));rr('body',(1,0,0),.12*s)
   if kind=='bird':
    for side,ph in [('L',0),('R',math.pi)]:rr('leg.'+side,(1,0,0),.35*math.sin(ang+ph))
  if name in ('Idle','Observe','Sniff','Groom','Wag'):
   rr('head',(0,0,1),(.17 if name=='Observe' else .045)*s)
   rr('tail',(0,0,1),(.55 if name=='Wag' else .08)*s)
   if name=='Sniff':rr('neck',(1,0,0),-.20+.08*s)
   if name=='Groom':rr('head',(0,1,0),.35+.15*s);rr('front_upper.L',(1,0,0),.7+.15*c)
   if kind=='bird':rr('head',(0,0,1),.22*s)
   for side in ['L','R']:rr('ear.'+side,(0,1,0),.08*s)
  if name in ('Eat','Drink'):
   rr('neck',(1,0,0),-.35+.06*s);rr('head',(1,0,0),-.3+.10*math.sin(t*8*math.pi));rr('jaw',(1,0,0),.15+.12*math.sin(t*8*math.pi))
  if name=='Rest':
   if kind in ('rabbit','guineapig'):
    tr('body',(0,0,-.012+.001*s));rr('front_upper.L',(1,0,0),.20);rr('front_upper.R',(1,0,0),.20);rr('front_lower.L',(1,0,0),-.20);rr('front_lower.R',(1,0,0),-.20);rr('back_upper.L',(1,0,0),-.15);rr('back_upper.R',(1,0,0),-.15);rr('back_lower.L',(1,0,0),.16);rr('back_lower.R',(1,0,0),.16)
   elif kind=='bird':tr('body',(0,0,-.012+.001*s));rr('head',(0,0,1),.6)
   elif kind=='tortoise':tr('neck',(0,.018,0));rr('head',(1,0,0),.1)
   rr('head',(1,0,0),-.13+.018*s)
  if name=='Fly':
   for side,sign in [('L',-1),('R',1)]:
    rr('wing.'+side,(0,1,0),sign*(.1+.65*math.sin(t*4*math.pi)));pb=r.pose.bones['wing.'+side];ax=pb.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,1));pb.rotation_quaternion=pb.rotation_quaternion@Quaternion(ax,-sign*1.1)
    rr('wingtip.'+side,(0,1,0),sign*(.2+.45*math.sin(t*4*math.pi+.5)))
    rr('leg.'+side,(1,0,0),-.8)
   rr('tail',(1,0,0),.15*s);rr('body',(1,0,0),.12)
  if name=='Hide':tr('neck',(0,.04*(.5+.5*s),-.006));rr('head',(1,0,0),.2)
 names=['Idle','Walk','Eat','Drink','Rest','Observe']
 if kind in ('rabbit','guineapig'):names+=['Run','Sniff','Groom']
 if kind=='rabbit':names+=['Hop']
 if kind=='bird':names+=['Hop','Fly','Groom']
 if kind=='tortoise':names.remove('Drink');names+=['Hide']
 return [action(rig,n,lambda t,r,n=n:pose(t,r,n),48 if n not in ('Idle','Rest') else 72) for n in names]

def create_original(p):
 reset();a=p['animal'];kind='bird' if a['species']=='鸟' else ('rabbit' if a['species']=='兔' else ('guineapig' if a['species']=='豚鼠' else 'tortoise'))
 parts=[];defs=[]
 def bone(n,h,t,pa='body'):defs.append((n,h,t,pa))
 def ell(n,l,s,m,b='body',k='UV',r=None):parts.append(meshpart(n,l,s,m,b,k,r))
 def seg(n,h,t,r1,r2,m,b):parts.append(segment(n,h,t,r1,r2,m,b))
 black=mat('Obsidian eyes',(.014,.019,.018));shine=mat('Eye glint',(.93,.97,1));pink=mat('Warm nose and inner ear',(.65,.32,.29))
 if kind=='bird':
  blue='blue' in p['id'];cock='cockatiel' in p['id'];canary='canary' in p['id']
  bodycol=(.12,.48,.72) if blue else ((.43,.47,.49) if cock else ((.94,.73,.05) if canary else (.30,.61,.13)))
  headcol=(.85,.89,.86) if blue else ((.97,.78,.18) if cock or not canary else (.98,.82,.10))
  ma=mat('Species body plumage',bodycol);headmat=mat('Head plumage',headcol);wingma=mat('Wing feathers',tuple(v*.72 for v in bodycol));tip=mat('Flight feather edges',(.15,.20,.21) if not canary else (.65,.48,.06));beak=mat('Horn beak',(.75,.55,.27));feet=mat('Zygodactyl toes',(.52,.40,.37));cheek=mat('Cockatiel orange cheek',(.98,.31,.04))
  sc=1.1 if cock else (.86 if canary else 1)
  bone('body',(0,0,.09),(0,0,.15),None);bone('neck',(0,-.025,.14),(0,-.045,.175));bone('head',(0,-.045,.175),(0,-.048,.20),'neck');bone('jaw',(0,-.07,.175),(0,-.086,.17),'head');bone('tail',(0,.027,.10),(0,.12,.055))
  ell('Tapered feathered breast',(0,.0,.115),(.037,.049,.062),ma);ell('Round head',(0,-.035,.18),(.030,.032,.032),headmat,'head');ell('Beak',(0,-.068,.177),(.010,.016,.014),beak,'jaw','CONE',(math.pi/2,0,0));ell('Cere',(0,-.064,.187),(.009,.004,.004),mat('Cere',(.27,.50,.67) if not cock else (.6,.6,.6)),'head')
  for side,sign in [('L',-1),('R',1)]:
   bone('wing.'+side,(sign*.026,0,.145),(sign*.055,.023,.11));bone('wingtip.'+side,(sign*.055,.023,.11),(sign*.062,.06,.075),'wing.'+side)
   ell('Folded primary wing '+side,(sign*.033,.016,.118),(.015,.038,.042),wingma,'wing.'+side,r=(.25,sign*.15,sign*-.12))
   for j in range(5):
    ell('Primary feather '+side+str(j),(sign*(.035+j*.004),.04+j*.004,.092-j*.004),(.0045,.032,.012),tip if j%2==0 else wingma,'wingtip.'+side,r=(.3,0,sign*-.12))
   for j in range(4):ell('Wing scallop '+side+str(j),(sign*.046,.004+j*.012,.14-j*.011),(.0035,.014,.003),tip if not canary else wingma,'wing.'+side)
   ell('Eye '+side,(sign*.026,-.051,.188),(.0045,.0045,.005),black,'head');ell('Eye glint '+side,(sign*.028,-.054,.190),(.0013,.0013,.0013),shine,'head')
   if cock:ell('Orange cheek '+side,(sign*.026,-.047,.175),(.0025,.009,.008),cheek,'head')
   bone('leg.'+side,(sign*.014,.002,.073),(sign*.014,-.003,.022));bone('foot.'+side,(sign*.014,-.003,.022),(sign*.014,-.028,.009),'leg.'+side)
   seg('Tarsus '+side,(sign*.014,.002,.068),(sign*.014,-.003,.014),.0032,.0028,feet,'leg.'+side)
   for j in [-1,0,1]:seg('Front toe '+side+str(j),(sign*.014,-.003,.009),(sign*.014+j*.008,-.027,.003),.002,.0015,feet,'foot.'+side)
   seg('Rear toe '+side,(sign*.014,.001,.009),(sign*.014,.021,.003),.002,.0014,feet,'foot.'+side)
  for j in range(5):ell('Long tail feather '+str(j),((j-2)*.007,.09+abs(j-2)*-.004,.065),(.005,.06,.008),tip if not canary else ma,'tail',r=(-.38,0,0))
  if cock:
   for j in range(5):ell('Expressive crest '+str(j),((j-2)*.004,-.024,.223+(.008 if j==2 else 0)),(.0025,.006,.028),headmat,'head',r=(-.35+(j-2)*.08,0,0))
  rig=rig_from_defs(defs);skin_parts(parts,rig)
  if sc!=1:
   root=bpy.data.objects.new('SpeciesScale',None);bpy.context.collection.objects.link(root);rig.parent=root;root.scale=(sc,sc,sc)
 elif kind in ('rabbit','guineapig'):
  rabbit=kind=='rabbit';lop='lop' in p['id'];gp=not rabbit
  ma=mat('Fur base',(.66,.69,.69) if lop else ((.12,.13,.14) if rabbit else (.54,.28,.12)));white=mat('Clean white saddle',(.87,.88,.83));dark=mat('Dark fur',(.08,.075,.064));brown=mat('Rosette tan',(.63,.34,.13))
  bl=.19 if rabbit else .14;bh=.15 if rabbit else .10;hw=.066 if rabbit else .05
  bone('body',(0,0,bh*.7),(0,0,bh),None);bone('neck',(0,-bl*.45,bh),(0,-bl*.66,bh*1.10));bone('head',(0,-bl*.66,bh*1.10),(0,-bl*.88,bh*1.15),'neck');bone('jaw',(0,-bl*.87,bh*1.0),(0,-bl*.94,bh*.97),'head');bone('tail',(0,bl*.75,bh*.65),(0,bl*.92,bh*.7))
  ell('Pear-shaped haunch',(0,bl*.20,bh*.71),(.081 if rabbit else .067,bl*.68,bh*.72),ma);ell('Chest',(0,-bl*.35,bh*.70),(.063 if rabbit else .06,bl*.48,bh*.60),white if not gp else ma);ell('Soft muzzle head',(0,-bl*.65,bh*1.03),(hw,bl*.43,bh*.49),ma,'head');ell('Muzzle white',(0,-bl*.91,bh*.96),(hw*.61,bl*.15,bh*.24),white,'jaw');ell('Small split nose',(0,-bl*1.044,bh*1.02),(.008,.005,.006),pink,'head');ell('Tail',(0,bl*.82,bh*.66),(.026,.025,.025),white,'tail')
  for side,sign in [('L',-1),('R',1)]:
   for limb,yy in [('front',-bl*.48),('back',bl*.48)]:
    x=sign*(.042 if limb=='front' else .06);hip=(x,yy,bh*.61);knee=(x,yy+(.016 if limb=='back' else 0),.04);foot=(x,yy-.04,.017)
    bone(limb+'_upper.'+side,hip,knee);bone(limb+'_lower.'+side,knee,foot,limb+'_upper.'+side)
    ell(limb+' thigh '+side,hip,(.032 if limb=='back' else .020,.047 if limb=='back' else .022,.055 if rabbit else .030),ma,limb+'_upper.'+side)
    seg(limb+' lower '+side,knee,foot,.013,.012,white,limb+'_lower.'+side);ell(limb+' paw '+side,(x,foot[1]-.01,.015),(.023,.047 if limb=='back' else .032,.015),white,limb+'_lower.'+side)
   ell('Dark eye '+side,(sign*hw*.83,-bl*.81,bh*1.21),(.009,.008,.010),black,'head');ell('Eye shine '+side,(sign*hw*.90,-bl*.838,bh*1.24),(.0025,.0025,.0025),shine,'head')
   eh=(sign*hw*.50,-bl*.60,bh*1.37)
   if rabbit:
    et=(sign*(.105 if lop else .048),-bl*.48,bh*(.60 if lop else 2.08));bone('ear.'+side,eh,et,'head');mid=(Vector(eh)+Vector(et))/2
    ell('Long soft ear '+side,mid,(.022,.026,(Vector(et)-Vector(eh)).length*.60),ma,'ear.'+side,r=(0,sign*(.14 if lop else -.12),0));ell('Pink inner ear '+side,(mid.x,mid.y-.020,mid.z),(.012,.006,(Vector(et)-Vector(eh)).length*.44),pink,'ear.'+side,r=(0,sign*(.14 if lop else -.12),0))
   else:
    bone('ear.'+side,eh,(sign*hw*.98,-bl*.55,bh*1.55),'head');ell('Round ear '+side,(sign*hw*.89,-bl*.54,bh*1.38),(.014,.009,.019),brown,'ear.'+side)
  if gp:
   for j in range(26):
    ang=j*2.399;y=-.045+(j%6)*.019;x=math.sin(ang)*.050;z=.10+math.cos(ang)*.014
    ell('Abyssinian rosette tuft '+str(j),(x,y,z),(.022,.026,.021),[brown,white,dark][j%3],k='ICO')
  elif not lop:
   ell('Dutch white blaze',(0,-bl*.923,bh*1.27),(.018,.012,.038),white,'head')
  rig=rig_from_defs(defs);skin_parts(parts,rig)
 else:
  shell=mat('Hermann ochre shell',(.58,.43,.14));scute=mat('Black scute centres',(.17,.17,.095));edge=mat('Amber shell margins',(.73,.56,.22));skin=mat('Scaled olive skin',(.42,.40,.22));claw=mat('Ivory claws',(.75,.72,.52))
  bone('body',(0,0,.05),(0,0,.08),None);bone('neck',(0,-.06,.05),(0,-.11,.045));bone('head',(0,-.11,.045),(0,-.14,.047),'neck');bone('jaw',(0,-.135,.037),(0,-.15,.033),'head');bone('tail',(0,.08,.035),(0,.115,.022))
  ell('Domed carapace',(0,.005,.061),(.081,.108,.060),shell);ell('Plastron',(0,.005,.025),(.074,.10,.021),edge);ell('Neck',(0,-.092,.045),(.024,.047,.023),skin,'neck');ell('Reptile head',(0,-.132,.048),(.025,.034,.025),skin,'head');ell('Horn beak',(0,-.157,.041),(.018,.010,.012),edge,'jaw')
  for side,sign in [('L',-1),('R',1)]:
   for limb,yy in [('front',-.055),('back',.065)]:
    hip=(sign*.051,yy,.04);knee=(sign*.079,yy-.01,.025);ft=(sign*.096,yy-.027,.014);bone(limb+'_upper.'+side,hip,knee);bone(limb+'_lower.'+side,knee,ft,limb+'_upper.'+side);seg('Scaled limb '+limb+side,hip,knee,.021,.017,skin,limb+'_upper.'+side);ell('Tortoise foot '+limb+side,ft,(.024,.025,.014),skin,limb+'_lower.'+side)
    for k in range(3):ell('Claw '+limb+side+str(k),(ft[0]+(k-1)*.009,ft[1]-.022,.008),(.003,.008,.003),claw,limb+'_lower.'+side)
   ell('Lateral eye '+side,(sign*.023,-.144,.057),(.003,.004,.004),black,'head')
  def patch(name,x,y,rx,ry,ma,lift):
   verts=[]
   for j in range(6):
    an=math.pi*2*j/6;xx=x+rx*math.cos(an);yy=y+ry*math.sin(an);zz=.061+.060*math.sqrt(max(.01,1-(xx/.081)**2-((yy-.005)/.108)**2))+lift;verts.append((xx,yy,zz))
   me=bpy.data.meshes.new(name);me.from_pydata(verts,[],[list(range(6))]);ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.data.materials.append(ma);ob.vertex_groups.new(name='body').add(list(range(6)),1,'REPLACE');parts.append(ob)
  for row,y in enumerate([-.059,-.018,.023,.064]):
   for j,x in enumerate([-.041,0,.041]):
    patch('Dark fitted scute '+str(row)+str(j),x,y,.020,.025,scute,.001)
    patch('Ochre scute centre '+str(row)+str(j),x-.002,y-.003,.009,.012,edge,.0018)
  seg('Small tail',(0,.087,.032),(0,.126,.02),.009,.002,skin,'tail');rig=rig_from_defs(defs);skin_parts(parts,rig)
 acts=native_actions(rig,kind);return rig,acts,kind,'original:Pixel Town animal asset team (2026-10-17)'

def custom_source_actions(rig,sourcecat=False,horse=False):
 bones=set(rig.pose.bones.keys())
 def pose(t,r,name):
  s=math.sin(t*math.pi*2)
  def rr(n,ax,a):
   if n in bones:rot_world(r.pose.bones[n],ax,a)
  def tr(n,v):
   if n in bones:translate_world(r.pose.bones[n],v)
  if sourcecat:
   if name in ('Walk','Run'):
    ax=(0,1,0);speed=2 if name=='Run' else 1
    for side,ph in [('L',0),('R',math.pi)]:
     for pre,ph2 in [('_Leg',ph),('_BLeg',ph+math.pi)]:
      u=math.sin(t*math.pi*2*speed+ph2);rr(side+pre+'_Upper',ax,.42*u);rr(side+pre+'_Lower',ax,.35*max(0,-u))
    rr('root',(0,1,0),.025*s)
   elif name in ('Eat','Drink'):
    rr('Neck',(0,1,0),.40+.05*s);rr('Head',(0,1,0),.45+.10*math.sin(t*math.pi*8))
   elif name=='Rest':
    tr('MotionRoot',(0,0,-.83));rr('Neck',(0,1,0),.12);rr('Head',(0,1,0),.16+.02*s)
    for side in ['L','R']:
     rr(side+'_Leg_Upper',(0,1,0),1.30);rr(side+'_Leg_Lower',(0,1,0),-2.40);rr(side+'_Foot',(0,1,0),1.10);rr(side+'_BLeg_Upper',(0,1,0),-1.30);rr(side+'_BLeg_Lower',(0,1,0),2.40);rr(side+'_BFoot',(0,1,0),-1.10)
   elif name=='Groom':rr('Head',(0,0,1),.55+.1*s);rr('Neck',(0,1,0),.3);rr('L_Leg_Upper',(0,1,0),-.7)
   elif name=='Sniff':rr('Neck',(0,1,0),.22+.06*s);rr('Head',(0,0,1),.1*s)
   elif name=='Observe':rr('Neck',(0,0,1),.3*s)
   for j in range(1,5):rr('tail'+str(j),(0,0,1),.07*s*(j/2))
  else:
   if name=='Rest':
    # Natural standing doze for equines; tucked chest-down rest for dogs.
    if horse:rr('Neck1',(1,0,0),-.08);rr('Head',(1,0,0),-.15+.025*s);rr('BackLeg.L',(1,0,0),.08)
    else:
     rr('Neck1',(1,0,0),-.10+.01*s);rr('Neck2',(1,0,0),-.12);rr('Head',(1,0,0),-.16+.02*s);rr('Tail1',(1,0,0),-.12);rr('Torso',(1,0,0),.01*s)
   if name=='Wag':
    for j in range(1,8):rr('Tail'+str(j),(0,0,1),.23*s)
   if name=='Sniff':rr('Neck1',(1,0,0),-.18+.05*s);rr('Head',(0,0,1),.12*s)
   if name=='Observe':rr('Neck2',(0,0,1),.2*s);rr('Head',(0,0,1),.15*s)
   if name=='Drink':
    for n in ['Neck1','Neck2','Neck3']:rr(n,(1,0,0),-.22+.02*s)
    rr('Head',(1,0,0),-.35+.04*math.sin(t*math.pi*6))
 names=['Walk','Run','Eat','Drink','Rest','Groom','Sniff','Observe'] if sourcecat else ['Drink','Rest','Wag','Sniff','Observe']
 return [action(rig,n,lambda t,r,n=n:pose(t,r,n),48 if n not in ('Rest','Observe') else 72) for n in names]

def coat_cats(mesh,p):
 # Original albedo is retained only for dark pupils and pink facial details; coat is authored in mesh color.
 image=next(iter(bpy.data.images),None);img=next((i for i in bpy.data.images if i.size[0]>8),None);pix=list(img.pixels) if img else [];uv=mesh.data.uv_layers.active
 col=mesh.data.color_attributes.new(name='IndividualCoat',type='FLOAT_COLOR',domain='CORNER')
 idx=int(p['id'][:2]);M=mat('Identity coat '+p['name'],(.7,.7,.7));nd=M.node_tree.nodes;vc=nd.new('ShaderNodeVertexColor');vc.layer_name=col.name;M.node_tree.links.new(vc.outputs['Color'],next(n for n in nd if n.type=='BSDF_PRINCIPLED').inputs['Base Color']);mesh.data.materials.clear();mesh.data.materials.append(M)
 for poly in mesh.data.polygons:
  for li in poly.loop_indices:
   v=mesh.matrix_world@mesh.data.vertices[mesh.data.loops[li].vertex_index].co;x,y,z=v
   stripe=math.sin(x*13+z*7+abs(y)*2)>.68
   if idx==1:c=(.085,.045,.020) if stripe and abs(y)>.14 else (.44,.25,.11)
   elif idx==2:
    c=(.90,.88,.79)
    if (x+.65)**2+(z-1.9)**2<.9:c=(.10,.095,.085)
    if (x-.6)**2+(z-2.6)**2<.55 or (x+1.1)**2+(z-3.0)**2<.6:c=(.73,.32,.10)
   elif idx==3:c=(.35,.42,.48)
   elif idx==4:c=(.25,.18,.14) if (x>.78 and z>2.20) or z<.60 or x<-1.5 else (.82,.75,.59)
   else:c=(.22,.17,.12) if stripe and abs(y)>.17 else (.53,.49,.38)
   if pix and uv:
    u,w=uv.data[li].uv;ix=min(img.size[0]-1,max(0,int(u*img.size[0])));iy=min(img.size[1]-1,max(0,int(w*img.size[1])));q=pix[4*(iy*img.size[0]+ix):4*(iy*img.size[0]+ix)+3]
    if max(q)-min(q)>.12 and q[0]>q[1]*1.12:c=tuple(q)
    if max(q)<.055:c=(.015,.020,.017)
   col.data[li].color=(*c,1)


def create_source(p):
 idx=int(p['id'][:2]);cat=idx<=5;horse=idx==20;f='cat' if cat else ('Horse' if horse else ('Husky' if idx in [8,9] else 'ShibaInu'))
 bpy.ops.wm.open_mainfile(filepath=str(BASE/'source'/f'{f}.blend'))
 rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers))
 for o in list(bpy.context.scene.objects):
  if o not in [rig,mesh]:bpy.data.objects.remove(o,do_unlink=True)
 rig.parent=None;rig.animation_data.action=None
 for t in list(rig.animation_data.nla_tracks):rig.animation_data.nla_tracks.remove(t)
 for b in rig.pose.bones:b.matrix_basis.identity()
 acts=[]
 if cat:
  bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT');eb=rig.data.edit_bones;master=eb.new('MotionRoot');master.head=(0,0,0);master.tail=(0,.01,0)
  for b in eb:
   if b.name!='MotionRoot' and not b.parent:b.parent=master
  bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False)
  keep=next(iter(bpy.data.actions));keep.name='Idle';acts=[keep]
  for ac in list(bpy.data.actions):
   if ac not in acts:bpy.data.actions.remove(ac)
  coat_cats(mesh,p)
  # Distinct body proportions, beyond a color swap: stocky blue, long Maine, slender Siamese.
  scales={1:(.136,.145,.132),2:(.128,.142,.126),3:(.140,.195,.135),4:(.139,.125,.137),5:(.180,.175,.166)}[idx]
  angle=-math.pi/2
 else:
  mapping={'Idle':'Idle','Walk':'Walk','Gallop':'Run','Eating':'Eat'}
  for ac in list(bpy.data.actions):
   if ac.name in mapping:ac.name=mapping[ac.name];acts.append(ac)
   else:bpy.data.actions.remove(ac)
  scales={6:(.27,.205,.125),7:(.225,.185,.190),8:(.24,.225,.245),9:(.31,.24,.270),10:(.19,.24,.108),11:(.18,.135,.153),20:(.47,.34,.31)}[idx]
  angle=0
  colors={6:[(.68,.32,.075),(.05,.04,.03),(.91,.86,.74)],7:[(.64,.25,.065),(.04,.035,.025),(.90,.86,.74)],8:[(.055,.06,.065),(.94,.93,.86),(.90,.89,.81)],9:[(.67,.37,.09),(.91,.66,.25),(.85,.57,.19)],10:[(.20,.085,.035),(.028,.020,.014),(.45,.25,.12)],11:[(.80,.70,.52),(.08,.06,.04),(.92,.86,.71)],20:[(.41,.16,.055),(.23,.065,.02),(.62,.31,.12),(.10,.08,.055),(.20,.065,.02),(.19,.12,.08),(.92,.91,.85),(.015,.02,.025)]}[idx]
  for j,m in enumerate(mesh.data.materials):
   m.use_nodes=True;bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Metallic'].default_value=0;bs.inputs['Roughness'].default_value=.87
   # Only main coat slots are changed; the original eyes remain readable.
   if j<len(colors) and (horse or j<3):bs.inputs['Base Color'].default_value=(*colors[j],1);m.diffuse_color=(*colors[j],1)
 # Breed additions use actual source bones, never independent world-space bobbing.
 additions=[];fur=mat('Breed added fur',(.82,.73,.54) if idx==11 else ((.66,.36,.10) if idx==9 else ((.20,.08,.035) if idx==10 else (.49,.46,.36))))
 if cat:
  iris=mat('Cat iris',(.55,.68,.18) if idx!=3 else (.79,.43,.08));pupil=mat('Vertical cat pupils',(.010,.018,.012));glint=mat('Eye highlight',(.95,.98,1))
  for sign in [-1,1]:
   additions.append(meshpart('Almond cat eye',(1.25,sign*.40,3.43),(.105,.035,.080),iris,'Head'))
   additions.append(meshpart('Narrow pupil',(1.28,sign*.432,3.44),(.028,.012,.068),pupil,'Head'))
   additions.append(meshpart('Eye glint',(1.30,sign*.445,3.465),(.016,.007,.016),glint,'Head'))
 if idx in [9,10,11]:
  # Replace narrow pointed ears with a pair of visibly pendant ear surfaces.
  eargroups={vg.index for vg in mesh.vertex_groups if vg.name.startswith('Ear')}
  remove={v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if g.group in eargroups)>.35}
  bm=bmesh.new();bm.from_mesh(mesh.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in remove],context='VERTS');bm.to_mesh(mesh.data);bm.free()
  for sign in [-1,1]:additions.append(meshpart('Pendulous breed ear',(sign*.42,-1.76,2.48),(.16,.18,.38),fur,'Head'))
  additions.append(meshpart('Soft breed neck ruff',(0,-1.66,2.50),(.35,.32,.33),fur,'Neck3'))
  muzzle=mat('Soft breed muzzle',(.73,.47,.20) if idx==9 else ((.37,.18,.07) if idx==10 else (.86,.77,.62)));nose=mat('Canine nose',(.025,.025,.018));eye=mat('Natural canine eyes',(.025,.018,.010));gl=mat('Canine eye glint',(.9,.94,.95))
  additions.append(meshpart('Rounded breed skull',(0,-2.02,2.64),(.32,.35,.28),fur,'Head'));additions.append(meshpart('Tapered breed muzzle',(0,-2.32,2.45),(.24,.26,.16),muzzle,'Head'));additions.append(meshpart('Canine nose',(0,-2.55,2.48),(.13,.045,.080),nose,'Head'))
  for sign in [-1,1]:
   additions.append(meshpart('Canine eye',(sign*.238,-2.22,2.72),(.052,.040,.052),eye,'Head'));additions.append(meshpart('Canine eye glint',(sign*.248,-2.25,2.738),(.014,.012,.014),gl,'Head'))
 if idx in [6,8,9,10,11]:
  tailgroups={vg.index for vg in mesh.vertex_groups if vg.name.startswith('Tail')};remove={v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups if g.group in tailgroups)>.55};bm=bmesh.new();bm.from_mesh(mesh.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in remove],context='VERTS');bm.to_mesh(mesh.data);bm.free()
  if idx==6:points=[(0,.78,1.8),(0,1.10,1.84)];radii=[.15,.07]
  elif idx==11:points=[(0,.78,1.8),(0,1.10,2.02),(0,1.22,2.25)];radii=[.07,.07,.04]
  else:points=[(0,.78,1.8),(0,1.23,1.80),(0,1.65,1.63),(0,2.05,1.39)];radii=([.14,.15,.10,.025] if idx in [8,9] else [.065,.055,.037,.014])
  tailmat=mat('Breed tail coat',(.68,.37,.09) if idx==9 else ((.06,.06,.06) if idx==8 else ((.20,.085,.035) if idx==10 else (.77,.65,.45))))
  for j in range(len(points)-1):additions.append(segment('Natural tail segment '+str(j),points[j],points[j+1],radii[j],radii[j+1],tailmat,'Tail'+str(j+1)))
  if idx==11:additions.append(meshpart('Poodle tail pom',points[-1],(.16,.16,.18),tailmat,'Tail2','ICO'))
 if idx==11:
  for j in range(35):
   a=j*2.399;lo=(math.cos(a)*.38,-1.78+math.sin(a)*.22,2.55+(j%4)*.10)
   additions.append(meshpart('Poodle rounded curl '+str(j),lo,(.13,.13,.13),fur,'Head','ICO'))
  for side,sign in [('L',1),('R',-1)]:
   for n,y,z in [('FrontLowerLeg',-.96,.65),('BackUpperLeg',.70,.85)]:additions.append(meshpart('Poodle leg curl '+n+side,(sign*.33,y,z),(.19,.20,.24),fur,n+'.'+side,'ICO'))
 if idx==5:
  for sign in [-1,1]:additions.append(meshpart('Maine ear tuft',(.65,sign*.50,3.96),(.06,.075,.16),fur,'Head','CONE',(.0,sign*.2,0)))
  for j in range(8):additions.append(meshpart('Maine chest ruff '+str(j),(.68,-.40+j*.11,1.96),(.18,.10,.27),fur,'chest','ICO'))
 if idx==20:
  white=mat('White forehead star',(.90,.87,.76));additions.append(meshpart('Shetland white forehead',(0,-3.12,4.33),(.12,.027,.17),white,'Head'))
 if additions:
  bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True)
  for o in additions:o.select_set(True)
  bpy.context.view_layer.objects.active=mesh;bpy.ops.object.join()
 for poly in mesh.data.polygons:poly.use_smooth=True
 acts+=custom_source_actions(rig,cat,horse)
 # Preserve the source armature / mesh world relationship under one nonanimated wrapper.
 wrapper=bpy.data.objects.new('IndividualSizeAndForward',None);bpy.context.collection.objects.link(wrapper)
 for o in [rig,mesh]:
  if o.parent not in [rig,mesh]:
   w=o.matrix_world.copy();o.parent=wrapper;o.matrix_world=w
 wrapper.scale=scales;wrapper.rotation_euler.z=angle
 bpy.context.view_layer.update()
 return rig,acts,'cat' if cat else ('pony' if horse else 'dog'),('J-Toastie Cat CC BY 3.0; pinned source in vendor/sources.json' if cat else 'Quaternius Ultimate Animated Animals CC0 1.0; pinned source in vendor/sources.json')

def export_animal(p,rig,acts,kind,source):
 scene=bpy.context.scene;scene.render.fps=24
 for ac in acts:
  if ac.name not in ['Walk','Run','Hop']:continue
  rig.animation_data.action=ac
  if len(ac.slots):rig.animation_data.action_slot=ac.slots[0]
  rootname='MotionRoot' if 'MotionRoot' in rig.pose.bones else ('Body' if 'Body' in rig.pose.bones else ('root' if 'root' in rig.pose.bones else 'body'));pb=rig.pose.bones[rootname];samples=[];q=pb.bone.matrix_local.to_quaternion()
  for frame in range(int(ac.frame_range[0]),int(ac.frame_range[1])+1):
   scene.frame_set(frame);v=rig.matrix_world.to_3x3()@(q@pb.location);v.x=0;v.y=0;samples.append((frame,q.inverted()@(rig.matrix_world.to_3x3().inverted()@v)))
  for frame,v in samples:pb.location=v;pb.keyframe_insert('location',frame=frame)
 # All exported tracks have one action and one slot, preventing accidental concatenation.
 rig.animation_data.action=None
 for t in list(rig.animation_data.nla_tracks):rig.animation_data.nla_tracks.remove(t)
 for ac in acts:
  ac.use_fake_user=True;t=rig.animation_data.nla_tracks.new();t.name=ac.name;strip=t.strips.new(ac.name,0,ac)
  if hasattr(strip,'action_slot') and len(ac.slots):strip.action_slot=ac.slots[0]
  t.mute=True
 rig.animation_data.action=next(a for a in acts if a.name=='Idle')
 if len(rig.animation_data.action.slots):rig.animation_data.action_slot=rig.animation_data.action.slots[0]
 scene.frame_set(0);bpy.context.view_layer.update()
 meshes=[o for o in scene.objects if o.type=='MESH']
 dg=bpy.context.evaluated_depsgraph_get();points=[o.evaluated_get(dg).matrix_world@v.co for o in meshes for v in o.evaluated_get(dg).data.vertices]
 lo=Vector([min(v[i] for v in points) for i in range(3)]);hi=Vector([max(v[i] for v in points) for i in range(3)])
 roots=[o for o in scene.objects if not o.parent]
 # Root correction is a constant transform; all geometry and clips share exactly the same correction.
 offset=lo.z
 for o in roots:o.location.z-=offset
 bpy.context.view_layer.update();lo.z-=offset;hi.z-=offset
 headbone='Head' if 'Head' in rig.pose.bones else ('head')
 head=rig.matrix_world@rig.pose.bones[headbone].head
 bodybone='body' if 'body' in rig.pose.bones else ('root' if 'root' in rig.pose.bones else 'Torso')
 body=rig.matrix_world@rig.pose.bones[bodybone].head
 conv=lambda v:[round(v.x,5),round(v.z,5),round(-v.y,5)]
 a=p['animal'];entry={'id':p['id'],'name':p['name'],'species':a['species'],'breed':a['breed'],'coat':a['coat'],'bodySize':a['bodySize'],'source':source,'glb':'assets/'+p['id']+'.glb','height':round(hi.z-lo.z,5),'length':round(hi.y-lo.y,5),'radius':round(max((hi.x-lo.x)/2,(hi.y-lo.y)/2)*.80,5),'actions':[ac.name for ac in acts],'headLocal':conv(head),'bodyLocal':conv(body),'groundOffset':0,'front':'+Z','rig':kind,'boneCount':len(rig.data.bones),'originalIdentityScale':a['scale']}
 rig.animation_data.action=None
 rootname='MotionRoot' if 'MotionRoot' in rig.pose.bones else ('Body' if 'Body' in rig.pose.bones else 'body');rootpb=rig.pose.bones[rootname]
 for ac in acts:
  rig.animation_data.action=ac
  if len(ac.slots):rig.animation_data.action_slot=ac.slots[0]
  corrections=[]
  for frame in range(int(ac.frame_range[0]),int(ac.frame_range[1])+1):
   scene.frame_set(frame);dg=bpy.context.evaluated_depsgraph_get();mn=min((o.evaluated_get(dg).matrix_world@v.co).z for o in meshes for v in o.evaluated_get(dg).data.vertices)
   if mn<-.0001:corrections.append((frame,rootpb.location.copy()+rootpb.bone.matrix_local.to_quaternion().inverted()@(rig.matrix_world.to_3x3().inverted()@Vector((0,0,-mn)))))
  for frame,v in corrections:rootpb.location=v;rootpb.keyframe_insert('location',frame=frame)
 rig.animation_data.action=None
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.ops.file.pack_all();scene['animal_identity']=json.dumps(entry,ensure_ascii=False)
 bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'assets'/(p['id']+'.blend')))
 for t in rig.animation_data.nla_tracks:t.mute=False
 bpy.ops.export_scene.gltf(filepath=str(BASE/entry['glb']),export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='NLA_TRACKS',export_nla_strips=True,export_force_sampling=True,export_anim_slide_to_zero=True,export_materials='EXPORT',export_extras=True,export_cameras=False,export_lights=False)
 for t in rig.animation_data.nla_tracks:t.mute=True
 rig.animation_data.action=next(a for a in acts if a.name=='Idle')
 if len(rig.animation_data.action.slots):rig.animation_data.action_slot=rig.animation_data.action.slots[0]
 scene.frame_set(0);render(p,entry)
 MAN.append(entry);REPORT.append({'id':p['id'],'bones':len(rig.data.bones),'vertices':sum(len(o.data.vertices) for o in meshes),'actions':entry['actions'],'boundsRest':[conv(lo),conv(hi)]})
 if len(MAN)==len(ROSTER):
  manifest_tmp=BASE/'assets'/'manifest.json.tmp';manifest_tmp.write_text(json.dumps({'version':1,'units':'metres','up':'+Y','front':'+Z','animals':MAN},ensure_ascii=False,indent=2));manifest_tmp.replace(BASE/'assets'/'manifest.json')
 (BASE/'qa'/'build-report.json').write_text(json.dumps(REPORT,ensure_ascii=False,indent=2))
 print('COMPLETED',p['id'],flush=True)

def render(p,e):
 scene=bpy.context.scene
 def aim(o,pt):o.rotation_euler=(Vector(pt)-o.location).to_track_quat('-Z','Y').to_euler()
 h=e['height'];l=e['length'];sz=max(h,l)*1.15;center=Vector((0,0,h*.48))
 bpy.ops.object.camera_add(location=center+Vector((1.3,-2.0,1.0))*sz);cam=bpy.context.object;aim(cam,center);cam.data.type='ORTHO';cam.data.ortho_scale=sz*1.25;scene.camera=cam
 helpers=[cam]
 for xyz,power in [((2,-3,4),250),((-3,-1,2),130)]:
  bpy.ops.object.light_add(type='AREA',location=center+Vector(xyz)*sz);light=bpy.context.object;light.data.energy=power*sz*sz;light.data.size=sz*2;aim(light,center);helpers.append(light)
 scene.world=bpy.data.worlds.new('StudioWorld');scene.world.color=(.45,.45,.45);scene.render.engine='CYCLES';scene.cycles.samples=12;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.filepath=str(BASE/'renders'/(p['id']+'.png'));scene.view_settings.view_transform='AgX';bpy.ops.render.render(write_still=True)
 for o in helpers:bpy.data.objects.remove(o,do_unlink=True)

for p in ROSTER:
 idx=int(p['id'][:2])
 rig,acts,kind,source=create_source(p) if idx<=11 or idx==20 else create_original(p)
 export_animal(p,rig,acts,kind,source)
