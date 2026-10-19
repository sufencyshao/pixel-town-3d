import * as THREE from 'three';

// All distances are metres. The model is already exported with world-space Y up.
const sharedGLSL=`uniform float wxTime,wxWind;
vec3 windOffset(vec3 p){float h=max(0.,p.y);float bend=min(h*h*.004,.24);float wave=.55+.30*sin(wxTime*2.1+p.x*.035+p.z*.025)+.15*sin(wxTime*3.7+p.z*.08);return vec3(1.,0.,.32)*wxWind*bend*wave;}
float waterWave(vec3 p){return (sin(p.x*1.8+p.z*.45-wxTime*3.2)+.45*sin(p.z*3.4+p.x*.6-wxTime*4.7))*min(.035,wxWind*.003);}
`;
const logVertex=`#include <common>
#include <logdepthbuf_pars_vertex>
`;
const logFragment=`#include <common>
#include <logdepthbuf_pars_fragment>
`;

export class ExtendedWeather {
 constructor(env){
  this.env=env;this.uniforms={wxTime:{value:0},wxWind:{value:.7},wxSnow:{value:0},wxRiver:{value:0},wxHeight:{value:env.heightTexture}};
  this.root=new THREE.Group();this.root.name='SnowWindCyclone';env.scene.add(this.root);
  this.snowLayers=[];this.windMeshes=[];this.waterMeshes=[];this.flags=[];this.snowCount=0;this.quality={};
  this.makeSnowfall();this.makeTornado();this.makeWindTrails();this.makeFlags();
 }
 patchMaterial(material,type){
  const m=material.clone(),u=this.uniforms;
  m.onBeforeCompile=shader=>{
   Object.assign(shader.uniforms,u);
   shader.vertexShader=sharedGLSL+'uniform float wxRiver; varying vec3 wxPosition;\n'+shader.vertexShader;
   let displacement='';
   if(type==='tree')displacement='transformed+=windOffset(transformed);';
   if(type==='bunting')displacement='float pin=clamp((4.74-transformed.y)/.54,0.,1.);transformed.z+=pin*min(wxWind*.065,.65)*sin(wxTime*5.-transformed.x*3.);';
   if(type==='water'||type==='river')displacement=`transformed.y+=waterWave(transformed)${type==='river'?'+wxRiver':''};`;
   shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\n'+displacement+'\nwxPosition=transformed;');
   if(type==='water'||type==='river'){
    shader.fragmentShader='uniform float wxTime,wxWind;varying vec3 wxPosition;\n'+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <normal_fragment_maps>',`#include <normal_fragment_maps>
     float a=min(.3,wxWind*.027);normal=normalize(normal+vec3(cos(wxPosition.x*1.8+wxPosition.z*.45-wxTime*3.2)*a,0.,cos(wxPosition.z*3.4+wxPosition.x*.6-wxTime*4.7)*a));`);
    shader.fragmentShader=shader.fragmentShader.replace('#include <color_fragment>',`#include <color_fragment>
     float stripes=pow(.5+.5*sin(wxPosition.x*1.8+wxPosition.z*.45-wxTime*3.2+sin(wxPosition.z*.75-wxTime*.7)*.8),22.);
     diffuseColor.rgb=mix(diffuseColor.rgb,vec3(.46,.68,.66),stripes*min(.30,wxWind*.025));`);
   }
  };
  m.customProgramCacheKey=()=>`v4-${type}`;
  if(type==='water'||type==='river'){m.roughness=.3;m.metalness=.12;}
  return m;
 }
 snowMaterial(sway,skirt=false){
  const m=new THREE.MeshStandardMaterial({color:'#f1f5fa',roughness:.92,side:THREE.DoubleSide});
  m.onBeforeCompile=shader=>{
   Object.assign(shader.uniforms,this.uniforms);
   shader.vertexShader=sharedGLSL+`${skirt?'attribute float coatLift;':''}uniform float wxSnow;varying vec3 snowBase;varying float snowUp;\n`+shader.vertexShader;
   shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>
    snowBase=(modelMatrix*vec4(position,1.)).xyz;snowUp=${skirt?'1.':'(mat3(modelMatrix)*normal).y'};
    transformed.y+=wxSnow*${skirt?'coatLift':'clamp(snowUp*1.6,0.,1.)'}+.009;
    ${sway?'transformed+=windOffset(position);':''}`);
   shader.fragmentShader=`uniform float wxSnow;uniform sampler2D wxHeight;varying vec3 snowBase;varying float snowUp;
    float coatHash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
    float coatNoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(coatHash(i),coatHash(i+vec2(1,0)),f.x),mix(coatHash(i+vec2(0,1)),coatHash(i+1.),f.x),f.y);}
    `+shader.fragmentShader;
   shader.fragmentShader=shader.fragmentShader.replace('#include <clipping_planes_fragment>',`#include <clipping_planes_fragment>
    if(snowUp<.32||wxSnow<.001)discard;
    vec2 cell=((snowBase.xz-vec2(-135.,-115.))/.75+.5)/vec2(401.,301.);
    float top=texture2D(wxHeight,cell).r;
    if(top>snowBase.y+.85)discard;
    float snowPatch=.65*coatNoise(snowBase.xz*.5)+.35*coatNoise(snowBase.xz*1.7);
    if(snowPatch>clamp(wxSnow/.075,0.,1.))discard;`);
  };
  m.customProgramCacheKey=()=>`v4-snow-${sway}-${skirt}`;return m;
 }
 attach(asset){
  const meshes=[];asset.traverse(o=>{if(o.isMesh)meshes.push(o)});
  const snowStatic=this.snowMaterial(false),snowSway=this.snowMaterial(true),snowEdge=this.snowMaterial(false,true);let edgeCount=0;
  for(const o of meshes){
   let owner=o;while(owner.parent&&owner.parent!==asset)owner=owner.parent;
   const name=owner.name,m=o.material;if(Array.isArray(m))continue;
   const indoor=/Interior|Furniture/.test(name)&&!/Street_Furniture|F__Furniture/.test(name);
   const leaf=/^(leaf|leafLight|leafDark|leaf2)(\.|$)/.test(m.name);
   const trunk=/^(F__Trees|F__Pet_Trees|E__Landmark_Trunk|G__Orchard|T__Planting|F__Far_Bank)$/.test(name)&&/^(wood|bark)/.test(m.name);
   const tree=!indoor&&((leaf&&/Landscape|Planting|Trees|Landmark|Orchard|Borders|Fields|Far_Bank|Habitat/.test(name))||trunk);
   const river=/^(F__River|T__River)$/.test(name);
   const water=/^(water|river|ripple)(\.|$)/.test(m.name);
   const bunting=name==='E__Event_Decor'&&/^(sage|clay|ochre|mutedblue)/.test(m.name);
   if(tree||water||bunting){const type=tree?'tree':bunting?'bunting':river?'river':'water';o.material=this.patchMaterial(m,type);if(tree){this.windMeshes.push(o);o.customDepthMaterial=this.patchMaterial(new THREE.MeshDepthMaterial({depthPacking:THREE.RGBADepthPacking}),'tree');}if(water)this.waterMeshes.push(o);if(bunting)this.flags.push(o);}
   const exterior=/Roof|Landscape|Ground|Land$|Paths|Paving|Canopy|Trees|Planting|Orchard|Fields|Borders|Bridges|Rest|Street_Furniture|Terrace|Approach|Transitions|Benches/.test(name);
   if(exterior&&!indoor&&!water&&!/glass|lamp|wire/.test(m.name)){
    const layer=new THREE.Mesh(o.geometry,tree?snowSway:snowStatic);layer.name='SnowCover';layer.receiveShadow=true;layer.frustumCulled=false;o.add(layer);this.snowLayers.push(layer);
    if(!tree&&/Roof|Ground|Land$|Paths|Paving|Benches|Approach/.test(name)){
     const geometry=this.snowSkirt(o.geometry,/Roof/.test(name));if(geometry){const side=new THREE.Mesh(geometry,snowEdge);side.name='SnowDepthEdge';side.receiveShadow=true;side.frustumCulled=false;o.add(side);this.snowLayers.push(side);edgeCount++;}
    }
   }
  }
  this.quality={snowLayers:this.snowLayers.length,snowEdges:edgeCount,windMeshes:this.windMeshes.length,waterMeshes:this.waterMeshes.length,flags:this.flags.length};
 }
 // Close the exposed top surfaces with vertical snow edges, so deep snow has thickness.
 snowSkirt(geometry,outerOnly=false){
  const pos=geometry.getAttribute('position'),normal=geometry.getAttribute('normal'),index=geometry.index;
  if(!normal)return null;
  const edges=new Map(),count=index?index.count:pos.count;
  const key=i=>`${Math.round(pos.getX(i)*1000)},${Math.round(pos.getY(i)*1000)},${Math.round(pos.getZ(i)*1000)}`;
  for(let i=0;i<count;i+=3){const tri=[0,1,2].map(k=>index?index.getX(i+k):i+k);if(tri.reduce((v,n)=>v+normal.getY(n),0)/3<.45)continue;
   for(let j=0;j<3;j++){const a=tri[j],b=tri[(j+1)%3],ka=key(a),kb=key(b),k=ka<kb?ka+'|'+kb:kb+'|'+ka;const old=edges.get(k);if(old)old.count++;else edges.set(k,{a,b,count:1});}
  }
  // On roofs, close only the outer perimeter; internal roof seams must not become snow walls.
  let hull=[];
  if(outerOnly){const map=new Map();for(const e of edges.values())for(const i of [e.a,e.b])map.set(`${pos.getX(i).toFixed(3)},${pos.getZ(i).toFixed(3)}`,[pos.getX(i),pos.getZ(i)]);
   const points=[...map.values()].sort((a,b)=>a[0]-b[0]||a[1]-b[1]),cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
   const half=points=>{const h=[];for(const p of points){while(h.length>=2&&cross(h[h.length-2],h[h.length-1],p)<=0)h.pop();h.push(p);}return h.slice(0,-1);};hull=half(points).concat(half([...points].reverse()));
  }
  const perimeter=(x,z)=>hull.some((a,i)=>{const b=hull[(i+1)%hull.length],dx=b[0]-a[0],dz=b[1]-a[1],len=dx*dx+dz*dz;if(!len)return false;const t=Math.min(1,Math.max(0,((x-a[0])*dx+(z-a[1])*dz)/len));return Math.hypot(x-a[0]-t*dx,z-a[1]-t*dz)<.025;});
  const vertices=[],normals=[],lifts=[];
  for(const e of edges.values()){if(e.count!==1)continue;const a=[pos.getX(e.a),pos.getY(e.a),pos.getZ(e.a)],b=[pos.getX(e.b),pos.getY(e.b),pos.getZ(e.b)];const dx=b[0]-a[0],dz=b[2]-a[2],length=Math.hypot(dx,dz);if(length<.02||(outerOnly&&!perimeter((a[0]+b[0])/2,(a[2]+b[2])/2)))continue;
   for(const [v,lift] of [[a,0],[b,0],[b,1],[a,0],[b,1],[a,1]]){vertices.push(...v);normals.push(dz/length,0,-dx/length);lifts.push(lift);}
  }
  if(!vertices.length)return null;const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));g.setAttribute('normal',new THREE.Float32BufferAttribute(normals,3));g.setAttribute('coatLift',new THREE.Float32BufferAttribute(lifts,1));return g;
 }
 makeSnowfall(){
  let seed=47;const rnd=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
  const n=14000,seeds=new Float32Array(n*3);for(let i=0;i<seeds.length;i++)seeds[i]=rnd();
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(seeds,3));g.setDrawRange(0,0);
  const m=new THREE.ShaderMaterial({transparent:true,depthWrite:false,uniforms:{...this.uniforms,pixelScale:{value:800}},vertexShader:logVertex+`
   uniform float wxTime,wxWind,pixelScale,wxSnow;uniform sampler2D wxHeight;varying float snowAlpha;
   void main(){float x=-135.+mod(position.x*300.+wxTime*wxWind*.9+sin(wxTime*.8+position.z*40.)*.9,300.);
    float z=-115.+mod(position.z*225.+wxTime*wxWind*.28+cos(wxTime+position.x*30.)*.7,225.);
    float y=mod(position.y*44.-wxTime*(1.6+position.z*1.4),44.);
    float ground=texture2D(wxHeight,((vec2(x,z)-vec2(-135.,-115.))/.75+.5)/vec2(401.,301.)).r;
    snowAlpha=step(ground+wxSnow+.08,y);vec4 mvPosition=modelViewMatrix*vec4(x,y,z,1.);gl_Position=projectionMatrix*mvPosition;gl_PointSize=clamp(pixelScale*(.13+position.y*.16)/max(1.,-mvPosition.z),1.3,7.);
    #include <logdepthbuf_vertex>
   }`,fragmentShader:logFragment+`
   varying float snowAlpha;void main(){float d=length(gl_PointCoord-.5);if(d>.5||snowAlpha<.5)discard;gl_FragColor=vec4(.93,.97,1.,(1.-smoothstep(.15,.5,d))*.85);
   #include <logdepthbuf_fragment>
   }`});
  this.snowfall=new THREE.Points(g,m);this.snowfall.frustumCulled=false;this.root.add(this.snowfall);
 }
 makeTornado(){
  this.cyclone=new THREE.Group();this.cyclone.name='Tornado';this.root.add(this.cyclone);
  const g=new THREE.CylinderGeometry(10,1.5,62,64,48,true);g.translate(0,31,0);
  const m=new THREE.ShaderMaterial({transparent:true,side:THREE.DoubleSide,depthWrite:false,uniforms:{t:{value:0},power:{value:0}},vertexShader:logVertex+`
   uniform float t;varying vec2 vUv;void main(){vUv=uv;vec3 p=position;p.x+=sin(p.y*.075+t*.6)*p.y*.055;p.z+=cos(p.y*.06+t*.5)*p.y*.035;vec4 mvPosition=modelViewMatrix*vec4(p,1.);gl_Position=projectionMatrix*mvPosition;
   #include <logdepthbuf_vertex>
   }`,fragmentShader:logFragment+`
   uniform float t,power;varying vec2 vUv;void main(){float swirl=.5+.5*sin(vUv.x*50.-vUv.y*45.-t*9.);float fine=.5+.5*sin(vUv.x*113.+vUv.y*27.+t*5.);vec3 color=mix(vec3(.16,.20,.21),vec3(.36,.41,.42),swirl*.55+fine*.12);gl_FragColor=vec4(color,power*(.66+.18*swirl)*(1.-smoothstep(.84,1.,vUv.y)));
   #include <logdepthbuf_fragment>
   #include <tonemapping_fragment>
   #include <colorspace_fragment>
   }`});
  this.funnel=new THREE.Mesh(g,m);this.funnel.frustumCulled=false;this.cyclone.add(this.funnel);
  const seed=new Float32Array(1300*3);for(let i=0;i<1300;i++){seed[i*3]=(i*.61803399)%1;seed[i*3+1]=(i*.75487766)%1;seed[i*3+2]=(i*.56984029)%1;}
  const dg=new THREE.BufferGeometry();dg.setAttribute('position',new THREE.BufferAttribute(seed,3));
  const dm=new THREE.ShaderMaterial({transparent:true,depthWrite:false,uniforms:{t:{value:0},power:{value:0}},vertexShader:logVertex+`
   uniform float t,power;varying float shade;void main(){float h=mod(position.y*35.+t*2.,35.);float angle=position.x*6.283+t*(3.-h*.035);float radius=2.+h*.18+position.z*3.;vec3 p=vec3(cos(angle)*radius,h,sin(angle)*radius);shade=position.z;vec4 mvPosition=modelViewMatrix*vec4(p,1.);gl_Position=projectionMatrix*mvPosition;gl_PointSize=clamp(700.*(.12+position.z*.32)/max(1.,-mvPosition.z),1.,6.);
   #include <logdepthbuf_vertex>
   }`,fragmentShader:logFragment+`
   uniform float power;varying float shade;void main(){if(length(gl_PointCoord-.5)>.5)discard;gl_FragColor=vec4(mix(vec3(.25,.22,.14),vec3(.53,.48,.33),shade),power*.8);
   #include <logdepthbuf_fragment>
   }`});
  this.debris=new THREE.Points(dg,dm);this.debris.frustumCulled=false;this.cyclone.add(this.debris);
 }
 makeWindTrails(){
  const n=260,positions=new Float32Array(n*6),seeds=new Float32Array(n*6),tips=new Float32Array(n*2);
  for(let i=0;i<n;i++){const p=[(i*.61803399)%1,(i*.75487766)%1,(i*.56984029)%1];seeds.set(p,i*6);seeds.set(p,i*6+3);tips[i*2+1]=1;}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(positions,3));g.setAttribute('seed',new THREE.BufferAttribute(seeds,3));g.setAttribute('tip',new THREE.BufferAttribute(tips,1));
  const m=new THREE.ShaderMaterial({transparent:true,depthWrite:false,uniforms:{...this.uniforms,opacity:{value:0}},vertexShader:logVertex+`
   attribute vec3 seed;attribute float tip;uniform float wxTime,wxWind;void main(){float x=-135.+mod(seed.x*300.+wxTime*wxWind*2.8,300.)-tip*3.;float z=-115.+mod(seed.z*225.+wxTime*wxWind*.7,225.);float y=2.+seed.y*19.+sin(wxTime+seed.x*7.);vec4 mvPosition=modelViewMatrix*vec4(x,y,z,1.);gl_Position=projectionMatrix*mvPosition;
   #include <logdepthbuf_vertex>
   }`,fragmentShader:logFragment+`
   uniform float opacity;void main(){gl_FragColor=vec4(.72,.80,.78,opacity);
   #include <logdepthbuf_fragment>
   }`});this.trails=new THREE.LineSegments(g,m);this.trails.frustumCulled=false;this.root.add(this.trails);
 }
 makeFlags(){
  this.flagGroup=new THREE.Group();this.flagGroup.name='RiversideWindFlags';this.root.add(this.flagGroup);
  for(let i=0;i<3;i++){
   const group=new THREE.Group();group.position.set(115,0,76+i*7);this.flagGroup.add(group);
   const pole=new THREE.Mesh(new THREE.CylinderGeometry(.055,.075,4.8,8),new THREE.MeshStandardMaterial({color:'#475850',roughness:.65}));pole.position.y=2.4;group.add(pole);
   const g=new THREE.PlaneGeometry(2.4,1.15,24,8);g.translate(1.2,3.95,0);
   const m=new THREE.MeshStandardMaterial({color:['#c57f56','#bca768','#648e81'][i],side:THREE.DoubleSide,roughness:.85});
   m.onBeforeCompile=shader=>{Object.assign(shader.uniforms,this.uniforms);shader.vertexShader='uniform float wxTime,wxWind;\n'+shader.vertexShader;shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>',`#include <begin_vertex>
    float pin=clamp(position.x/2.4,0.,1.);transformed.z+=pin*(.035+min(wxWind*.07,.7))*sin(wxTime*(2.+wxWind*.35)-position.x*3.2+position.y*1.8);
    transformed.y-=pin*.32/(1.+wxWind);`);};m.customProgramCacheKey=()=> 'v4-flag';
   const flag=new THREE.Mesh(g,m);flag.frustumCulled=false;group.add(flag);this.flags.push(flag);
  }
 }
 update(s,t,interior){
  this.uniforms.wxTime.value=t;this.uniforms.wxWind.value=s.visual.wind;this.uniforms.wxSnow.value=s.snowDepth;this.uniforms.wxRiver.value=s.riverRise;
  for(const layer of this.snowLayers)layer.visible=s.snowDepth>.001&&!interior;
  this.snowCount=Math.round(s.visual.snow*14000);this.snowfall.geometry.setDrawRange(0,this.snowCount);this.snowfall.visible=this.snowCount>8&&!interior;this.snowfall.material.uniforms.pixelScale.value=this.env.renderer.domElement.height;
  this.cyclone.visible=s.visual.tornado>.01&&!interior;this.cyclone.position.set(152+Math.sin(t*.09)*2,0,Math.sin(t*.06)*15);this.cyclone.scale.setScalar(.65+s.visual.tornado*.35);
  for(const m of [this.funnel.material,this.debris.material]){m.uniforms.t.value=t;m.uniforms.power.value=s.visual.tornado;}
  this.trails.visible=s.visual.wind>4&&!interior;this.trails.material.uniforms.opacity.value=Math.min(.18,(s.visual.wind-4)*.018);
  this.flagGroup.visible=!interior&&(this.env.asset?.children.find(o=>o.name==='T__Planting')?.visible??true);
 }
 snapshot(){return {...this.quality,snowCount:this.snowCount,snowVisible:this.snowfall.visible,tornadoVisible:this.cyclone.visible,windTrails:this.trails.visible,riverOffset:this.uniforms.wxRiver.value,windStrength:this.uniforms.wxWind.value};}
}
