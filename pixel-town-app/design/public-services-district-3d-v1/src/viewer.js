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
overview:{title:'B 区 · 公共服务庭院',target:[0,1,0],eye:[79,91,111],desc:'小学、两层图书馆、诊所、社区中心、邮局与警务站围绕公共庭院。已有建筑按原尺寸落位，四栋新建筑补齐公共服务。'},
plan:{title:'总平面 · 上北下南',target:[0,0,0],eye:[0,130,.01],desc:'85 × 62.5 米地块，六栋分列南北。4 米主步道连接东西住宅区；南入口沿邮局后侧公共步道绕行接入庭院。'},
school:{id:'B01',title:'B01 · 溪畔小学',target:[-26.125,1,-15.25],eye:[-2,31,15],desc:'两间教室各 12 个学生座位，配教师工作位、卫生间与 18 × 8 米小操场。入口步道从操场东侧绕行，保持活动空间。'},
library:{id:'B02',title:'B02 · 溪畔图书馆',target:[1.875,1,-13.5],eye:[25,29,16],desc:'保留原有两层平顶图书馆、22 级楼梯及真实楼板开口。共 30 个阅读座位、8 组双面书架；可切换一层与二层。'},
clinic:{id:'B03',title:'B03 · 溪畔诊所',target:[28.25,1,-13.5],eye:[50,27,15],desc:'保留平顶、医疗红十字、接待候诊、两间诊室和护理观察。区块副本新增东侧辅助门，连接独立侧通道。'},
community:{id:'B04',title:'B04 · 邻里社区中心',target:[-26.125,1,17],eye:[-2,30,-13],desc:'共享活动厅与协商长桌、儿童手作角、独立咨询室、茶水和卫生间，为邻里活动与日常交流留出空间。'},
post:{id:'B05',title:'B05 · 小镇邮局',target:[.5,1,17],eye:[25,29,-13],desc:'北侧寄取件窗口与自助包装，后侧为信件分拣和包裹架。南侧收发门、坡道与货物小推车连接后勤步道。'},
police:{id:'B06',title:'B06 · 社区警务站',target:[27.625,1,17],eye:[51,29,-13],desc:'便民接待、等候座位、两处值班工作位、独立社区调解室、装备柜与卫生间。面向庭院的开放式社区服务站。'},
court:{title:'树荫下的公共庭院',target:[4,1,4],eye:[76,48,61],desc:'自然花灌木、树荫长椅与阅读廊架组成安静的公共庭院。诊所门前设置等候小庭，小学活动场地与主通道分开。'}
};
function applyVisibility(){
 if(!current)return;const selected=views[mode].id,show=document.querySelector('#roof').checked,solo=document.querySelector('#isolate').checked,floor=Number(document.querySelector('#floor').value);
 for(const node of current.children){
  const isBuilding=/^B0[1-6]_/.test(node.name),id=node.name.slice(0,3),part=node.name.slice(4);
  let visible=true;
  if(solo&&selected)visible=isBuilding?id===selected:['Ground','Paths'].includes(node.name);
  if(node.name.endsWith('_Roof'))visible=visible&&((selected&&id!==selected)?true:show);
  if(selected===id&&!show){if(['Front','FrontFacade','EastFacade'].includes(part))visible=false;if(id==='B02'&&((floor===1&&part.startsWith('Upper'))||(floor===2&&['UpperFront','UpperEast'].includes(part))))visible=false;}
  if(!selected&&!show&&id==='B02'&&part.startsWith('Upper'))visible=false;
  node.visible=visible;
 }
 dirty=true;
}
function view(k){mode=k;const v=views[k];document.querySelector('#caption').textContent=v.title;document.querySelector('#description').textContent=v.desc;document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===k)));document.querySelector('#roof').checked=!v.id&&k!=='plan';document.querySelector('#isolate').checked=!!v.id;document.querySelector('#isolate').disabled=!v.id;document.querySelector('#floor').disabled=v.id!=='B02';document.querySelector('#floor').value='1';applyVisibility();const t=new THREE.Vector3(...v.target),p=new THREE.Vector3(...v.eye);if(camera.aspect<1)p.sub(t).multiplyScalar(1.5).add(t);camera.position.copy(p);controls.target.copy(t);controls.update();dirty=true;}
document.querySelector('#floor').onchange=()=>{document.querySelector('#roof').checked=false;applyVisibility();if(mode==='library'){controls.target.y=Number(document.querySelector('#floor').value)===2?4.5:1;dirty=true;}};
function resize(){renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();dirty=true;}new ResizeObserver(resize).observe(host);resize();
function bytes(){return Uint8Array.from(atob(window.B_ASSET),c=>c.charCodeAt(0));}
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));document.querySelector('#roof').onchange=applyVisibility;document.querySelector('#isolate').onchange=applyVisibility;document.querySelector('#reset').onclick=()=>view(mode);document.querySelector('#auto').onchange=e=>{controls.autoRotate=e.target.checked;controls.autoRotateSpeed=.35;};document.querySelector('#download').onclick=()=>download(new Blob([bytes()],{type:'model/gltf-binary'}),'B-public-services.glb');document.querySelector('#capture').onclick=()=>{renderer.render(scene,camera);renderer.domElement.toBlob(b=>download(b,'B-'+mode+'.png'));};
new GLTFLoader().parseAsync(bytes().buffer,'').then(g=>{current=g.scene;scene.add(current);document.querySelector('#status').textContent='拖动旋转 · 滚轮缩放 · 右键平移';view('overview');}).catch(e=>{document.querySelector('#status').textContent='载入失败：'+e.message;throw e;});
renderer.setAnimationLoop(()=>{controls.update();if(dirty){renderer.render(scene,camera);dirty=false;}});
window.civicViewer={scene,camera,renderer,controls,view,get current(){return current},get mode(){return mode}};
