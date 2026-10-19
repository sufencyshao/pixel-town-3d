import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const host=document.querySelector('#canvas'),renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.15;host.append(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color('#e8e7df');scene.add(new THREE.HemisphereLight('#fff3df','#7d9279',2.5));
for(const [pos,color,power] of [[[ -30,65,40],'#fff3df',3],[[40,25,-30],'#dceaf0',1]]){const l=new THREE.DirectionalLight(color,power);l.position.set(...pos);scene.add(l);}
const camera=new THREE.PerspectiveCamera(38,1,.1,500),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.maxPolarAngle=Math.PI*.49;controls.minDistance=5;controls.maxDistance=240;
let current,mode='overview',dirty=true;controls.addEventListener('change',()=>dirty=true);
const views={
overview:{title:'H 区 · 日常商业街',target:[0,1,0],eye:[79,86,103],desc:'六间小店面向一条东西步行巷。保留已有咖啡厅及露台，补齐烘焙、小餐馆、杂货、花店和理发店。'},
plan:{title:'总平面 · 上北下南',target:[0,0,0],eye:[0,125,.01],desc:'85 × 55 米地块，北排餐饮、南排生活小店。4.5 米主步道贯通东西，北口连接大树广场；后勤沿两侧支路和店后步道通行。'},
cafe:{id:'H01',title:'H01 · 溪畔咖啡厅',target:[-26.5,1,-11.5],eye:[-4,28,17],desc:'按原尺寸纳入已有模型：18 个室内座位、4 个露台座位、咖啡吧、备餐储物和卫生间。保留原材质与店招贴图，后门接上收货通道。'},
bakery:{id:'H02',title:'H02 · 麦香烘焙坊',target:[1.75,1,-11.5],eye:[25,29,17],desc:'面包和蛋糕展示柜、四座品尝角，后场配双层烤炉、揉面台、搅拌机、洗涤和卫生间。麦麦、陶麦、糖糖的工作空间。'},
restaurant:{id:'H03',title:'H03 · 小锅家常食堂',target:[28.125,1,-11.5],eye:[51,28,17],desc:'16 座用餐区、收银和两组户外桌。后场设置备餐台、炉灶、排烟罩、洗涤、冷藏与卫生间，后门单独收货。'},
grocer:{id:'H04',title:'H04 · 籽杏杂货铺',target:[-26.5,1,15],eye:[-3,29,-14],desc:'蔬果、干货、饮品冷柜与收银台，三组货架留出中央通道；南侧后仓、收货门和卫生间。店前有小型蔬果陈列。'},
florist:{id:'H05',title:'H05 · 花苔花店',target:[1.75,1,15],eye:[25,29,-14],desc:'鲜花桶、绿植台与花艺工作桌，搭配包装卷纸、清洗和保鲜柜。屋顶玻璃采光顶下预留真实开口，店前展示鲜花。'},
salon:{id:'H06',title:'H06 · 银梳理发屋',target:[28.125,1,15],eye:[51,28,-14],desc:'三组剪发椅和镜台、两组洗发位，配预约接待、等候沙发、毛巾柜与卫生间。门旁的三色理发柱帮助识别店面。'},
street:{title:'沿街的小店与树荫',target:[0,1,1.5],eye:[56,30,-44],desc:'条纹遮阳棚、外摆桌、花束、蔬果和长椅退在店前空间内，中央步行带保持连续；旋转可以查看两侧店面。'}
};
function applyVisibility(){
 if(!current)return;const selected=views[mode].id,show=document.querySelector('#roof').checked,solo=document.querySelector('#isolate').checked;
 for(const node of current.children){const isBuilding=/^H0[1-6]_/.test(node.name),id=node.name.slice(0,3),part=node.name.slice(4);let visible=true;if(solo&&selected)visible=isBuilding?id===selected:['Ground','Paths'].includes(node.name);if(part==='Roof')visible=visible&&((selected&&id!==selected)?true:show);if(id===selected&&!show&&['Front','East'].includes(part))visible=false;node.visible=visible;}dirty=true;
}
function view(k){mode=k;const v=views[k];document.querySelector('#caption').textContent=v.title;document.querySelector('#description').textContent=v.desc;document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===k)));document.querySelector('#roof').checked=!v.id&&k!=='plan';document.querySelector('#isolate').checked=!!v.id;document.querySelector('#isolate').disabled=!v.id;applyVisibility();const t=new THREE.Vector3(...v.target),p=new THREE.Vector3(...v.eye);if(camera.aspect<1)p.sub(t).multiplyScalar(1.5).add(t);camera.position.copy(p);controls.target.copy(t);controls.update();dirty=true;}
function resize(){renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();dirty=true;}new ResizeObserver(resize).observe(host);resize();
function bytes(){return Uint8Array.from(atob(window.H_ASSET),c=>c.charCodeAt(0));}
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),2000);}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));document.querySelector('#roof').onchange=applyVisibility;document.querySelector('#isolate').onchange=applyVisibility;document.querySelector('#reset').onclick=()=>view(mode);document.querySelector('#auto').onchange=e=>{controls.autoRotate=e.target.checked;controls.autoRotateSpeed=.35;};document.querySelector('#download').onclick=()=>download(new Blob([bytes()],{type:'model/gltf-binary'}),'H-daily-shops.glb');document.querySelector('#capture').onclick=()=>{renderer.render(scene,camera);renderer.domElement.toBlob(b=>download(b,'H-'+mode+'.png'));};
new GLTFLoader().parseAsync(bytes().buffer,'').then(g=>{current=g.scene;scene.add(current);document.querySelector('#status').textContent='拖动旋转 · 滚轮缩放 · 右键平移';view('overview');}).catch(e=>{document.querySelector('#status').textContent='载入失败：'+e.message;throw e;});
renderer.setAnimationLoop(()=>{controls.update();if(dirty){renderer.render(scene,camera);dirty=false;}});
window.shopsViewer={scene,camera,renderer,controls,view,get current(){return current},get mode(){return mode}};
