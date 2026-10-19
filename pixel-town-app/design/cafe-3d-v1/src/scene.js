import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';

const container=document.querySelector('#viewport');
const scene=new THREE.Scene();scene.background=new THREE.Color('#e9e7dd');
const camera=new THREE.PerspectiveCamera(38,1,.1,180);
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;renderer.shadowMap.needsUpdate=true;renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.2;container.append(renderer.domElement);
let dirty=true;function invalidate(shadow=false){dirty=true;if(shadow)renderer.shadowMap.needsUpdate=true;}
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.minDistance=6;controls.maxDistance=65;controls.maxPolarAngle=Math.PI*.49;controls.target.set(0,1.4,0);controls.addEventListener('change',()=>invalidate());
const model=new THREE.Group();model.name='H01_Creekside_Cafe';model.userData={units:'metres',buildingId:'H01',buildingWidth:18,buildingDepth:9,plotWidth:23.5,plotDepth:13,version:'1.0',frontDirection:'+Z'};scene.add(model);
function group(name,parent=model){const g=new THREE.Group();g.name=name;parent.add(g);return g;}
const shell=group('Architecture'),front=group('FrontFacade',shell),right=group('EastFacade',shell),roof=group('RemovableRoof',shell),inside=group('Interior'),outdoor=group('Terrace'),landscape=group('Landscape');
const mats={};function mat(n,c,extra={}){return mats[n]=new THREE.MeshStandardMaterial({name:n,color:c,roughness:.8,...extra})}
mat('plaster','#e8dfc8');mat('oak','#ae7d4e');mat('oakLight','#c89862');mat('endgrain','#805c3b');mat('sage','#536f5c');mat('sageLight','#92a183');mat('roof','#a75e43');mat('roofEdge','#784633');mat('stone','#c9c6b6');mat('cream','#eee7d2');mat('brass','#b49854',{metalness:.7,roughness:.3});mat('metal','#394742',{metalness:.5,roughness:.4});mat('steel','#a6afab',{metalness:.8,roughness:.3});mat('coffee','#46301d');mat('soil','#514532');mat('leaf','#758f56');mat('leafLight','#94a66b');mat('terra','#bd8160');mat('fabric','#c5c7a8');mat('glass','#b7d2cb',{transparent:true,opacity:.23,roughness:.15,metalness:.05,depthWrite:false});mat('light','#ffdf9a',{emissive:'#ffbf64',emissiveIntensity:.65});
const geomCache=new Map();
function mesh(n,g,m,x,y,z,p=model){const a=new THREE.Mesh(g,typeof m==='string'?mats[m]:m);a.name=n;a.position.set(x,y,z);a.castShadow=true;a.receiveShadow=true;p.add(a);return a;}
function box(n,x,y,z,w,h,d,m,p=model){const key=[w,h,d].join();if(!geomCache.has(key))geomCache.set(key,new THREE.BoxGeometry(w,h,d));return mesh(n,geomCache.get(key),m,x,y,z,p);}
function cyl(n,x,y,z,rt,rb,h,m,p=model,seg=20){return mesh(n,new THREE.CylinderGeometry(rt,rb,h,seg),m,x,y,z,p)}
function ball(n,x,y,z,r,m,p=model,scale=[1,1,1]){let a=mesh(n,new THREE.IcosahedronGeometry(r,1),m,x,y,z,p);a.scale.set(...scale);return a;}
function beam(n,a,b,r,m,p=model){let va=new THREE.Vector3(...a),vb=new THREE.Vector3(...b);const g=cyl(n,...va.clone().add(vb).multiplyScalar(.5).toArray(),r,r,va.distanceTo(vb),m,p,8);g.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),vb.sub(va).normalize());return g;}
function sign(n,txt,x,y,z,w,h,p,color='#f3ecd7',bg='#526852'){const c=document.createElement('canvas');c.width=1024;c.height=Math.round(1024*h/w);const ctx=c.getContext('2d');ctx.fillStyle=bg;ctx.fillRect(0,0,c.width,c.height);ctx.strokeStyle=color;ctx.lineWidth=3;ctx.strokeRect(15,15,c.width-30,c.height-30);ctx.fillStyle=color;ctx.textAlign='center';ctx.textBaseline='middle';ctx.font=`500 ${Math.round(c.height*.44)}px "Songti SC", "PingFang SC", serif`;ctx.fillText(txt,512,c.height*.51,960);const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return mesh(n,new THREE.PlaneGeometry(w,h),new THREE.MeshStandardMaterial({map:t,roughness:.8,side:THREE.DoubleSide}),x,y,z,p);}
// Architectural shell: foundation and individual wood boards.
box('Foundation',0,-.10,0,18.4,.36,9.4,'stone',shell);
for(let i=0;i<36;i++)box('OakFloor_'+i,-8.75+i*.5,.105,0,.488,.10,8.9,i%5===0?'oak':'oakLight',inside);
box('RearPlaster',-2.2,1.97,-4.4,13.6,3.7,.2,'plaster',shell);
// Rear service door is a real opening, 1.1m wide.
box('RearServiceWall',7.35,1.97,-4.4,3.3,3.7,.2,'plaster',shell);box('RearDoorLintel',5.15,3.22,-4.4,1.1,1.2,.2,'plaster',shell);box('RearServiceDoor',5.15,1.4,-4.41,1.06,2.55,.09,'sage',shell);
for(const [g,x] of [[shell,-8.9],[right,8.9]]){
 box('SidePlinth',x,.57,0,.2,.9,8.8,'sage',g);box('SideHeader',x,3.36,0,.2,.82,8.8,'plaster',g);
 for(const z of [-4.25,-1.5,1.5,4.25])box('SidePost',x,1.96,z,.25,3.7,.18,'oak',g);
 for(const [z,d] of [[-2.85,2.55],[0,2.8],[2.85,2.55]]){box('SideGlass',x,1.97,z,.035,1.95,d,(x>0&&z< -2)?'plaster':'glass',g);box('SideSill',x,1.03,z,.35,.12,d+.1,'oak',g);}
}
// Street facade, glazed openings and recessed entrance.
for(const [x,w] of [[-5,7.6],[5.05,7.5]]){box('FrontPlinth',x,.56,4.4,w,.88,.22,'sage',front);box('FrontGlass',x,1.92,4.4,w,1.84,.04,'glass',front);box('FrontSill',x,1.01,4.49,w+.08,.12,.37,'oak',front);}
for(const x of [-8.85,-5.2,-1.2,1.2,5.2,8.85])box('FrontTimberPost',x,1.96,4.4,.18,3.7,.3,'oak',front);
box('SignFascia',0,3.36,4.43,18,.82,.24,'sage',front);
// Door frame, an open leaf rotated into the entry recess.
box('DoorHeader',0,2.89,4.4,2.4,.14,.25,'oak',front);const door=group('EntranceDoor',front);door.position.set(-1.08,.12,4.36);door.rotation.y=-Math.PI*.38;
box('DoorLeafGlass',.52,1.33,0,1.0,2.5,.04,'glass',door);for(const x of [0,1.04])box('DoorStile',x,1.34,0,.075,2.68,.1,'sage',door);for(const y of [.05,1.0,2.62])box('DoorRail',.52,y,0,1.1,.09,.1,'sage',door);box('DoorHandle',.86,1.21,.08,.04,.36,.05,'brass',door);
sign('CafeName','溪 畔 咖 啡',0,3.38,4.565,4.5,.65,front);sign('WindowLettering','COFFEE  /  BAKES',-5,2.1,4.45,2.7,.28,front,'#f1e4bf','#536f5c');
// Solid gables and removable pitched roof.
for(const x of [-8.9,8.9]){const sh=new THREE.Shape();sh.moveTo(-4.5,0);sh.lineTo(4.5,0);sh.lineTo(0,1.9);sh.closePath();const a=mesh('Gable',new THREE.ShapeGeometry(sh),'plaster',x,3.82,0,roof);a.rotation.y=Math.PI/2;a.material=a.material.clone();a.material.side=THREE.DoubleSide;}
const pitch=Math.atan2(2.05,4.95),slope=Math.hypot(2.05,4.95);
for(const side of [-1,1]){const p=group('RoofSlope',roof);p.position.set(0,4.825,side*2.475);p.rotation.x=side*pitch;box('TerracottaRoof',0,0,0,19.25,.18,slope,'roof',p);for(let x=-9.45;x<9.5;x+=.47)box('StandingSeam',x,.11,0,.035,.045,slope,'roofEdge',p);box('EaveTrim',0,.015,side*slope/2,19.4,.23,.13,'roofEdge',p);}
box('RidgeCap',0,5.88,0,19.5,.18,.22,'roofEdge',roof);
for(const x of [-8.8,-4.45,0,4.45,8.8]){beam('RoofTruss',[x,3.65,-4.3],[x,5.5,0],.075,'oak',roof);beam('RoofTruss',[x,5.5,0],[x,3.65,4.3],.075,'oak',roof);box('TieBeam',x,3.67,0,.14,.2,8.7,'oak',roof);}
// Furniture helpers.
function cup(x,y,z,p=inside){cyl('CupSaucer',x,y,z,.13,.13,.025,'cream',p);cyl('Cup',x,y+.095,z,.085,.067,.16,'cream',p);cyl('Coffee',x,y+.178,z,.071,.071,.008,'coffee',p);const h=mesh('CupHandle',new THREE.TorusGeometry(.055,.013,6,14),'cream',x+.089,y+.10,z,p);}
function chair(x,z,angle=0,p=inside){const g=group('Chair',p);g.position.set(x,.15,z);g.rotation.y=angle;box('Seat',0,.46,0,.52,.10,.52,'sageLight',g);for(const xx of [-.20,.20])for(const zz of [-.20,.20])box('ChairLeg',xx,.22,zz,.055,.44,.055,'oak',g);for(const xx of [-.22,.22])box('BackPost',xx,.76,-.22,.05,.65,.06,'oak',g);box('BackRest',0,.95,-.22,.50,.23,.07,'oak',g);return g;}
function table(x,z,r=.66,p=inside){cyl('RoundTableTop',x,.96,z,r,r,.085,'oakLight',p,40);cyl('TableStem',x,.54,z,.08,.09,.78,'metal',p);cyl('TableFoot',x,.18,z,.31,.36,.07,'metal',p);cup(x-.18,1.01,z,p);cup(x+.18,1.01,z+.2,p);}
function plant(x,z,s=1,p=inside){cyl('TerracottaPot',x,.15+.28*s,z,.28*s,.20*s,.56*s,'terra',p,14);cyl('PotSoil',x,.15+.56*s,z,.24*s,.24*s,.025,'soil',p);for(let i=0;i<7;i++){const a=i*2.4;let ex=x+Math.cos(a)*s*.42,ez=z+Math.sin(a)*s*.42,y=.65*s+(i%3)*.18;beam('PlantStem',[x,.55*s, z],[ex,y+.3,ez],.018*s,'leaf',p);ball('Leaf',ex,y+.2,ez,.28*s,i%2?'leaf':'leafLight',p,[1,.35,1]);}}
// Bar and rear staff work aisle, clear width 1.35 m.
const bar=group('CoffeeBar',inside);box('BarCabinet',-1.4,.70,-1.35,8.6,1.1,1.0,'sage',bar);box('Countertop',-1.4,1.29,-1.35,8.85,.12,1.12,'cream',bar);
for(let x=-5.45;x<2.8;x+=.16)box('BarOakFlute',x,.70,-.837,.046,.94,.025,'oakLight',bar);
box('EndCounter',2.6,.70,-2.30,.7,1.1,2.8,'sage',bar);box('EndCountertop',2.6,1.29,-2.8425,.82,.12,1.865,'cream',bar);
box('RearWorktop',-1.4,1.10,-3.94,8.8,.10,.75,'oak',bar);box('RearCabinet',-1.4,.64,-3.98,8.7,.85,.66,'sage',bar);
for(let x=-5.3;x<2.8;x+=1.05){box('CabinetDoor',x,.68,-3.635,.96,.73,.03,'sageLight',bar);box('CabinetPull',x+.30,.78,-3.60,.035,.17,.04,'brass',bar);}
// Espresso machine: group heads, controls, cups and steam wands.
box('EspressoBase',-2.2,1.43,-1.36,1.8,.18,.66,'metal',bar);box('EspressoBody',-2.2,1.74,-1.52,1.8,.55,.42,'steel',bar);box('EspressoTop',-2.2,2.03,-1.49,1.88,.08,.54,'sage',bar);
for(const x of [-2.65,-2.2,-1.75]){cyl('GroupHead',x,1.84,-1.15,.09,.09,.19,'metal',bar);box('PortafilterHandle',x,1.80,-.98,.045,.035,.25,'endgrain',bar);cup(x,1.51,-1.10,bar);cyl('ControlButton',x,1.96,-1.286,.027,.027,.025,'brass',bar).rotation.x=Math.PI/2;}
beam('SteamWand',[-1.38,1.80,-1.30],[-1.26,1.54,-1.11],.019,'steel',bar);
box('GrinderBase',-.63,1.42,-1.38,.4,.18,.4,'metal',bar);cyl('Grinder',-.63,1.69,-1.4,.14,.14,.42,'sage',bar);cyl('BeanHopper',-.63,2.02,-1.4,.19,.1,.32,'glass',bar);cyl('CoffeeBeans',-.63,2.0,-1.4,.15,.09,.25,'coffee',bar);
box('POS',1.55,1.6,-1.18,.48,.35,.07,'metal',bar).rotation.x=-.3;box('POSFoot',1.55,1.38,-1.35,.32,.05,.27,'metal',bar);
// Pastry case left of coffee machine.
box('PastryCaseBase',-4.6,1.40,-1.35,1.5,.13,.8,'oak',bar);box('PastryCaseGlass',-4.6,1.73,-1.35,1.5,.55,.78,'glass',bar);box('PastryShelf',-4.6,1.74,-1.35,1.40,.035,.7,'cream',bar);
for(const x of [-5.05,-4.6,-4.15])for(const y of [1.52,1.83])ball('Pastry',x,y,-1.31,.12,'terra',bar,[1.3,.65,1]);
// Sink and open shelves.
box('SinkRim',1.2,1.17,-3.95,1.15,.05,.59,'steel',bar);box('SinkBowl',1.2,1.19,-3.94,.85,.02,.39,'metal',bar);beam('Faucet',[1.2,1.18,-4.15],[1.2,1.57,-4.15],.025,'steel',bar);beam('Faucet',[1.2,1.57,-4.15],[1.2,1.57,-3.91],.025,'steel',bar);
for(const y of [2.05,2.77]){box('DisplayShelf',-1.3,y,-4.06,8.4,.09,.45,'oak',bar);for(let x=-5;x<2.8;x+=.65){if(x>0)cup(x,y+.05,-4,bar);else{cyl('CoffeeJar',x,y+.24,-4,.11,.11,.36,'cream',bar);cyl('JarLid',x,y+.44,-4,.12,.12,.035,'oak',bar);}}}
sign('CoffeeMenu','ESPRESSO   /   LATTE   /   FILTER',-1.6,3.26,-4.27,5.6,.48,bar,'#ece5ce','#3c5144');
// Service rooms at northeast, open tops for cutaway viewing. Partitions have actual door gaps.
const service=group('ServiceRooms',inside);box('ServiceWestPartition',4.35,1.65,-2.9,.14,3.0,2.65,'plaster',service);box('ServiceMiddlePartition',6.65,1.65,-2.9,.12,3.0,2.8,'plaster',service);
for(const [x,w] of [[4.58,.46],[6.09,1.08],[8.29,1.02]])box('ServiceFrontPartition',x,1.65,-1.44,w,3.0,.14,'plaster',service);
for(const x of [5.25,7.48])box('ServiceDoorHeader',x,2.92,-1.44,.88,.46,.14,'plaster',service);
sign('StaffLabel','备餐 / 储物',5.3,2.90,-1.35,1.42,.27,service);sign('WCLabel','WC',7.49,2.90,-1.35,.6,.27,service);
box('ServicePrepTable',5.5,1.04,-3.80,1.7,.10,.7,'steel',service);box('Fridge',4.89,.91,-2.36,.65,1.5,.65,'cream',service);box('FridgeHandle',5.13,1.11,-2.01,.04,.40,.05,'steel',service);
box('ToiletTank',7.55,.89,-3.95,.63,.78,.25,'cream',service);cyl('ToiletBowl',7.55,.49,-3.55,.33,.24,.46,'cream',service);box('WCWashstand',8.37,.91,-2.45,.55,.17,.65,'cream',service);box('WCMirror',8.76,1.70,-2.45,.025,.7,.57,'steel',service);
// Guest seating: 4 two-seat tables, communal table with 6, window stools with 4 =18 indoor seats.
for(const [x,z] of [[-7.0,-1.75],[-7.0,1.35],[-3.35,2.15],[3.4,2.15]]){table(x,z);chair(x-.92,z,Math.PI/2);chair(x+.92,z,-Math.PI/2);}
box('CommunalTable',6.5,.99,.35,2.4,.10,1.0,'oakLight',inside);for(const x of [5.7,7.3])for(const z of [0,.7])box('TableLeg',x,.53,z,.09,.86,.09,'oak',inside);for(const x of [5.65,6.5,7.35]){chair(x,-.65,0);chair(x,1.35,Math.PI);cup(x,1.06,.30);}
box('WindowBar',-5.25,1.16,3.91,6.2,.10,.5,'oak',inside);for(const x of [-7.5,-6,-4.5,-3]){cyl('StoolSeat',x,.81,3.12,.27,.27,.09,'sageLight',inside);for(const dx of [-.15,.15])for(const dz of [-.15,.15])box('StoolLeg',x+dx,.47,3.12+dz,.045,.65,.045,'oak',inside);}
plant(-8.15,3.42,1.1);plant(8.04,3.4,1.3);plant(-7.9,-3.6,.85);
// Lamps are independent from roof so cutaway still communicates ceiling height.
const lights=group('PendantFixtures',inside);
for(const [x,z] of [[-4.7,-1.35],[-1.3,-1.35],[2.1,-1.35],[-3.35,2.15],[3.4,2.15],[6.5,.35]]){cyl('PendantCord',x,3.26,z,.015,.015,1.1,'metal',lights,8);cyl('PendantShade',x,2.77,z,.12,.33,.28,'sage',lights);cyl('PendantGlow',x,2.62,z,.28,.28,.025,'light',lights);}
// Terrace, accessible flush threshold and straight entry strip.
box('TerraceSlab',0,-.05,5.48,22.7,.28,3,'stone',outdoor);for(let x=-10.9;x<11;x+=.65)box('TerracePaverJoint',x,.096,5.48,.012,.008,2.9,'cream',outdoor);
for(const [x,z] of [[-6.8,5.95],[6.8,5.95]]){table(x,z,.65,outdoor);chair(x-.95,z,Math.PI/2,outdoor);chair(x+.95,z,-Math.PI/2,outdoor);}
// Lightweight green pergola/awning attached outside front wall.
for(const x of [-8.9,-1.3,1.3,8.9])box('CanopySupport',x,1.52,6.3,.09,2.85,.09,'sage',outdoor);
box('CanopyFrontBeam',0,3.04,6.3,18,.15,.13,'sage',outdoor);
box('StreetSignBoard',0,2.72,6.35,3.3,.58,.10,'sage',outdoor);sign('StreetCafeName','溪 畔 咖 啡',0,2.72,6.408,3.16,.50,outdoor);
for(let x=-8.9;x<=8.9;x+=.6){const a=box('CanopySlat',x,3.17,5.33,.075,.1,2.12,'oak',outdoor);a.rotation.x=.08;}
for(const x of [-10.15,10.15]){box('PlanterBox',x,.37,5.70,1.15,.55,1.5,'sage',landscape);for(const z of [5.25,5.9])ball('TerraceShrub',x,.98,z,.62,'leaf',landscape,[.85,.75,1]);}
const board=group('MenuAFrame',outdoor);board.position.set(2.35,.12,5.43);box('MenuBoard',0,.70,0,.65,1.05,.055,'oak',board).rotation.x=-.12;sign('MenuText','今日咖啡',0,.87,.085,.53,.3,board,'#ede7cd','#354b40');sign('MenuPrice','COFFEE & BAKES',0,.58,.055,.52,.18,board,'#ede7cd','#354b40');beam('BoardRearLeg',[-.28,1.12,0],[-.28,0,-.55],.035,'oak',board);beam('BoardRearLeg',[.28,1.12,0],[.28,0,-.55],.035,'oak',board);
// Site vignette, not included in the building export.
const context=group('DisplayContext',scene);box('SiteBase',0,-.40,.8,25,.4,16,'cream',context);box('SiteGrassLeft',-10.8,-.13,-1.4,2.1,.10,8.9,'sageLight',context);box('SiteGrassRight',10.8,-.13,-1.4,2.1,.10,8.9,'sageLight',context);
for(const x of [-10.7,10.7]){cyl('TreeTrunk',x,1.22,-3,.13,.20,2.65,'oak',context);for(const [dx,dy,dz,r] of [[0,3.4,0,1.25],[-.65,3.05,.30,.85],[.6,3.2,-.25,.9],[.1,4.05,.1,.9]])ball('TreeCrown',x+dx,dy,-3+dz,r,dx<0?'leafLight':'leaf',context);}
const ground=mesh('Backdrop',new THREE.PlaneGeometry(200,200),new THREE.MeshStandardMaterial({color:'#e9e7dd',roughness:1}),0,-.62,0,scene);ground.rotation.x=-Math.PI/2;ground.castShadow=false;
const ambient=new THREE.HemisphereLight('#fff6dd','#819489',2.3);scene.add(ambient);const sun=new THREE.DirectionalLight('#ffefd8',3.4);sun.position.set(-12,23,17);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-23,right:23,top:22,bottom:-20,near:1,far:70});sun.shadow.bias=-.00035;sun.shadow.normalBias=.035;scene.add(sun);
const fill=new THREE.DirectionalLight('#d8e9ef',1.0);fill.position.set(15,10,-10);scene.add(fill);
const warmLights=[];for(const x of [-5,1,6]){const l=new THREE.PointLight('#ffd28e',0,14,2);l.position.set(x,2.8,1);scene.add(l);warmLights.push(l);}
const states={view:'exterior',night:false,rotate:false};const viewPresets={exterior:{eye:[25,14,31],target:[0,1.7,1]},cutaway:{eye:[21,24,27],target:[0,0.6,0]},top:{eye:[0,37,.1],target:[0,0,0]},counter:{eye:[-.8,2.7,3.0],target:[-1.8,1.75,-1.4]}};
function fit(){const w=container.clientWidth,h=container.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();invalidate();}
function view(name){invalidate(true);states.view=name;const cut=name!=='exterior';roof.visible=!cut;front.visible=!cut;right.visible=name==='exterior';lights.visible=name!=='top';const p=viewPresets[name],t=new THREE.Vector3(...p.target),e=new THREE.Vector3(...p.eye);if(camera.aspect<1)e.sub(t).multiplyScalar(1.40).add(t);camera.position.copy(e);controls.target.copy(t);controls.minDistance=name==='counter'?2:6;controls.update();document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===name)));document.querySelector('#roof').checked=roof.visible;document.querySelector('#view-name').textContent={exterior:'完整外观',cutaway:'室内剖切',top:'俯视布局',counter:'吧台近景'}[name];}
function night(on){invalidate();states.night=on;scene.background.set(on?'#243732':'#e9e7dd');ground.material.color.set(on?'#35483f':'#e9e7dd');ambient.intensity=on?.60:2.3;sun.intensity=on?.24:3.4;fill.intensity=on?.5:1;warmLights.forEach(l=>l.intensity=on?90:0);mats.light.emissiveIntensity=on?2.0:.65;}
async function exportGLB(){const vis=[roof.visible,front.visible,right.visible,lights.visible];roof.visible=front.visible=right.visible=lights.visible=true;model.updateMatrixWorld(true);try{return await new GLTFExporter().parseAsync(model,{binary:true,onlyVisible:true});}finally{[roof.visible,front.visible,right.visible,lights.visible]=vis;}}
function download(blob,name){const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);}
document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>view(b.dataset.view));document.querySelector('#roof').onchange=e=>{roof.visible=e.target.checked;invalidate(true)};document.querySelector('#night').onchange=e=>night(e.target.checked);document.querySelector('#rotate').onchange=e=>{states.rotate=e.target.checked;controls.autoRotate=e.target.checked;controls.autoRotateSpeed=.55};document.querySelector('#reset').onclick=()=>view(states.view);document.querySelector('#export').onclick=async()=>{const b=document.querySelector('#export');b.disabled=true;b.textContent='正在导出…';try{download(new Blob([await exportGLB()],{type:'model/gltf-binary'}),'H01-溪畔咖啡厅.glb');}catch(e){document.querySelector('#status').textContent='导出失败：'+e.message;}finally{b.disabled=false;b.textContent='下载 3D 模型';}};document.querySelector('#capture').onclick=()=>{renderer.render(scene,camera);renderer.domElement.toBlob(b=>download(b,'咖啡厅-'+states.view+'.png'));};
new ResizeObserver(fit).observe(container);fit();view('exterior');renderer.setAnimationLoop(()=>{controls.update();if(dirty){renderer.render(scene,camera);dirty=false;}});
let meshes=0,triangles=0;model.traverse(o=>{if(o.isMesh){meshes++;triangles+=(o.geometry.index?o.geometry.index.count:o.geometry.attributes.position.count)/3;}});document.querySelector('#status').textContent='模型已就绪 · 拖动旋转 / 滚轮缩放 / 右键平移';window.cafe={scene,model,camera,controls,renderer,view,night,exportGLB,stats:{meshes,triangles},validateGLB:async(buffer)=>{const gltf=await new GLTFLoader().parseAsync(buffer,'');let count=0;gltf.scene.traverse(o=>{if(o.isMesh)count++});return {meshes:count,bounds:new THREE.Box3().setFromObject(gltf.scene).getSize(new THREE.Vector3()).toArray(),root:gltf.scene.children[0]?.name}},groups:{roof,front,right,lights}};
