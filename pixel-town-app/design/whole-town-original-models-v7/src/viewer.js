import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {AnimalWorld} from './animal-world.js';
import {TownEnvironment} from './environment-renderer.js';
import {WEATHER,SEASONS,weatherAllowed} from './environment-state.js';
const meta=window.TOWN_META,host=document.querySelector('#canvas');
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true,logarithmicDepthBuffer:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.35));renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.12;host.prepend(renderer.domElement);
const scene=new THREE.Scene();
const camera=new THREE.PerspectiveCamera(38,1,1,2200),controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=10;controls.maxDistance=1400;controls.maxPolarAngle=Math.PI*.49;
const environment=new TownEnvironment(scene,camera,renderer,meta,window.TOWN_ENV,syncEnvironmentUI);
let animalWorld;let current,zone='all',mode='exterior',floor=1,dirty=true,detailView=false;const labels=[];controls.addEventListener('change',()=>dirty=true);
const descriptions={A:'六栋双层花园别墅与主角泳池小屋，保留庭院、菜园及共享绿地。',B:'小学、二层图书馆、红十字诊所、社区中心、邮局和警务站围合公共庭院。',C:'五栋三至五层的河畔公寓，共 40 套住宅，以中央步道连接各楼入口。',D:'木工坊、修理铺、共享画室与排练室，店前展示巷连接中央广场。',E:'大树广场、环座、市集摊位、浅水景和阅读廊架，是小镇日常相遇的中心。',F:'动物诊所、宠物草地、小舞台和安静栖息角通向河岸，两座桥连接对岸自然步道。',G:'温室、工具屋、四块轮作田与果园，沿田间步道连接商业街。',H:'已有咖啡厅与烘焙坊、食堂、杂货铺、花店及理发屋，六店入口面向步行巷。',I:'六间客房的旅店、公交候车与接驳小巴、两车位消防站和独立车辆前场。'};
function visibility(){if(!current)return;const solo=document.querySelector('#isolate').checked,cut=!document.querySelector('#roof').checked;
 for(const o of current.children){const z=o.name[0],part=o.name.slice(3);let visible=!solo||zone==='all'||z===zone;const selected=zone==='all'||z===zone;
  if(selected&&cut){if(/Roof|roof/.test(part))visible=false;const match=/__L(\d{2})_/.exec(part)||/Inn_L(\d{2})_/.exec(part);if(match){const level=+match[1];if(level>floor)visible=false;if(level===floor&&/Front|East|South/.test(part))visible=false;}else if(z==='B'&&part.startsWith('B02_')){if(floor===1&&part.includes('Upper'))visible=false;if(/Front|East/.test(part))visible=false;}else if(/Front|Vet_East|Fire_South|Fire_East/.test(part))visible=false;}
  if(z==='E'&&!document.querySelector('#market').checked&&/Market_|Event_/.test(part))visible=false;
  if(!document.querySelector('#canopy').checked&&/Landmark_Canopy/.test(part))visible=false;
  if(z==='T'&&!document.querySelector('#details').checked&&/Street_|Road_|Crosswalk|Signals|Utilities|Wires|Benches|Bins|Wayfinding|Bollards|Drainage|Lamp_/.test(part))visible=false;if(part==='Wires'&&!document.querySelector('#wires').checked)visible=false;o.visible=visible;
 }animalWorld?.setVisibility(zone,solo,cut);dirty=true;
}
function view(m){if(animalWorld)animalWorld.viewMode='town';detailView=false;mode=m;document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===m)));document.querySelector('#roof').checked=m!=='interior';let target,eye;
 if(zone==='all'){target=new THREE.Vector3(12,2,0);eye=m==='plan'?new THREE.Vector3(12,460,.01):new THREE.Vector3(280,290,355);}
 else{const z=meta.zones[zone],[x,y]=z.center;target=new THREE.Vector3(x,zone==='C'?5:1,-y);const s=Math.max(...z.size)*1.15;eye=m==='plan'?new THREE.Vector3(x,s*1.7,-y+.01):new THREE.Vector3(x+s*.85,s*.95,-y+s*1.1);}
 const bounds=new THREE.Box3();for(const o of current.children)if(zone==='all'||o.name.startsWith(zone+'__'))bounds.expandByObject(o);const back=eye.clone().sub(target).normalize(),right=new THREE.Vector3().crossVectors(new THREE.Vector3(0,1,0),back).normalize(),up=new THREE.Vector3().crossVectors(back,right),tan=Math.tan(THREE.MathUtils.degToRad(camera.fov/2));let distance=0;for(const x of [bounds.min.x,bounds.max.x])for(const y of [bounds.min.y,bounds.max.y])for(const z of [bounds.min.z,bounds.max.z]){const rel=new THREE.Vector3(x,y,z).sub(target);distance=Math.max(distance,rel.dot(back)+1.12*Math.max(Math.abs(rel.dot(right))/(tan*camera.aspect),Math.abs(rel.dot(up))/tan));}eye.copy(target).addScaledVector(back,distance);camera.position.copy(eye);controls.target.copy(target);controls.update();visibility();document.querySelector('#caption').textContent=(zone==='all'?'九区全景':zone+' · '+meta.zones[zone].name)+' / '+({exterior:'完整外观',plan:'上北下南',interior:floor+' 层剖切'}[m]);dirty=true;
}
function district(z){zone=z;floor=1;document.querySelector('#floor').value='1';document.querySelector('#isolate').disabled=z==='all';document.querySelector('#isolate').checked=false;document.querySelectorAll('[data-zone]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.zone===z)));document.querySelector('#name').textContent=z==='all'?'九个片区，一个小镇':z+' · '+meta.zones[z].name;document.querySelector('#description').textContent=z==='all'?'主体道路统一为柏油马路，带车道线、行驶箭头与斑马线；区块内建筑之间保留浅色石板步道。街角、河岸增设路灯、长椅和导向牌。':descriptions[z];document.querySelector('#floor').max=z==='C'?5:z==='A'||z==='B'||z==='I'?2:1;document.querySelector('#floor-value').textContent='1 层';view('exterior');}
function detail(key){district('all');detailView=true;const v={crossing:[[-99,29,37],[-130,1,2.5],'过街路口'],river:[[146,26,106],[119,1,82],'河岸座椅'],arrival:[[75,25,141],[49,1,104],'到达街角']}[key];camera.position.set(...v[0]);controls.target.set(...v[1]);controls.update();document.querySelector('#labels').checked=false;document.querySelector('#caption').textContent=v[2]+' / 街道细节';dirty=true;}
for(const b of document.querySelectorAll('[data-detail]'))b.onclick=()=>detail(b.dataset.detail);
function resize(){renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();if(current&&!detailView)view(mode);dirty=true;}new ResizeObserver(resize).observe(host);resize();
function bytes(){return Uint8Array.from(atob(window.TOWN_ASSET),c=>c.charCodeAt(0))}
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),5000)}
for(const b of document.querySelectorAll('[data-zone]'))b.onclick=()=>district(b.dataset.zone);for(const b of document.querySelectorAll('[data-view]'))b.onclick=()=>view(b.dataset.view);
for(const id of ['roof','isolate','market','canopy','labels','details','wires'])document.querySelector('#'+id).onchange=visibility;
document.querySelector('#floor').oninput=e=>{floor=+e.target.value;document.querySelector('#floor-value').textContent=floor+' 层';view('interior')};document.querySelector('#reset').onclick=()=>view(mode);document.querySelector('#auto').onchange=e=>{controls.autoRotate=e.target.checked;controls.autoRotateSpeed=.25};document.querySelector('#download').onclick=()=>download(new Blob([bytes()],{type:'model/gltf-binary'}),'Town-complete.glb');document.querySelector('#capture').onclick=()=>{renderer.render(scene,camera);renderer.domElement.toBlob(b=>download(b,'Town-'+zone+'.png'))};
for(const z of Object.values(meta.zones)){const el=document.createElement('button');el.className='map-label';el.textContent=z.id+' '+z.name;el.onclick=()=>district(z.id);host.append(el);labels.push({el,p:new THREE.Vector3(z.center[0],z.id==='C'?20:8,-z.center[1])});}
new GLTFLoader().parseAsync(bytes().buffer,'').then(async g=>{current=g.scene;scene.add(current);environment.attach(current);document.querySelector('#status').textContent='拖动旋转 · 滚轮缩放 · 右键平移';district('all');animalWorld=await AnimalWorld.create({scene,camera,controls,renderer,host,environment,focusDistrict:z=>{district(z);detailView=true;}});window.townViewer.animals=animalWorld;}).catch(e=>{document.querySelector('#status').textContent='载入失败：'+e.message;throw e});
let lastFrame=performance.now();
document.addEventListener('visibilitychange',()=>{lastFrame=performance.now()});
renderer.setAnimationLoop(now=>{if(document.hidden){lastFrame=now;return;}if(now-lastFrame<32)return;const dt=Math.max(0,(now-lastFrame)/1000);lastFrame=now;controls.update();environment.update(dt,{target:controls.target,interior:mode==='interior',lampsVisible:!!current?.children.find(o=>o.name==='T__Lamp_Glow')?.visible});animalWorld?.update(dt);renderer.render(scene,camera);for(const {el,p} of labels){const v=p.clone().project(camera),show=zone==='all'&&document.querySelector('#labels').checked&&v.z<1&&Math.abs(v.x)<.97&&Math.abs(v.y)<.95;el.style.display=show?'block':'none';el.style.left=(v.x*.5+.5)*host.clientWidth+'px';el.style.top=(-v.y*.5+.5)*host.clientHeight+'px';}dirty=false});
function setText(id,value){const el=document.getElementById(id);if(el.textContent!==value)el.textContent=value}
function syncEnvironmentUI(s){
 const period=s.altitude< -6?'夜晚':s.hour<12&&s.hour<s.sunrise+1?'清晨':s.hour>12&&s.hour>s.sunset-1?'傍晚':'日间';
 const clock=h=>{const m=Math.round(h*60);return String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0')};
 setText('season-name',SEASONS[s.season].name);setText('season-day',s.autoSeasons?'第 '+s.seasonDay+' / '+s.seasonDays+' 天':'已固定季节');setText('season-note',SEASONS[s.season].note);setText('hud-season',SEASONS[s.season].name+' · '+(s.autoSeasons?'第 '+s.seasonDay+' / '+s.seasonDays+' 天':'固定季节'));
 setText('sunrise',clock(s.sunrise));setText('sunset',clock(s.sunset));setText('sun-altitude',s.altitude.toFixed(1)+'°');setText('daylength','白昼 '+Math.floor(s.dayLength)+' 小时 '+Math.round(s.dayLength%1*60)+' 分 · '+(s.altitude<0?'太阳在地平线下':'太阳在地平线上'));
 document.querySelector('#auto-seasons').checked=s.autoSeasons;
 for(const b of document.querySelectorAll('[data-season]'))b.setAttribute('aria-pressed',String(b.dataset.season===s.season));
 setText('snow-depth',(s.snowDepth*100).toFixed(1)+' cm');setText('river-rise','+'+Math.round(s.riverRise*100)+' cm');setText('wind-level',s.visual.wind>10?'强阵风':s.visual.wind>6?'大风':s.visual.wind>2?'有风':'微风');setText('hud-surface','积雪 '+(s.snowDepth*100).toFixed(1)+' cm · 河水 +'+Math.round(s.riverRise*100)+' cm');setText('clock',s.clock);setText('day','第 '+s.day+' 天');setText('period',period);setText('hud-clock',s.clock);setText('hud-weather',WEATHER[s.weather].name);setText('hud-light','第 '+s.day+' 天 · '+(s.night>.5?'路灯已亮':'日间照明'));
 const slider=document.querySelector('#time-slider');if(document.activeElement!==slider)slider.value=String(Math.floor(s.hour*60));if(document.activeElement!==document.querySelector('#time-input'))document.querySelector('#time-input').value=s.clock;
 setText('pause-time',s.paused?'继续时间':'暂停时间');document.querySelector('#pause-time').setAttribute('aria-pressed',String(s.paused));document.querySelector('#auto-weather').checked=s.autoWeather;
 for(const b of document.querySelectorAll('[data-weather]')){b.setAttribute('aria-pressed',String(b.dataset.weather===s.weather));b.disabled=!weatherAllowed(b.dataset.weather,s.season);b.title=b.disabled?'当前季节不出现此天气':'';}
 const text={sunny:'晴朗、干燥，路灯随日落自动亮起。',cloudy:'云团缓慢移动，天空保留透光间隙。',overcast:'云层覆盖，日照变柔，远处略有薄雾。',lightRain:'细雨飘落，铺装逐渐湿润。',rain:'持续降雨，雨滴与地面涟漪更加明显。',heavyRain:'密集雨幕、较强风势，远处能见度降低。',storm:'强风雨伴随闪电，河水上涨；雷声可单独开启。',lightSnow:'稀疏雪花，薄薄覆雪约 3 cm。',snow:'持续降雪，积雪逐渐加厚至约 12 cm。',heavySnow:'密集风雪，路面与屋顶积雪逐渐加厚至约 30 cm。',windy:'树冠摇摆、旗帜飘动，水面出现持续波纹。',typhoon:'持续暴雨、强阵风与大浪，河水逐渐上涨至约 68 cm。',tornado:'河流东岸出现旋转漏斗、扬尘和卷起的碎屑。'}[s.weather];setText('weather-note',text+(mode==='interior'?' 剖切时隐藏降水和覆雪，便于查看室内。':''));document.querySelector('#test-lightning').disabled=!['storm','typhoon'].includes(s.weather)||!environment.flashEnabled;
}
for(const b of document.querySelectorAll('[data-season]'))b.onclick=()=>{environment.state.setSeason(b.dataset.season);environment.update(0,{target:controls.target,interior:mode==='interior'});syncEnvironmentUI(environment.state.snapshot())};
 document.querySelector('#auto-seasons').onchange=e=>{environment.state.setAutoSeasons(e.target.checked);syncEnvironmentUI(environment.state.snapshot())};
function setTime(h){environment.state.setHour(h);environment.state.paused=true;environment.update(0,{target:controls.target,interior:mode==='interior'});renderer.shadowMap.needsUpdate=true}
document.querySelector('#time-slider').oninput=e=>setTime(+e.target.value/60);
document.querySelector('#time-input').onchange=e=>{const [h,m]=e.target.value.split(':').map(Number);if(Number.isFinite(h+m))setTime(h+m/60)};
for(const b of document.querySelectorAll('[data-hour]'))b.onclick=()=>setTime(+b.dataset.hour);
document.querySelector('#pause-time').onclick=()=>{environment.state.paused=!environment.state.paused;syncEnvironmentUI(environment.state.snapshot())};
document.querySelector('#speed').onchange=e=>environment.state.rate=+e.target.value;
for(const b of document.querySelectorAll('[data-weather]'))b.onclick=()=>{environment.state.setWeather(b.dataset.weather);syncEnvironmentUI(environment.state.snapshot())};
document.querySelector('#auto-weather').onchange=e=>environment.state.autoWeather=e.target.checked;
document.querySelector('#flash').checked=environment.flashEnabled;document.querySelector('#flash').onchange=e=>{environment.flashEnabled=e.target.checked;if(!e.target.checked)environment.flash=0;syncEnvironmentUI(environment.state.snapshot())};
document.querySelector('#thunder').onchange=e=>environment.enableSound(e.target.checked);
document.querySelector('#settle-weather').onclick=()=>{environment.state.previewSettled();syncEnvironmentUI(environment.state.snapshot())};
document.querySelector('#reset-surface').onclick=()=>{environment.state.resetSurface();syncEnvironmentUI(environment.state.snapshot())};
document.querySelector('#weather-focus').onclick=()=>{detail('river');camera.position.set(143,20,111);controls.target.set(121,2,83);controls.update()};
document.querySelector('#test-lightning').onclick=()=>environment.triggerLightning();
window.townViewer={environment,setTime,scene,camera,renderer,controls,district,view,detail,get current(){return current},get zone(){return zone},get mode(){return mode},get floor(){return floor}};
