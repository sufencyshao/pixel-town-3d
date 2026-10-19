import * as THREE from 'three';
import {AutumnLeaves} from './autumn-leaves.js';
import {SEASONS} from './environment-state.js';

// GLB combines many plants into each mesh. Weld equal positions to recover each
// connected crown, so winter contraction never pulls trees toward the town origin.
function crownAttributes(source,woody=true){
 const g=source.clone(),p=g.attributes.position,n=p.count,parent=Int32Array.from({length:n},(_,i)=>i),weld=new Map();
 const root=i=>{while(parent[i]!==i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
 const join=(a,b)=>{a=root(a);b=root(b);if(a!==b)parent[b]=a;};
 for(let i=0;i<n;i++){const key=`${p.getX(i).toFixed(4)},${p.getY(i).toFixed(4)},${p.getZ(i).toFixed(4)}`;if(weld.has(key))join(i,weld.get(key));else weld.set(key,i);}
 const count=g.index?.count||n;
 for(let i=0;i<count;i+=3){const a=g.index?g.index.getX(i):i;join(a,g.index?g.index.getX(i+1):i+1);join(a,g.index?g.index.getX(i+2):i+2);}
 const groups=new Map();
 for(let i=0;i<n;i++){const key=root(i);let c=groups.get(key);if(!c){c={min:new THREE.Vector3(Infinity,Infinity,Infinity),max:new THREE.Vector3(-Infinity,-Infinity,-Infinity)};groups.set(key,c);}const v=new THREE.Vector3().fromBufferAttribute(p,i);c.min.min(v);c.max.max(v);}
 for(const c of groups.values()){c.center=c.min.clone().add(c.max).multiplyScalar(.5);c.size=c.max.clone().sub(c.min);c.tree=woody&&c.min.y>1.4&&Math.max(c.size.x,c.size.z)>.85?1:0;}
 const pivot=new Float32Array(n*3),tree=new Float32Array(n);
 for(let i=0;i<n;i++){const c=groups.get(root(i));c.center.toArray(pivot,i*3);tree[i]=c.tree;}
 g.setAttribute('seasonPivot',new THREE.BufferAttribute(pivot,3));g.setAttribute('seasonTree',new THREE.BufferAttribute(tree,1));
 return {geometry:g,crowns:[...groups.values()].filter(c=>c.tree)};
}
export class SeasonalVegetation {
 constructor(env){this.env=env;this.materials=[];this.flowers=[];this.fruits=[];this.branches=[];this.uniforms={seasonCrown:{value:.94},seasonShrub:{value:.98}};this.lastSeason=null;this.fallAnchors=[];this.leafFall=new AutumnLeaves(env);this.leafMeshes=0;this.crownCount=0;}
 patch(source){
  const m=source.clone(),before=source.onBeforeCompile,key=source.customProgramCacheKey();
  m.onBeforeCompile=(shader,renderer)=>{before.call(source,shader,renderer);Object.assign(shader.uniforms,this.uniforms);
   shader.vertexShader='attribute vec3 seasonPivot;attribute float seasonTree;uniform float seasonCrown,seasonShrub;\n'+shader.vertexShader;
   // Append to the original shader so wind, snow and shadow all use the same crown shape.
   shader.vertexShader=shader.vertexShader.replace('#include <project_vertex>','transformed=seasonPivot+(transformed-seasonPivot)*mix(seasonShrub,seasonCrown,seasonTree);\n#include <project_vertex>');
  };
  m.customProgramCacheKey=()=>key+'-season-v5';return m;
 }
 attach(asset){
  asset.updateMatrixWorld(true);
  const list=[];asset.traverse(o=>{if(o.isMesh&&!['SnowCover','SnowDepthEdge'].includes(o.name))list.push(o)});
  for(const o of list){
   let owner=o;while(owner.parent&&owner.parent!==asset)owner=owner.parent;const name=owner.name,m=o.material;
   if(Array.isArray(m))continue;
   const outside=/Landscape|Planting|Trees|Landmark_Canopy|Orchard|Borders|Fields|Far_Bank|Habitat|Ground|Land$|L\d{2}_Front|Pergola_Roof|Pet_Lawn|Planters/.test(name);
   if(!outside)continue;
   const leaf=/^(leaf|leafLight|leafDark|leaf2)(\.|$)/.test(m.name),grass=/^(grass|meadow)(\.|$)/.test(m.name),flower=/^(flowerPink|flowerYellow|flowerWhite|lavender)(\.|$)/.test(m.name),crop=/Fields/.test(name)&&/^(darkgreen|sage)(\.|$)/.test(m.name);
   if(leaf){
    const {geometry,crowns}=crownAttributes(o.geometry,!/Front|Pergola_Roof|Planters/.test(name));o.geometry=geometry;o.material=this.patch(m);this.leafMeshes++;this.crownCount+=crowns.length;for(const c of crowns)this.fallAnchors.push({center:c.center.clone().applyMatrix4(o.matrixWorld),radius:Math.max(c.size.x,c.size.z)*.5,owner});
    if(o.customDepthMaterial)o.customDepthMaterial=this.patch(o.customDepthMaterial);
    for(const child of o.children)if(child.name==='SnowCover'){child.geometry=geometry;child.material=this.patch(child.material);}
    this.materials.push({m:o.material,kind:/leafLight|leaf2/.test(m.name)?'leafLight':'leaf',base:m.color.clone(),seed:this.materials.length});
    if(crowns.length)this.makeBranches(o,crowns);
   }else if(grass||crop){o.material=m.clone();this.materials.push({m:o.material,kind:'grass',base:m.color.clone(),seed:0});}
   else if(flower){o.material=m.clone();this.flowers.push({o,base:m.color.clone()});}
   if(/Orchard/.test(name)&&/^(apple|pear)(\.|$)/.test(m.name))this.fruits.push(o);
  }
  this.lastSeason=null;this.leafFall.attach(this.fallAnchors);
 }
 makeBranches(owner,crowns){
  const matrices=[],q=new THREE.Quaternion(),up=new THREE.Vector3(0,1,0),mid=new THREE.Vector3(),matrix=new THREE.Matrix4();
  const segment=(a,b,width)=>{const d=b.clone().sub(a);q.setFromUnitVectors(up,d.clone().normalize());mid.copy(a).add(b).multiplyScalar(.5);matrix.compose(mid,q,new THREE.Vector3(width,d.length(),width));matrices.push(matrix.clone());};
  for(const c of crowns){
   const base=c.center.clone();base.y=c.min.y;
   const top=c.center.clone();top.y+=c.size.y*.22;segment(base,top,.06+Math.min(c.size.x,c.size.z)*.025);
   for(let k=0;k<4;k++){const angle=k*Math.PI/2+c.center.x*.13,tip=c.center.clone().add(new THREE.Vector3(Math.cos(angle)*c.size.x*.34,c.size.y*(.10+(k%2)*.18),Math.sin(angle)*c.size.z*.34));segment(base.clone().lerp(top,.45),tip,.035+Math.min(c.size.x,c.size.z)*.012);const twig=tip.clone().add(new THREE.Vector3(Math.cos(angle+.5)*c.size.x*.12,c.size.y*.18,Math.sin(angle+.5)*c.size.z*.12));segment(tip,twig,.022);}
  }
  const branches=new THREE.InstancedMesh(new THREE.CylinderGeometry(.35,.6,1,5),this.env.extended.patchMaterial(new THREE.MeshStandardMaterial({color:'#80664b',roughness:1}),'tree'),matrices.length);
  matrices.forEach((m,i)=>branches.setMatrixAt(i,m));branches.name='SeasonalBareBranches';branches.castShadow=false;branches.receiveShadow=true;branches.frustumCulled=false;owner.add(branches);this.branches.push(branches);
 }
 update(s,seconds=0,interior=false){
  this.leafFall.update(s,seconds,interior);
  if(this.lastSeason===s.season)return;
  this.lastSeason=s.season;const palette=SEASONS[s.season];this.uniforms.seasonCrown.value=palette.foliage;this.uniforms.seasonShrub.value=s.season==='winter'?.66:s.season==='autumn'?.9:1;
  for(const {m,kind,base,seed} of this.materials){const color=new THREE.Color(palette[kind]);if(kind==='leaf')color.offsetHSL((seed%5-2)*.014,0,(seed%3-1)*.025);m.color.copy(base).lerp(color,.88);}
  for(const {o,base} of this.flowers){o.visible=palette.flower>0;o.material.color.copy(base).lerp(new THREE.Color(s.season==='autumn'?'#b99a71':'#f4d7bb'),1-palette.flower);}
  for(const o of this.fruits)o.visible=['summer','autumn'].includes(s.season);
  for(const b of this.branches)b.visible=s.season==='winter';this.env.renderer.shadowMap.needsUpdate=true;
 }
 snapshot(){return {seasonLeafMeshes:this.leafMeshes,seasonCrowns:this.crownCount,seasonGroundMaterials:this.materials.filter(m=>m.kind==='grass').length,seasonFlowerMeshes:this.flowers.length,seasonBranchGroups:this.branches.length,seasonCrownScale:this.uniforms.seasonCrown.value,...this.leafFall.snapshot()};}
}
