import * as THREE from 'three';
import Protocol from '../../../shared/town-3d-protocol.js';
import {PublicNavigation} from './navigation.js';
export class ActorExecutor {
 constructor(population,{capabilities,navigation,onFinish=()=>{},onChange=()=>{}}){this.population=population;this.capabilities=new Map(capabilities.map(c=>[c.id,c]));this.nav=new PublicNavigation(navigation);this.onFinish=onFinish;this.onChange=onChange;this.active=null;this.last=null}
 scene(){return {actors:[...this.population.avatars.values()].map(a=>({id:a.profile.id,position:a.root.position.toArray(),action:a.active,busy:this.active?.actorId===a.profile.id})),environment:{...window.townViewer.environment.state.snapshot(),paused:this.population.paused}}}
 start(envelope){if(this.active)throw new Error('已有角色行为正在进行');if(envelope.capability)this.capabilities.set(envelope.actorId,envelope.capability);const cap=this.capabilities.get(envelope.actorId),plan=Protocol.parse(envelope.plan,cap);const a=this.population.avatars.get(envelope.actorId);if(!a)throw new Error('角色尚未加载');this.active={...envelope,plan,index:0,results:[],elapsed:0,command:null,stages:[],actor:a};this.population.paused=false;this.population.restoreOcclusion();this.onChange();return true}
 blocked(id){const b=new Set();for(const a of this.population.avatars.values())if(a.profile.id!==id){const p=a.root.position;for(let dz=-1;dz<=1;dz++)for(let dx=-1;dx<=1;dx++){const i=this.nav.index(p.x+dx*.5,p.z+dz*.5);if(i>=0&&Math.hypot(this.nav.point(i)[0]-p.x,this.nav.point(i)[2]-p.z)<.54)b.add(i)}}return b}
 route(point,gait='walk'){
  const e=this.active,a=e.actor,cap=this.capabilities.get(e.actorId);if(!cap.locomotion[gait])throw new Error('当前模型没有对应步行动画，禁止滑行');
  e.route=this.nav.path(a.root.position.toArray(),point,this.blocked(e.actorId));e.routeIndex=0;e.speed=gait==='run'?2.6:1.2;e.blockedTime=0;this.population.playFor(a,cap.locomotion[gait]);
 }
 begin(c){const e=this.active,a=e.actor;e.elapsed=0;e.command=c;e.stages=[];e.phase=0;e.phaseTime=0;e.route=null;this.clearPose(a);
  if(c.type==='move')this.route([c.destination.x,0,c.destination.z],c.gait);
  else if(c.type==='work'){e.job=this.capabilities.get(e.actorId).jobs.find(j=>j.id===c.jobId);this.route(e.job.location);e.workState='travelling';}
  else if(c.type==='preset')this.population.playFor(a,c.clip);
  else if(c.type==='pose')this.pose(a,c.joints,c.seconds);
  else if(c.type==='social'){const target=this.population.avatars.get(c.targetId);if(!target||Math.hypot(target.root.position.x-a.root.position.x,target.root.position.z-a.root.position.z)>4)throw new Error('交谈对象已离开附近');a.root.rotation.y=Math.atan2(target.root.position.x-a.root.position.x,target.root.position.z-a.root.position.z);this.population.playFor(a,'Talk');}
  else this.population.playFor(a,'Idle');this.onChange();
 }
 pose(a,joints,seconds){const cap=this.capabilities.get(a.profile.id);a.aiPose={joints:Object.entries(joints).map(([key,angles])=>{const rule=cap.joints[key],bone=a.model.getObjectByName(rule.bone);if(!bone)throw new Error('模型骨骼不存在');return {bone,delta:new THREE.Quaternion().setFromEuler(new THREE.Euler(...angles.map(THREE.MathUtils.degToRad),'XYZ')),base:bone.quaternion.clone()}}),time:0,duration:seconds};}
 clearPose(a){if(a.aiPose){for(const j of a.aiPose.joints)j.bone.quaternion.copy(j.base);delete a.aiPose}}
 beforeAnimation(){for(const a of this.population.avatars.values())if(a.aiPose)for(const j of a.aiPose.joints)j.bone.quaternion.copy(j.base)}
 afterAnimation(dt){for(const a of this.population.avatars.values())if(a.aiPose){const p=a.aiPose;p.time+=dt;const weight=Math.min(1,p.time/.3,(p.duration-p.time)/.3);for(const j of p.joints){j.base.copy(j.bone.quaternion);j.bone.quaternion.multiply(new THREE.Quaternion().slerp(j.delta,Math.max(0,weight)))}if(p.time>=p.duration)this.clearPose(a)}}
 travel(dt){const e=this.active,a=e.actor;if(e.routeIndex>=e.route.length)return true;const point=e.route[e.routeIndex],p=new THREE.Vector3(...point),delta=p.clone().sub(a.root.position),distance=Math.hypot(delta.x,delta.z),step=Math.min(distance,e.speed*dt);
  if(distance<.008){a.root.position.copy(p);e.routeIndex++;return e.routeIndex>=e.route.length}
  const candidate=a.root.position.clone().addScaledVector(delta,step/Math.max(distance,.001));
  if([...this.population.avatars.values()].some(b=>b!==a&&Math.hypot(candidate.x-b.root.position.x,candidate.z-b.root.position.z)<.5)){e.blockedTime+=dt;if(e.blockedTime>5)throw new Error('前方被其他角色占用，已停止，稍后可重新寻路');return false}
  e.blockedTime=0;a.root.position.copy(candidate);a.root.rotation.y=Math.atan2(delta.x,delta.z);for(const [id,z] of Object.entries(window.TOWN_META.zones))if(Math.abs(candidate.x-z.center[0])<=z.size[0]/2&&Math.abs(candidate.z+z.center[1])<=z.size[1]/2){a.profile.zone=id;break}return false;
 }
 workPhase(){const e=this.active,s=e.job.steps[e.phase];if(!s)return;e.phaseTime=0;this.population.playFor(e.actor,e.actor.actions.Thoughtful?'Thoughtful':'Idle');const side=e.phase%2?'leftForearm':'rightForearm';if(this.capabilities.get(e.actorId).joints[side])this.pose(e.actor,{[side]:[0,0,12]},s.seconds);this.onChange();}
 update(dt){if(!this.active||this.population.paused)return;const e=this.active;
  try{
   if(!e.command)this.begin(e.plan.commands[e.index]);e.elapsed+=dt;const c=e.command;let done=false;
   if(c.type==='move')done=this.travel(dt);
   else if(c.type==='work'){
    if(e.workState==='travelling'){if(this.travel(dt)){e.workState='practising';this.workPhase()}}
    else{e.phaseTime+=dt;if(e.phaseTime>=e.job.steps[e.phase].seconds){const s=e.job.steps[e.phase];e.stages.push({name:s.name,seconds:e.phaseTime});this.clearPose(e.actor);e.phase++;if(e.phase>=e.job.steps.length)done=true;else this.workPhase()}}
   }else done=e.elapsed>=(c.type==='social'?3:c.seconds);
   if(done){e.results.push({index:e.index,status:'completed',elapsed:e.elapsed,...(c.type==='work'?{stages:e.stages}: {})});this.clearPose(e.actor);e.index++;e.command=null;if(e.index>=e.plan.commands.length)this.finish('completed');else this.onChange();}
  }catch(error){e.results.push({index:e.index,status:'failed',elapsed:e.elapsed,error:error.message});this.finish('failed')}
 }
 stop(){if(this.active){const e=this.active;if(e.command)e.results.push({index:e.index,status:'cancelled',elapsed:e.elapsed});this.finish('cancelled')}}
 finish(status){const e=this.active;if(!e)return;this.clearPose(e.actor);this.population.playFor(e.actor,e.actor.profile.defaultAction||'Idle');const receipt={requestId:e.requestId,actorId:e.actorId,status,results:e.results,scene:this.scene()};this.active=null;this.last=receipt;this.onChange();this.onFinish(receipt)}
 snapshot(){const e=this.active;return e?{actorId:e.actorId,index:e.index,type:e.command?.type,elapsed:e.elapsed,phase:e.phase,stage:e.job?.steps[e.phase]?.name,position:e.actor.root.position.toArray()}:null}
}
