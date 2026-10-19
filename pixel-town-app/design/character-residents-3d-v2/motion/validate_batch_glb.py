"""Read actual resident GLB binaries independently of the resident builder.
No source/runtime/API/save modifications; writes only motion/qa JSON.
"""
from pathlib import Path
import sys,json,struct,math,time
import numpy as np
O=Path(__file__).resolve().parent;A=O.parent/'assets'
CANON={r['name'] for r in json.loads((O/'bone-rest.json').read_text())['bones']}
META={r['name']:r for r in json.loads((O/'actions.json').read_text())['actions']}
EXPECTED=set(META);CUSTOM=['Eat','Drink','Read','Phone','Stretch','LieDown','LieRest','GetUp']
MIN_COUNT=int(sys.argv[sys.argv.index('--expect-count')+1]) if '--expect-count' in sys.argv else 45

def load(path):
 raw=path.read_bytes();magic,version,length=struct.unpack_from('<III',raw,0)
 if magic!=0x46546c67 or version!=2 or length!=len(raw):raise ValueError('invalid GLB header/length')
 chunks={};at=12
 while at<len(raw):
  size,kind=struct.unpack_from('<II',raw,at);chunks[kind]=raw[at+8:at+8+size];at+=8+size
 return json.loads(chunks[0x4e4f534a]),chunks.get(0x004e4942,b'')

def accessor(g,data,index):
 a=g['accessors'][index];bv=g['bufferViews'][a['bufferView']];dims={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dtype={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']];dt=np.dtype(dtype);offset=bv.get('byteOffset',0)+a.get('byteOffset',0);stride=bv.get('byteStride',dt.itemsize*dims)
 return np.ndarray(shape=(a['count'],dims),dtype=dt,buffer=data,offset=offset,strides=(stride,dt.itemsize))

def qdistance(a,b):
 a=a/np.linalg.norm(a,axis=-1,keepdims=True);b=b/np.linalg.norm(b,axis=-1,keepdims=True);dot=np.abs(np.sum(a*b,axis=-1));return float(np.max(np.degrees(2*np.arccos(np.clip(dot,0,1)))))

def trs(node,override=None):
 override=override or {}
 if 'matrix' in node and not override:return np.asarray(node['matrix'],dtype=float).reshape(4,4).T
 t=np.asarray(override.get('translation',node.get('translation',[0,0,0])),dtype=float);q=np.asarray(override.get('rotation',node.get('rotation',[0,0,0,1])),dtype=float);q=q/np.linalg.norm(q);x,y,z,w=q;s=np.asarray(override.get('scale',node.get('scale',[1,1,1])),dtype=float)
 r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])*s[None,:]
 m=np.eye(4);m[:3,:3]=r;m[:3,3]=t;return m

def sampled_world(g,data,anim,phase):
 nodes=g['nodes'];overrides={};parent={child:i for i,n in enumerate(nodes) for child in n.get('children',[])};duration=max(float(accessor(g,data,s['input'])[-1,0]) for s in anim['samplers']);t=phase*duration
 for c in anim['channels']:
  target=c['target'];prop=target['path']
  if prop not in ['translation','rotation','scale']:continue
  sp=anim['samplers'][c['sampler']];times=accessor(g,data,sp['input']).ravel();arr=accessor(g,data,sp['output'])
  if sp.get('interpolation')=='CUBICSPLINE':arr=arr.reshape(len(times),3,-1)[:,1,:]
  index=max(0,min(len(times)-1,int(np.searchsorted(times,t,side='right')-1)));nxt=min(len(times)-1,index+1);mix=0 if index==nxt else float((t-times[index])/(times[nxt]-times[index]));mix=max(0,min(1,mix));a=arr[index].astype(float);b=arr[nxt].astype(float)
  if prop=='rotation':
   a/=np.linalg.norm(a);b/=np.linalg.norm(b);dot=float(np.dot(a,b))
   if dot<0:b=-b;dot=-dot
   if dot>.9995:value=a*(1-mix)+b*mix;value/=np.linalg.norm(value)
   else:theta=math.acos(max(-1,min(1,dot)));value=(math.sin((1-mix)*theta)*a+math.sin(mix*theta)*b)/math.sin(theta)
  elif sp.get('interpolation')=='STEP':value=a
  else:value=a*(1-mix)+b*mix
  overrides.setdefault(target['node'],{})[prop]=value
 cache={}
 def world(i):
  if i not in cache:cache[i]=(world(parent[i]) if i in parent else np.eye(4))@trs(nodes[i],overrides.get(i))
  return cache[i]
 return {i:world(i) for i in range(len(nodes))}

def skinned_ground(g,data,world):
 lows=[]
 for node in g['nodes']:
  if 'mesh' not in node or 'skin' not in node:continue
  skin=g['skins'][node['skin']];inverse=accessor(g,data,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);matrices=np.asarray([world[j] for j in skin['joints']])@inverse
  for prim in g['meshes'][node['mesh']]['primitives']:
   attrs=prim['attributes'];positions=accessor(g,data,attrs['POSITION']);joint=accessor(g,data,attrs['JOINTS_0']);weight=accessor(g,data,attrs['WEIGHTS_0']);hom=np.column_stack([positions,np.ones(len(positions))]);ys=np.einsum('nv,nkv->nk',hom,matrices[joint,:, :][:,:,1,:]);lows.append(float(np.min(np.sum(ys*weight,axis=1))))
 return min(lows)

def test(path,identity):
 g,data=load(path);checks=[];metrics={};nodes=g.get('nodes',[])
 def check(n,ok,info=None):checks.append({'check':n,'pass':bool(ok),'info':info})
 check('Embedded GLB buffer',len(g.get('buffers',[]))==1 and 'uri' not in g['buffers'][0])
 skins=g.get('skins',[]);check('Exactly one skin',len(skins)==1)
 joints=skins[0]['joints'] if skins else [];names=[nodes[j].get('name','') for j in joints]
 check('65 canonical named joints',len(joints)==65 and set(names)==CANON,{'count':len(joints),'missing':sorted(CANON-set(names)),'extra':sorted(set(names)-CANON)})
 if skins:
  inv=accessor(g,data,skins[0]['inverseBindMatrices']);check('Finite invertible inverse bind matrices',np.isfinite(inv).all() and np.min(np.abs(np.linalg.det(inv.reshape(-1,4,4)[:,:3,:3])))>1e-9)
 weighted=0;max_weight_error=0;max_joint=0;weight_finite=True
 for mesh in g.get('meshes',[]):
  for primitive in mesh.get('primitives',[]):
   attrs=primitive.get('attributes',{})
   if 'JOINTS_0' in attrs and 'WEIGHTS_0' in attrs:
    j=accessor(g,data,attrs['JOINTS_0']);w=accessor(g,data,attrs['WEIGHTS_0']);weighted+=len(j);max_joint=max(max_joint,int(np.max(j)));max_weight_error=max(max_weight_error,float(np.max(np.abs(np.sum(w,axis=1)-1))));weight_finite=weight_finite and bool(np.isfinite(w).all() and np.min(w)>=0)
 check('Valid normalized skin weights',weighted>0 and weight_finite and max_weight_error<.0002 and max_joint<65,{'vertices':weighted,'maximumWeightSumError':max_weight_error,'maximumJointIndex':max_joint})
 anims={a['name']:a for a in g.get('animations',[])};check('All30 expected named animations',set(anims)==EXPECTED,{'count':len(anims),'missing':sorted(EXPECTED-set(anims)),'extra':sorted(set(anims)-EXPECTED)})
 endpoints={};global_norm=0;global_step=0;negative=0;total_samples=0
 for name,anim in anims.items():
  chan={};maxnorm=0;maxstep=0;duration=0;finite=True;monotonic=True;rotbones=set();neg=0
  for c in anim['channels']:
   sampler=anim['samplers'][c['sampler']];times=accessor(g,data,sampler['input']).ravel();arr=accessor(g,data,sampler['output']);node=c['target']['node'];prop=c['target']['path'];finite=finite and bool(np.isfinite(times).all() and np.isfinite(arr).all());monotonic=monotonic and bool(len(times)==1 or np.all(np.diff(times)>0));duration=max(duration,float(times[-1]));total_samples+=len(times)
   if sampler.get('interpolation')=='CUBICSPLINE':arr=arr.reshape(len(times),3,-1)[:,1,:]
   chan[(node,prop)]=(arr[0].copy(),arr[-1].copy())
   if prop=='rotation':
    rotbones.add(nodes[node].get('name',''));maxnorm=max(maxnorm,float(np.max(np.abs(np.linalg.norm(arr,axis=1)-1))))
    if len(arr)>1:
     maxstep=max(maxstep,qdistance(arr[:-1],arr[1:]));neg+=int(np.sum(np.sum(arr[:-1]*arr[1:],axis=1)<-.0001))
  endpoints[name]=chan;global_norm=max(global_norm,maxnorm);global_step=max(global_step,maxstep);negative+=neg
  expected_dur=META.get(name,{}).get('duration',duration);check(name+' finite monotone samples',finite and monotonic)
  check(name+' normalized quaternion keys',maxnorm<.0002,maxnorm)
  check(name+' duration',abs(duration-expected_dur)<.043,{'glbSeconds':duration,'expectedSeconds':expected_dur})
  # The exporter removes constant tracks. Missing constant rotations are valid.
  if name in CUSTOM:check(name+' no abrupt adjacent keys',maxstep<16,{'maximumDegrees':maxstep})
  if name in ['Eat','Read','Phone','LieRest']:
   qgap=max([qdistance(a,b) for (node,prop),(a,b) in chan.items() if prop=='rotation'] or [0]);pgap=max([float(np.linalg.norm(a-b)) for (node,prop),(a,b) in chan.items() if prop=='translation'] or [0]);check(name+' exact loop endpoint',qgap<.15 and pgap<.0003,{'rotationDegrees':qgap,'translationMetres':pgap})
  metrics[name]={'duration':duration,'rotationChannels':len(rotbones),'maximumQuaternionNormError':maxnorm,'maximumAdjacentRotationDegrees':maxstep,'negativeHemispherePairs':neg}
 check('No quaternion hemisphere sign inversions',negative==0,negative)
 runtime=path.parent/'runtime.glb'
 if runtime.exists():
  rg,rd=load(runtime);rnames={rg['nodes'][j].get('name','') for sk in rg.get('skins',[]) for j in sk['joints']};check('Runtime GLB same65 bones and no animation payload',rnames==CANON and not rg.get('animations'))
 else:check('Runtime GLB exists',False)
 def endpoint(a,b,ea,eb):
  aa=endpoints[a];bb=endpoints[b];qgap=0;pgap=0
  for key in aa.keys()|bb.keys():
   node,prop=key;default=np.asarray(nodes[node].get(prop,[0,0,0,1] if prop=='rotation' else [1,1,1] if prop=='scale' else [0,0,0]),dtype=np.float32);av=aa.get(key,(default,default))[ea];bv=bb.get(key,(default,default))[eb]
   if prop=='rotation':qgap=max(qgap,qdistance(av,bv))
   elif prop=='translation':pgap=max(pgap,float(np.linalg.norm(av-bv)))
  return qgap,pgap
 for a,b,ea,eb in [('LieDown','LieRest',1,0),('LieRest','GetUp',0,0)]:
  if a in endpoints and b in endpoints:
   qgap,pgap=endpoint(a,b,ea,eb);check(a+' -> '+b+' actual exported continuity',qgap<.15 and pgap<.0003,{'rotationDegrees':qgap,'translationMetres':pgap})
 # Verify actual exported anatomy in glTF world space (+Y up,+Z forward).
 byname={nodes[j]['name']:j for j in joints};wave=[]
 if 'Wave' in anims:
  for phase in [0,.25,.5,.75,1]:
   ww=sampled_world(g,data,anims['Wave'],phase);u=ww[byname['upperarm_l']];lo=ww[byname['lowerarm_l']];h=ww[byname['hand_l']];direction=h[:3,3]-lo[:3,3];direction/=np.linalg.norm(direction);d=np.linalg.inv(u[:3,:3])@direction;d/=np.linalg.norm(d);palm=h[:3,0]/np.linalg.norm(h[:3,0]);wave.append({'phase':phase,'sideBendDegrees':math.degrees(math.asin(max(-1,min(1,float(d[0]))))),'flexionDegrees':math.degrees(math.atan2(float(d[2]),float(d[1]))),'palmForwardDot':float(palm[2])})
  check('Exported Wave anatomical hinge plane',max(abs(x['sideBendDegrees']) for x in wave)<15,wave)
  check('Exported Wave positive flexion',all(45<x['flexionDegrees']<115 for x in wave))
  check('Exported Wave palm faces front',min(x['palmForwardDot'] for x in wave)>.5)
 if 'LieRest' in anims:
  ww=sampled_world(g,data,anims['LieRest'],.5);hp=ww[byname['pelvis']][:3,3];head=ww[byname['Head']][:3,3];axis=head-hp;axis/=np.linalg.norm(axis);flex={}
  for side in ['l','r']:
   hip=ww[byname['thigh_'+side]][:3,3];knee=ww[byname['calf_'+side]][:3,3];ankle=ww[byname['foot_'+side]][:3,3];u=knee-hip;v=ankle-knee;u/=np.linalg.norm(u);v/=np.linalg.norm(v);flex[side]=math.degrees(math.acos(max(-1,min(1,float(np.dot(u,v))))))
  check('Exported LieRest horizontal torso',abs(axis[1])<.20,{'upDot':float(axis[1])})
  check('Exported LieRest actual knee flexion',all(40<x<135 for x in flex.values()),flex)
 grounds={}
 for name in ['Eat','Drink','Read','Phone','Stretch','LieDown','LieRest','GetUp']:
  if name not in anims:continue
  values=[]
  for phase in [0,.5,1]:values.append(skinned_ground(g,data,sampled_world(g,data,anims[name],phase)))
  grounds[name]=values;check(name+' exported skinned mesh ground fit',min(values)>-.003 and max(values)<.012,{'worldYAtThreePhases':values})
 metrics['_exportedGroundSamples']=grounds
 return {'id':identity,'file':str(path.relative_to(O.parent)),'bytes':path.stat().st_size,'checks':checks,'passed':sum(x['pass'] for x in checks),'total':len(checks),'failed':[x for x in checks if not x['pass']],'metrics':metrics,'channelSampleCount':total_samples,'maximumQuaternionNormError':global_norm}

reports=[];errors=[]
for p in sorted(A.glob('*/manifest.json')):
 identity=p.parent.name;path=p.parent/'character.glb'
 if not path.exists():continue
 try:
  report=test(path,identity);reports.append(report);print('GLB',identity,report['passed'],report['total'],'failed',len(report['failed']),flush=True)
 except Exception as e:errors.append({'id':identity,'error':repr(e)});print('ERROR',identity,repr(e),flush=True)
result={'schemaVersion':1,'inspectedCount':len(reports),'expectedCount':MIN_COUNT,'countPass':len(reports)==MIN_COUNT,'passed':sum(r['passed'] for r in reports),'total':sum(r['total'] for r in reports),'errors':errors,'failedIdentities':[r['id'] for r in reports if r['failed']],'reports':reports}
(O/'qa/resident-batch-glb.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('BATCH_GLB_CHECKS',result['passed'],result['total'],'RESIDENTS',len(reports),'EXPECTED',MIN_COUNT,'ERRORS',errors)
