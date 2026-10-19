// Independent read-only headless audit; does not modify simulation or tests.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {AnimalLife} from './animal-simulation.js';

const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const read=f=>JSON.parse(fs.readFileSync(f,'utf8'));
const navigation=read(path.join(root,'reference/navigation.json'));
const manifest=read(fs.existsSync(path.join(root,'animal-library/assets/manifest.json'))?path.join(root,'animal-library/assets/manifest.json'):path.join(root,'../animal-assets-3d-v1/assets/manifest.json'));
const protectedFiles=['src/animal-simulation.js','src/animal-simulation.test.js','reference/navigation.json'];
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const sourceHashes=Object.fromEntries(protectedFiles.map(p=>[p,sha(path.join(root,p))]));
const distance=(a,b)=>Math.hypot(a[0]-b[0],a[2]-b[2]);
const round=p=>p?.map(v=>+v.toFixed(5));
const env={hour:10,weather:'sunny',season:'spring'};
const dt=1/30;
const scenarios=[];
const eventsOf=l=>l.events.map(e=>({...e}));
const summarize=l=>({time:+l.time.toFixed(2),human:{position:round(l.human.position),phase:l.human.phase,task:l.human.task,grid:l.human.grid?.id||'public',pathPoints:l.human.path.length,next:l.human.path[0],blocked:l.human.blocked},animals:l.animals.map(a=>({id:a.id,state:a.state,position:round(a.position),pathPoints:a.path.length,next:a.path[0],reserved:a.reserved,partner:a.partner,blocked:a.blocked,shelterDistance:+distance(a.position,a.habitat.shelter).toFixed(3),restTarget:round(a.restSlot||a.habitat.restSlots?.find?.(s=>s.petId===a.id)?.point||a.habitat.shelter),restTargetDistance:+distance(a.position,a.restSlot||a.habitat.restSlots?.find?.(s=>s.petId===a.id)?.point||a.habitat.shelter).toFixed(3),air:a.air}))});
function make(seed=20261017){return new AnimalLife(manifest.animals,navigation,{seed});}
function run(l,seconds,environment=env,stop=null){
 const metrics={secondsRequested:seconds,steps:0,invalidAnimalSamples:0,invalidHumanSamples:0,nonFiniteSamples:0,maxHumanStep:0,maxAnimalStep:0,maxGroundAnimalStep:0,maxAnimalStepDetail:null,penetrationSamples:0,minPairGap:Infinity,worstPair:null,minimumBird3DGap:Infinity,birdPenetrationSamples:0,worstBirdPair:null,minimumStaticPropGap:Infinity,worstStaticProp:null,humanUnderLowCanopySamples:0,firstLowCanopyEntry:null,firstInvalid:null,pathUnchangedFor:0,maxTaskStationarySeconds:0,finished:false};
 let previousHuman=l.human.position.slice(),previousAnimals=l.animals.map(a=>a.position.slice()),stationary=0;
 const taskBefore=l.human.task?.kind;const timeline=[];
 for(let i=0;i<seconds/dt;i++){
  l.update(dt,environment);metrics.steps++;
  const hd=distance(previousHuman,l.human.position);metrics.maxHumanStep=Math.max(metrics.maxHumanStep,hd);
  for(const habitat of l.habitats){const c=habitat.canopy;if(!c||c.roofY-habitat.grid.y(habitat.shelter[0],habitat.shelter[2])>=1.95)continue;const b=c.bounds,[x,,z]=l.human.position;if(x>b[0]-.3&&x<b[2]+.3&&z>b[1]-.3&&z<b[3]+.3){metrics.humanUnderLowCanopySamples++;metrics.firstLowCanopyEntry??={time:+l.time.toFixed(3),habitat:habitat.id,position:round(l.human.position),bounds:b,expansion:.3,humanPhase:l.human.phase};}}
  if(l.human.task&&hd<1e-5)stationary+=dt;else stationary=0;
  metrics.maxTaskStationarySeconds=Math.max(metrics.maxTaskStationarySeconds,stationary);
  const entities=[...l.animals,l.human];
  for(let j=0;j<entities.length;j++){
   const a=entities[j];const human=a===l.human;
   if(!a.position.every(Number.isFinite))metrics.nonFiniteSamples++;
   if((a.air||0)<=.4)for(const obstacle of a.habitat?.obstacles||[]){const gap=Math.hypot(a.position[0]-obstacle.point[0],a.position[2]-obstacle.point[1])-(a.radius||.25)-obstacle.radius;if(gap<metrics.minimumStaticPropGap){metrics.minimumStaticPropGap=gap;metrics.worstStaticProp={id:a.id,time:+l.time.toFixed(3),position:round(a.position),obstacle,clearance:gap};}}
   if((a.air||0)<=.4&&!a.grid.legal(a.position[0],a.position[2])){
    if(human)metrics.invalidHumanSamples++;else metrics.invalidAnimalSamples++;
    metrics.firstInvalid??={time:l.time,id:a.id,position:round(a.position),phase:a.phase,state:a.state,grid:a.grid.id||'public'};
   }
   if(!human){const moved=distance(previousAnimals[j],a.position);if(moved>metrics.maxAnimalStep){metrics.maxAnimalStep=moved;metrics.maxAnimalStepDetail={id:a.id,time:+l.time.toFixed(3),from:round(previousAnimals[j]),to:round(a.position),state:a.state,air:a.air,flight:a.flight?{perchIndex:a.perchIndex,to:a.flight.to,elapsed:a.flight.elapsed,duration:a.flight.duration}:null};}if(a.air<=.4)metrics.maxGroundAnimalStep=Math.max(metrics.maxGroundAnimalStep,moved);}
  }
  // Airborne birds are separated in 3D; ground body discs are compared in XZ.
  if(i%3===0)for(let a=0;a<entities.length;a++)for(let b=a+1;b<entities.length;b++){
   const one=entities[a],two=entities[b];if((one.air||0)>.4||(two.air||0)>.4)continue;
   const d=distance(one.position,two.position),gap=d-(one.radius||.2)-(two.radius||.25);
   if(gap<metrics.minPairGap){metrics.minPairGap=gap;metrics.worstPair={time:+l.time.toFixed(2),ids:[one.id,two.id],distance:+d.toFixed(5),radiusSum:+((one.radius||.2)+(two.radius||.25)).toFixed(5),positions:[round(one.position),round(two.position)]};}
   if(gap<-.02)metrics.penetrationSamples++;
  }
  if(i%3===0){const birds=l.animals.filter(a=>a.species==='鸟');for(let a=0;a<birds.length;a++)for(let b=a+1;b<birds.length;b++){const one=birds[a],two=birds[b],d=Math.hypot(...one.position.map((v,k)=>v-two.position[k])),gap=d-one.radius-two.radius;if(gap<metrics.minimumBird3DGap){metrics.minimumBird3DGap=gap;metrics.worstBirdPair={time:+l.time.toFixed(3),ids:[one.id,two.id],distance:+d.toFixed(6),positions:[round(one.position),round(two.position)],states:[one.state,two.state],nodes:[one.flightNode,two.flightNode]};}if(gap<-.02)metrics.birdPenetrationSamples++;}}
  previousHuman=l.human.position.slice();previousAnimals=l.animals.map(a=>a.position.slice());
  if(i%300===0)timeline.push({time:+l.time.toFixed(2),human:round(l.human.position),phase:l.human.phase,taskPhase:l.human.task?.phase,stage:l.human.task?.travelStage,path:l.human.path.length,animalPath:l.human.task?l.get(l.human.task.id)?.path.length:null});
  if(stop?.(l)){metrics.finished=true;break;}
 }
 metrics.secondsRun=+(metrics.steps*dt).toFixed(2);metrics.maxHumanStep=+metrics.maxHumanStep.toFixed(5);metrics.maxAnimalStep=+metrics.maxAnimalStep.toFixed(5);metrics.minPairGap=+metrics.minPairGap.toFixed(5);metrics.maxTaskStationarySeconds=+metrics.maxTaskStationarySeconds.toFixed(2);
 return {metrics,timeline,summary:summarize(l),events:eventsOf(l)};
}

const free=make();scenarios.push({name:'free-120s-real-20-animals',seed:20261017,...run(free,120)});
console.log('FREE',scenarios.at(-1).metrics);
const shortFree=make();scenarios.push({name:'free-60s-real-20-animals',seed:20261017,...run(shortFree,60)});
const weather=make();run(weather,30);weather.command('07_dog_shiba','fetch');const beforeWeather=summarize(weather);scenarios.push({name:'storm-shelter-120s-after-active-period',seed:20261017,beforeWeather,...run(weather,120,{hour:14,weather:'storm',season:'summer'})});
console.log('WEATHER',scenarios.at(-1).summary.animals.filter(a=>a.air<=.4&&a.shelterDistance>1.5).map(a=>({id:a.id,state:a.state,d:a.shelterDistance,path:a.pathPoints})));
for(const kind of ['feed','pet','fetch','walk','social']){
 const l=make();l.get('07_dog_shiba').hunger=.8;
 const result=l.command('07_dog_shiba',kind);const r=run(l,120,env,l=>l.events.some(e=>e.kind===kind+'-complete'||e.kind===kind+'-timeout'));
 scenarios.push({name:'f-shiba-'+kind,seed:20261017,command:result,...r});
 console.log(kind,result,r.metrics.finished,r.metrics.secondsRun,r.summary.human,r.events.filter(e=>e.kind.includes(kind)));
}
for(const [id,kind] of [['01_cat_tabby','feed'],['16_rabbit_lop','feed'],['03_cat_british_blue','pet']]){
 const l=make();const before=round(l.human.position);const result=l.command(id,kind);const after=round(l.human.position);
 const r=run(l,900,env,l=>l.events.some(e=>e.kind===kind+'-complete'));
 scenarios.push({name:'cross-town-'+id+'-'+kind,seed:20261017,command:result,before,immediatelyAfter:after,...r});
 console.log('CROSS',id,result,r.metrics.finished,r.metrics.secondsRun,r.metrics.maxHumanStep,r.summary.human,r.events.filter(e=>['visit-travel','local-visit',kind+'-complete'].includes(e.kind)));
}
// A difficult reproducibility case: feed then pet then fetch in the same life.
const sequence=make();const sequenceResults=[];
for(const kind of ['feed','pet','fetch','walk','social']){
 const result=sequence.command('07_dog_shiba',kind);const start=sequence.time;
 const r=run(sequence,90,env,l=>l.events.some(e=>e.time>=start&&e.kind===kind+'-complete'));
 sequenceResults.push({kind,command:result,...r});
}
scenarios.push({name:'f-shiba-sequential-interactions',seed:20261017,results:sequenceResults});
console.log('SEQUENCE',sequenceResults.map(r=>[r.kind,r.metrics.finished,r.metrics.secondsRun,r.summary.human.phase]));

const seedSweeps=[];
for(const seed of [1,7,17,42,123,20261017])for(const kind of ['feed','pet']){
 const l=make(seed);l.command('07_dog_shiba',kind);const result=run(l,60,env,l=>l.events.some(e=>e.kind===kind+'-complete'));
 seedSweeps.push({seed,kind,finished:result.metrics.finished,secondsRun:result.metrics.secondsRun,human:result.summary.human,animal:result.summary.animals.find(a=>a.id==='07_dog_shiba')});
}
console.log('SEED SWEEP',seedSweeps.map(r=>[r.seed,r.kind,r.finished]));
const birdFeed=make();birdFeed.command('12_bird_budgie_green','feed');const birdRun=run(birdFeed,250,env,l=>l.events.some(e=>e.kind==='feed-complete'));
scenarios.push({name:'bird-feed-contact-extra-check',seed:20261017,...birdRun});
console.log('BIRD FEED',birdRun.metrics.finished,birdRun.summary.animals.find(a=>a.id==='12_bird_budgie_green'),birdRun.summary.human);
const birdNeedEvidence=[];
for(const [need,node,field] of [['hunger','food','feederPoint'],['thirst','water','drinkingPoint']]){
 const l=make(),a=l.get('12_bird_budgie_green');a.hunger=.05;a.thirst=.05;a[need]=.95;a.timer=0;
 const r=run(l,60,env,l=>{const a=l.get('12_bird_budgie_green');return a.flightNode===node&&!a.flight&&a[need]<.70});
 const target=a.habitat[field],distance3D=Math.hypot(...a.position.map((v,k)=>v-target[k]));
 const evidence={need,node,completed:r.metrics.finished,secondsRun:r.metrics.secondsRun,position:round(a.position),target,distance3D:+distance3D.toFixed(6),remainingNeed:+a[need].toFixed(4),state:a.state};birdNeedEvidence.push(evidence);
 scenarios.push({name:'bird-autonomous-'+need+'-actual-contact',seed:20261017,contactEvidence:evidence,...r});
}
const birdShelter=make();const shelterRun=run(birdShelter,60,{hour:14,weather:'storm',season:'summer'},l=>l.animals.filter(a=>a.species==='鸟').every(a=>a.state==='rest'&&!a.flight&&distance(a.position,a.restSlot)<.13));
const birdShelterEvidence=birdShelter.animals.filter(a=>a.species==='鸟').map(a=>{const target=a.habitat.restSlots.find(s=>s.petId===a.id).point;return {id:a.id,node:a.flightNode,position:round(a.position),target,distance3D:+Math.hypot(...a.position.map((v,k)=>v-target[k])).toFixed(6),state:a.state}});
scenarios.push({name:'all-birds-shelter-actual-contact',seed:20261017,contactEvidence:birdShelterEvidence,...shelterRun});
console.log('BIRD NEEDS',birdNeedEvidence,'BIRD REFUGE',birdShelterEvidence);

const localVisitResults=[];
for(const profile of manifest.animals)for(const kind of ['feed','call','pet']){
 const l=make(),a=l.get(profile.id);if(!l.capabilities(a)[kind])continue;
 l.human.habitat=a.habitat;l.human.grid=a.grid;l.human.position=a.habitat.humanSpawn.slice();
 if(kind==='feed')a.hunger=.8;
 const command=l.command(a.id,kind),target=l.human.task?.foodTarget?.slice();
 const r=run(l,120,env,l=>l.events.some(e=>e.kind===kind+'-complete'||e.kind==='interaction-unavailable'));
 const completed=l.events.some(e=>e.kind===kind+'-complete'),actor=l.get(a.id),contactDistance=distance(l.human.position,actor.position),foodTargetDistance=target?Math.hypot(...actor.position.map((v,k)=>v-target[k])):null;
 localVisitResults.push({id:a.id,species:a.species,kind,callPolicy:kind==='call'&&a.species==='鸟'?'Respond at validated feeder node without arbitrary ground walking':undefined,command,completed,secondsRun:r.metrics.secondsRun,human:round(l.human.position),animal:round(actor.position),contactDistance:+contactDistance.toFixed(5),foodTarget:target,foodTargetDistance:foodTargetDistance===null?null:+foodTargetDistance.toFixed(5),metrics:r.metrics,events:r.events.filter(e=>[kind+'-complete','interaction-unavailable'].includes(e.kind))});
}
console.log('LOCAL VISITS',localVisitResults.length,'FAILED',localVisitResults.filter(r=>!r.completed).map(r=>[r.id,r.kind,r.secondsRun]));
const mixedSocialResults=[];
for(const id of ['02_cat_calico','03_cat_british_blue']){
 const l=make(),actor=l.get(id),phases=new Set(),states=new Set(),command=l.command(id,'social');
 const r=run(l,60,env,l=>{const p=l.pairs.find(p=>p.a.id===id||p.b.id===id);if(p){phases.add(p.phase);states.add(p.a.state);states.add(p.b.state);}return l.events.some(e=>e.kind==='social-complete'&&e.ids.includes(id))});
 mixedSocialResults.push({id,habitat:actor.habitat.id,command,completed:r.metrics.finished,observedPhases:[...phases],observedStates:[...states],noChase:!phases.has('play')&&!states.has('play'),...r});
}
console.log('CAT DOG SOCIAL',mixedSocialResults.map(r=>({id:r.id,complete:r.completed,phases:r.observedPhases,noChase:r.noChase})));
const afterRain=make();const rainExposure=run(afterRain,120,{hour:14,weather:'rain',season:'summer'}),rainCommand=afterRain.command('07_dog_shiba','pet');
const rainPet=run(afterRain,120,env,l=>l.events.some(e=>e.kind==='pet-complete'));
scenarios.push({name:'rain-120s-then-shiba-pet-120s',seed:20261017,rainExposureMetrics:rainExposure.metrics,command:rainCommand,...rainPet});
console.log('AFTER RAIN PET',rainPet.metrics.finished,rainPet.metrics.secondsRun,rainPet.metrics.humanUnderLowCanopySamples);

const radiusMismatches=manifest.animals.map(a=>({id:a.id,radius:a.radius,clearance:navigation.habitats.find(h=>h.petIds.includes(a.id)).clearance})).filter(a=>a.radius>a.clearance);
const feedFailures=seedSweeps.filter(r=>r.kind==='feed'&&!r.finished),petFailures=seedSweeps.filter(r=>r.kind==='pet'&&!r.finished);
const findingCandidates=[
 {id:'F1',priority:'P1',title:'Human interaction endpoint can be permanently occupied by target animal',evidence:{feedFailedSeeds:feedFailures.map(r=>r.seed),petFailedSeeds:petFailures.map(r=>r.seed),feed120s:scenarios.find(s=>s.name==='f-shiba-feed').summary.human,animal:scenarios.find(s=>s.name==='f-shiba-feed').summary.animals.find(a=>a.id==='07_dog_shiba')},cause:'startApproach snaps fixed human and dog offsets to adjacent 0.5m grid points. Their actual radius sum plus stop margin is .58298m, so human goal only .5m away from the dog is dynamically unreachable. updateHuman has no approach timeout or valid standoff completion fallback.',suggestion:'Choose human/animal endpoints jointly with real radii and available legal cells. Replan occupied goals; allow completion at validated standoff rather than waiting forever for exact grid goal.'},
 {id:'F2',priority:'P1',title:'Animals can pass through stationary human',evidence:scenarios[0].metrics.worstPair,cause:'move hard collision predicate o.air<=.4 excludes the human because human.air is undefined. Steering repulsion alone permits deep overlap.',suggestion:'Normalize air to zero for all ground agents or use (o.air||0)<=.4 in every separation predicate.'},
 {id:'F3',priority:'P1',title:'Airborne social initiation can restart old flight path and teleport bird',evidence:scenarios[0].metrics.maxAnimalStepDetail,cause:'fly() selects its path from perchIndex while a bird can be midway through an existing flight. updatePairs calls fly unconditionally in bird-start, so current position jumps to an old perch-based route.',suggestion:'Reserve or defer bird interaction until existing flight reaches a perch; preserve current path position when requesting another flight.'},
 {id:'F4',priority:'P1',title:'Some animals remain away from their weather refuge',evidence:scenarios.find(s=>s.name.startsWith('storm-shelter')).summary.animals.filter(a=>a.restTargetDistance>1.5),cause:'Inspect current shelter arrival and occupied destination handling against these remaining positions.',suggestion:'Track shelter arrival or proximity separately from rest action; weather must route outdoor resting animals to their own actual sheltered slot.'},
 {id:'F5',priority:'P2',title:'Bird feeding completes without bird reaching feeding station',evidence:{human:birdRun.summary.human,bird:birdRun.summary.animals.find(a=>a.id==='12_bird_budgie_green'),food:navigation.habitats.find(h=>h.id==='f-bird-sanctuary').food},cause:'startApproach sets a ground path on an airborne bird, but update skips ground movement when air>.1. A later fly() clears its path, satisfying feed path-empty condition even though no food arrival occurred.',suggestion:'Define an elevated bird feeder destination and flight approach, or suppress unsupported bird feed until contact is implemented. Test physical proximity and appropriate action before completion.'},
 {id:'F6',priority:'P2',title:'Actual asset radii exceed sampled habitat clearance',evidence:radiusMismatches,cause:'Navigation was sampled before final animal dimensions. Pony radius .79466 exceeds .6 clearance; golden .44715 exceeds .42. This is a coverage gap, not proof of a current mesh intersection.',suggestion:'Resample local habitat and edge geometry with final asset radius or validate its actual oriented footprint along every permitted route.'}
];
const birdFinal=birdRun.summary.animals.find(a=>a.id==='12_bird_budgie_green'),birdHabitat=navigation.habitats.find(h=>h.id==='f-bird-sanctuary'),birdTarget=birdHabitat.feederPoint||birdHabitat.food;
const conditions={F1:feedFailures.length>0||petFailures.length>0,F2:scenarios[0].metrics.minPairGap<-.02,F3:scenarios[0].metrics.maxAnimalStep>.15,F4:findingCandidates.find(f=>f.id==='F4').evidence.length>0,F5:birdRun.metrics.finished&&(distance(birdFinal.position,birdTarget)>.25||Math.abs(birdFinal.position[1]-birdTarget[1])>.15),F6:radiusMismatches.length>0};
const findings=findingCandidates.filter(f=>conditions[f.id]);
const crossFailures=scenarios.filter(s=>s.name.startsWith('cross-town-')&&!s.metrics.finished);
if(crossFailures.length)findings.push({id:'R1',priority:'P1',title:'Cross-town visit fails to finish after actual travel',evidence:crossFailures.map(s=>({name:s.name,metrics:s.metrics,human:s.summary.human,events:s.events.filter(e=>['interaction-unavailable','visit-travel','local-visit'].includes(e.kind))})),suggestion:'Check phase clocks separately from total travel elapsed; approaching should receive its own timeout after travel.'});
const illegalScenarios=scenarios.filter(s=>s.metrics&&(s.metrics.invalidAnimalSamples||s.metrics.invalidHumanSamples));
if(illegalScenarios.length)findings.push({id:'R2',priority:'P1',title:'Ground entity occupies a grid cell removed by runtime props',evidence:illegalScenarios.map(s=>({name:s.name,animalSamples:s.metrics.invalidAnimalSamples,humanSamples:s.metrics.invalidHumanSamples,first:s.metrics.firstInvalid})),suggestion:'After obstacle pruning, relocate initial ground entities onto the remaining reachable legal graph; keep airborne flight validation separate.'});
if(birdNeedEvidence.some(e=>!e.completed||e.distance3D>.15))findings.push({id:'R3',priority:'P1',title:'Bird autonomous food or water contact did not finish',evidence:birdNeedEvidence});
if(!shelterRun.metrics.finished||birdShelterEvidence.some(e=>e.distance3D>.15))findings.push({id:'R4',priority:'P1',title:'Bird refuge contact did not finish',evidence:birdShelterEvidence});
const failedVisits=localVisitResults.filter(r=>!r.completed||(r.kind==='feed'&&r.foodTargetDistance>.3)||(r.kind==='call'&&(r.species==='鸟'?r.foodTargetDistance>.3:r.contactDistance>1.85)));
if(failedVisits.length)findings.push({id:'R5',priority:'P1',title:'Local roster interaction did not complete or lacks actual contact',evidence:failedVisits});
const staticFailures=[...scenarios.filter(s=>s.metrics).map(s=>({name:s.name,...s.metrics})),...localVisitResults.map(s=>({name:s.id+' '+s.kind,...s.metrics}))].filter(m=>m.minimumStaticPropGap<-.005);
if(staticFailures.length)findings.push({id:'R6',priority:'P1',title:'Ground agent intersects a declared static prop disc',evidence:staticFailures.map(m=>({name:m.name,gap:m.minimumStaticPropGap,worst:m.worstStaticProp}))});
const freeBirdCheck=scenarios.find(s=>s.name==='free-120s-real-20-animals').metrics;
if(freeBirdCheck.minimumBird3DGap<-.02)findings.push({id:'R7',priority:'P1',title:'Birds can occupy the same perch or intersect while flying',evidence:{minimumBird3DGap:freeBirdCheck.minimumBird3DGap,penetrationSamples:freeBirdCheck.birdPenetrationSamples,worstPair:freeBirdCheck.worstBirdPair},suggestion:'Reserve destination nodes and airspace, or route only into genuinely vacant perches; preserve waiting when safe capacity is unavailable.'});
if(mixedSocialResults.some(r=>!r.completed||!r.noChase))findings.push({id:'R8',priority:'P1',title:'Cat and dog greeting failed or entered chase play',evidence:mixedSocialResults.filter(r=>!r.completed||!r.noChase)});
const canopyFailures=[...scenarios.filter(s=>s.metrics).map(s=>({name:s.name,...s.metrics})),...localVisitResults.map(s=>({name:s.id+' '+s.kind,...s.metrics}))].filter(m=>m.humanUnderLowCanopySamples>0);
if(canopyFailures.length)findings.push({id:'R9',priority:'P1',title:'Human enters a low animal canopy expanded by .3m',evidence:canopyFailures.map(m=>({name:m.name,samples:m.humanUnderLowCanopySamples,first:m.firstLowCanopyEntry}))});
if(!rainPet.metrics.finished)findings.push({id:'R10',priority:'P1',title:'Shiba pet interaction after 120s of rain did not finish',evidence:{command:rainCommand,metrics:rainPet.metrics,summary:rainPet.summary,events:rainPet.events}});
const tests=spawnSync(process.execPath,['--test',path.join(root,'src/animal-simulation.test.js')],{encoding:'utf8'});const outputText=tests.stdout+tests.stderr;
const unitTests={exitCode:tests.status,total:+(outputText.match(/(?:#|ℹ) tests (\d+)/)?.[1]||0),passed:+(outputText.match(/(?:#|ℹ) pass (\d+)/)?.[1]||0),failed:+(outputText.match(/(?:#|ℹ) fail (\d+)/)?.[1]||0)};
const output={status:findings.length?'AUDIT_FINDINGS':'PASS',date:'2026-10-18',auditor:'animal_navigation',scope:'Headless actual 20-animal manifest and actual town navigation; graph validity, runtime state and runtime static prop-disc audit. Static mesh collisions are covered by navigation-validation; renderer/animation QA remains outside this audit.',sourceHashes,protectedFilesUnchanged:protectedFiles.every(p=>sha(path.join(root,p))===sourceHashes[p]),unitTests,findings,resolvedFindingIds:Object.keys(conditions).filter(id=>!conditions[id]),radiusMismatches,seedSweeps,birdNeedEvidence,birdShelterEvidence,localVisitResults,mixedSocialResults,scenarios};
const outputFile=process.argv[2]||path.join(root,'qa/runtime-nav-retest.json');
fs.writeFileSync(outputFile,JSON.stringify(output,null,2));
console.log('WROTE',outputFile,'FINDINGS',findings.map(f=>f.id));
