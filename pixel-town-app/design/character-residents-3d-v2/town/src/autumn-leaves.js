import * as THREE from 'three';

// A bounded fall plume for each existing outdoor crown. No screen-space confetti.
export class AutumnLeaves {
 constructor(env){
  this.env=env;this.count=1800;this.anchors=[];this.uniforms={leafTime:{value:0},leafWind:{value:0},leafOpacity:{value:0}};
  const vertex=`
   #include <common>
   #include <logdepthbuf_pars_vertex>
   attribute vec3 leafAnchor,leafSeed;attribute float leafRadius,leafEnabled;
   uniform float leafTime,leafWind;varying vec2 leafUv;varying vec3 leafTint;varying float leafFade;
   void main(){
    float cycle=fract(leafTime*(.065+leafSeed.z*.045)+leafSeed.x);
    float angle=leafSeed.y*6.2831853,flutter=leafTime*(2.+leafSeed.z*3.)+angle;
    float drop=max(1.,leafAnchor.y-.16);
    vec3 center=leafAnchor;
    center.x+=cos(angle)*leafRadius*.62+cycle*min(leafWind*.50,5.)+sin(flutter*.58)*(.25+cycle*.6);
    center.z+=sin(angle)*leafRadius*.62+cycle*min(leafWind*.16,1.8)+cos(flutter*.46)*.45;
    center.y=max(.16,leafAnchor.y-cycle*drop+sin(flutter)*.13);
    vec3 local=position*(.75+leafSeed.z*.85);
    float yaw=flutter*.72,pitch=sin(flutter*.83)*1.2;
    local=vec3(local.x,local.y*cos(pitch)-local.z*sin(pitch),local.y*sin(pitch)+local.z*cos(pitch));
    local=vec3(local.x*cos(yaw)-local.z*sin(yaw),local.y,local.x*sin(yaw)+local.z*cos(yaw));
    vec4 mvPosition=modelViewMatrix*vec4(center+local,1.);gl_Position=projectionMatrix*mvPosition;
    leafUv=uv;leafTint=mix(vec3(.47,.19,.07),vec3(.86,.53,.14),leafSeed.y);
    leafFade=leafEnabled*smoothstep(0.,.06,cycle)*(1.-smoothstep(.88,1.,cycle));
    #include <logdepthbuf_vertex>
   }`;
  const fragment=`
   #include <common>
   #include <logdepthbuf_pars_fragment>
   uniform float leafOpacity;varying vec2 leafUv;varying vec3 leafTint;varying float leafFade;
   void main(){
    float vein=1.-smoothstep(.018,.04,abs(leafUv.x-.5));
    gl_FragColor=vec4(mix(leafTint,leafTint*.62,vein*.65),leafFade*leafOpacity);
    #include <logdepthbuf_fragment>
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
   }`;
  const g=new THREE.InstancedBufferGeometry();
  // Six-sided pointed leaf, about 15–34 cm long across the seeded scales.
  const p=[0,0,0,-.09,.02,0,-.065,.095,0,0,0,0,-.065,.095,0,0,.15,0,0,0,0,0,.15,0,.08,.04,0,0,0,0,.08,.04,0,0,-.12,0,0,0,0,0,-.12,0,-.09,.02,0];
  g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(p.flatMap((_,i)=>i%3===0?[p[i]/.2+.5,p[i+1]/.3+.5]:[]),2));g.instanceCount=0;
  this.mesh=new THREE.Mesh(g,new THREE.ShaderMaterial({vertexShader:vertex,fragmentShader:fragment,uniforms:this.uniforms,side:THREE.DoubleSide,transparent:true,depthWrite:false}));this.mesh.name='AutumnWindLeaves';this.mesh.frustumCulled=false;env.scene.add(this.mesh);
 }
 attach(anchors){
  this.anchors=anchors;const g=this.mesh.geometry,positions=new Float32Array(this.count*3),seeds=new Float32Array(this.count*3),radii=new Float32Array(this.count);this.sources=[];this.visibilityKey=null;
  let n=107;const random=()=>{n=(Math.imul(n,1664525)+1013904223)>>>0;return n/4294967296};
  for(let i=0;i<this.count;i++){const a=anchors[Math.floor(random()*anchors.length)];if(!a)continue;this.sources.push(a);a.center.toArray(positions,i*3);radii[i]=Math.min(4,a.radius);seeds.set([random(),random(),random()],i*3);}
  g.setAttribute('leafEnabled',new THREE.InstancedBufferAttribute(new Float32Array(this.count).fill(1),1));g.setAttribute('leafAnchor',new THREE.InstancedBufferAttribute(positions,3));g.setAttribute('leafSeed',new THREE.InstancedBufferAttribute(seeds,3));g.setAttribute('leafRadius',new THREE.InstancedBufferAttribute(radii,1));
 }
 update(s,seconds,interior){
  if(this.sources){const signature=this.anchors.map(a=>a.owner.visible?'1':'0').join('');if(signature!==this.visibilityKey){this.visibilityKey=signature;const active=this.mesh.geometry.attributes.leafEnabled;for(let i=0;i<this.sources.length;i++)active.setX(i,this.sources[i].owner.visible?1:0);active.needsUpdate=true;}}
  const wind=s.visual.wind,amount=s.season==='autumn'?THREE.MathUtils.clamp((wind-1.2)/6.3,0,1):0;
  this.mesh.visible=amount>.01&&!interior&&this.anchors.length>0;this.mesh.geometry.instanceCount=this.mesh.visible?Math.round(180+amount*(this.count-180)):0;
  this.uniforms.leafTime.value=seconds;this.uniforms.leafWind.value=wind;this.uniforms.leafOpacity.value=.86+s.daylight*.14;
 }
 snapshot(){return {autumnLeafCount:this.mesh.geometry.instanceCount,autumnLeavesVisible:this.mesh.visible,autumnLeafSources:this.anchors.length};}
}
