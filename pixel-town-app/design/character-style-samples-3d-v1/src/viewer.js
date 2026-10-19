import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const stages=[],labels={Idle:'站立',Walk:'走路',Wave:'挥手'};let active='Idle',paused=false,elapsed=0,speed=1,ready=false;
const loader=new GLTFLoader();
function bytes(key){return Uint8Array.from(atob(window.SAMPLE_ASSETS[key]),c=>c.charCodeAt(0))}
const cameraViews={front:[0,1.12,4.05],angle:[1.65,1.16,3.7],side:[4.05,1.12,0],back:[0,1.12,-4.05]};
function applyCamera(key){for(const s of stages){s.camera.position.set(...cameraViews[key]);s.controls.target.set(0,.86,0);s.controls.update()}for(const b of document.querySelectorAll('[data-camera]'))b.setAttribute('aria-pressed',String(b.dataset.camera===key))}
function applyTime(time){for(const s of stages){const a=s.actions[active];a.time=THREE.MathUtils.euclideanModulo(time,a.getClip().duration);s.mixer.update(0)} }
function play(clip){active=clip;elapsed=0;for(const s of stages){s.mixer.stopAllAction();s.actions[clip].reset().play();s.host.querySelector('.clip-readout').textContent=labels[clip]+' · 骨骼动画';}for(const b of document.querySelectorAll('[data-clip]'))b.setAttribute('aria-pressed',String(b.dataset.clip===clip));applyTime(0);}
async function makeStage(key,id){
 const host=document.getElementById(id),renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;host.prepend(renderer.domElement);
 const scene=new THREE.Scene();scene.background=new THREE.Color('#edf0e7');scene.add(new THREE.HemisphereLight('#f8f8f1','#8a9a84',2.2));
 const sun=new THREE.DirectionalLight('#fff4e3',3.5);sun.position.set(3,6,4);sun.castShadow=true;sun.shadow.mapSize.set(1024,1024);Object.assign(sun.shadow.camera,{left:-2,right:2,top:3,bottom:-1,near:.1,far:15});sun.shadow.bias=-.0003;scene.add(sun);
 const fill=new THREE.DirectionalLight('#b7d4e2',1.1);fill.position.set(-3,2,-2);scene.add(fill);
 const ground=new THREE.Mesh(new THREE.CylinderGeometry(.79,.83,.055,64),new THREE.MeshStandardMaterial({color:'#d9dfd0',roughness:.95}));ground.position.y=-.04;ground.receiveShadow=true;scene.add(ground);
 const floor=new THREE.Mesh(new THREE.PlaneGeometry(30,30),new THREE.ShadowMaterial({opacity:.12}));floor.rotation.x=-Math.PI/2;floor.position.y=-.07;floor.receiveShadow=true;scene.add(floor);
 const camera=new THREE.PerspectiveCamera(30,1,.03,35),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=1.7;controls.maxDistance=7;controls.maxPolarAngle=Math.PI*.51;controls.target.set(0,.86,0);camera.position.set(...cameraViews.angle);controls.update();
 const g=await loader.parseAsync(bytes(key).buffer,'');scene.add(g.scene);g.scene.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
 const mixer=new THREE.AnimationMixer(g.scene),actions=Object.fromEntries(g.animations.map(c=>[c.name,mixer.clipAction(c)]));if(!['Idle','Walk','Wave'].every(c=>actions[c]))throw new Error(key+' 缺少动作');
 const helper=new THREE.SkeletonHelper(g.scene);helper.visible=false;helper.material.depthTest=false;helper.material.transparent=true;helper.material.opacity=.8;scene.add(helper);
 const s={key,host,renderer,scene,camera,controls,model:g.scene,mixer,actions,helper};stages.push(s);
 new ResizeObserver(()=>{renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix()}).observe(host);
 renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();return s;
}
function download(key){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([bytes(key)],{type:'model/gltf-binary'}));a.download='Ache-'+key+'.glb';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000)}
for(const b of document.querySelectorAll('button'))b.disabled=true;
Promise.all([makeStage('A-chibi','view-A'),makeStage('B-cartoon','view-B'),makeStage('C-natural','view-C')]).then(()=>{stages.sort((a,b)=>a.key.localeCompare(b.key));ready=true;play('Idle');for(const b of document.querySelectorAll('button'))b.disabled=false;document.getElementById('load-status').textContent='三个样例已就绪 · 可独立旋转';}).catch(e=>{document.getElementById('load-status').textContent='载入失败：'+e.message;throw e});
for(const b of document.querySelectorAll('[data-clip]'))b.onclick=()=>play(b.dataset.clip);
for(const b of document.querySelectorAll('[data-camera]'))b.onclick=()=>applyCamera(b.dataset.camera);
for(const b of document.querySelectorAll('[data-download]'))b.onclick=()=>download(b.dataset.download);
document.getElementById('pause').onclick=()=>{paused=!paused;document.getElementById('pause').textContent=paused?'继续':'暂停';document.getElementById('pause').setAttribute('aria-pressed',String(paused))};
document.getElementById('bones').onchange=e=>stages.forEach(s=>s.helper.visible=e.target.checked);
document.getElementById('speed').onchange=e=>speed=+e.target.value;
document.getElementById('timeline').oninput=e=>{if(!ready)return;paused=true;document.getElementById('pause').textContent='继续';document.getElementById('pause').setAttribute('aria-pressed','true');elapsed=+e.target.value/1000*stages[0].actions[active].getClip().duration;applyTime(elapsed)};
let last=performance.now();document.addEventListener('visibilitychange',()=>last=performance.now());
function frame(now){requestAnimationFrame(frame);const dt=Math.min(.1,(now-last)/1000);last=now;if(document.hidden)return;if(ready){if(!paused){elapsed+=dt*speed;applyTime(elapsed)}const duration=stages[0].actions[active].getClip().duration,fraction=(elapsed%duration)/duration;if(document.activeElement!==document.getElementById('timeline'))document.getElementById('timeline').value=String(Math.round(fraction*1000));document.getElementById('progress').textContent=Math.round(fraction*100)+'%';}for(const s of stages){s.controls.update();s.renderer.render(s.scene,s.camera)}}requestAnimationFrame(frame);
window.characterSamples={stages,play,applyCamera,applyTime,get ready(){return ready},get active(){return active},get elapsed(){return elapsed},get paused(){return paused}};
