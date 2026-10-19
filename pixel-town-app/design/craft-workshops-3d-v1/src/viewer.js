import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const host=document.querySelector('#canvas'),renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;host.append(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color('#e8e7df');scene.add(new THREE.HemisphereLight('#fff3df','#7d9279',2.5));
for(const [pos,color,power] of [[[ -30,65,40],'#fff3df',3],[[40,25,-30],'#dceaf0',1]]){const l=new THREE.DirectionalLight(color,power);l.position.set(...pos);scene.add(l);}
const camera=new THREE.PerspectiveCamera(38,1,.1,500),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.maxPolarAngle=Math.PI*.49;controls.minDistance=5;controls.maxDistance=240;
let current,mode='overview',dirty=true;controls.addEventListener('change',()=>dirty=true);
const views={
overview:{title:'手作工作区全景',target:[0,1,0],eye:[94,102,123],desc:'木工、维修、绘画与音乐围绕一条展示小巷展开，工作台与街边树荫共同构成小镇的日常。'},
plan:{title:'总平面 · 上北下南',target:[0,0,0],eye:[0,141,.01],desc:'75 × 55 米地块。东口通往大树广场，南口接田园，西侧及北侧设置后勤路。'},
wood:{id:'D01',title:'D01 · 木工坊',target:[-18.75,1,-10],eye:[5,28,18],desc:'四张木工台、台钳、木材架、车床和工具墙；西后门接卸货通道。大森与榆棠的工作场景。'},
repair:{id:'D02',title:'D02 · 修理铺',target:[17,1,-10],eye:[46,29,19],desc:'接件柜台、电子维修台、两处自行车维修位与零件收纳。北侧宽门用于收货，正门面向小巷。'},
art:{id:'D03',title:'D03 · 共享画室',target:[-18.75,1,14.125],eye:[6,29,-14],desc:'六组画架、两张共用画桌、洗笔台与作品墙。屋顶采光天窗下预留真实开口，南侧有小型雕塑花园。'},
music:{id:'D04',title:'D04 · 排练室',target:[17,1,14.125],eye:[47,29,-15],desc:'入口缓冲区、休息角、钢琴与合奏台；配鼓组、吉他、音箱和麦克风。吸声板为模型示意。'},
lane:{title:'手作展示小巷',target:[0,1,2.5],eye:[66,24,31],desc:'四栋主入口面对小巷，长椅与小树设在通道两旁；4 米连续步行带连到东侧广场。'}
};
function applyVisibility(){if(!current)return;const selected=views[mode].id,show=document.querySelector('#roof').checked,solo=document.querySelector('#isolate').checked;for(const node of current.children){const id=node.name.slice(0,3),isBuilding=/^D0[1-4]_/.test(node.name);node.visible=!isBuilding||!solo||!selected||id===selected;if(node.name.endsWith('_Roof'))node.visible=node.visible&&(selected&&id!==selected?true:show);if(node.name.endsWith('_Front')&&id===selected&&!show)node.visible=false;}dirty=true;}
function view(k){mode=k;const v=views[k];document.querySelector('#caption').textContent=v.title;document.querySelector('#description').textContent=v.desc;document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===k)));document.querySelector('#roof').checked=!v.id&&k!=='plan';document.querySelector('#isolate').checked=!!v.id;document.querySelector('#isolate').disabled=!v.id;applyVisibility();const t=new THREE.Vector3(...v.target),p=new THREE.Vector3(...v.eye);if(camera.aspect<1)p.sub(t).multiplyScalar(1.5).add(t);camera.position.copy(p);controls.target.copy(t);controls.update();dirty=true;}
function resize(){renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();dirty=true;}new ResizeObserver(resize).observe(host);resize();
function bytes(){return Uint8Array.from(atob(window.D_ASSET),c=>c.charCodeAt(0));}
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));document.querySelector('#roof').onchange=applyVisibility;document.querySelector('#isolate').onchange=applyVisibility;document.querySelector('#reset').onclick=()=>view(mode);document.querySelector('#auto').onchange=e=>{controls.autoRotate=e.target.checked;controls.autoRotateSpeed=.35;};document.querySelector('#download').onclick=()=>download(new Blob([bytes()],{type:'model/gltf-binary'}),'D-craft-workshops.glb');document.querySelector('#capture').onclick=()=>{renderer.render(scene,camera);renderer.domElement.toBlob(b=>download(b,'D-'+mode+'.png'));};
new GLTFLoader().parseAsync(bytes().buffer,'').then(g=>{current=g.scene;scene.add(current);document.querySelector('#status').textContent='拖动旋转 · 滚轮缩放 · 右键平移';view('overview');}).catch(e=>{document.querySelector('#status').textContent='载入失败：'+e.message;throw e;});
renderer.setAnimationLoop(()=>{controls.update();if(dirty){renderer.render(scene,camera);dirty=false;}});
window.craftViewer={scene,camera,renderer,controls,view,get current(){return current},get mode(){return mode}};
