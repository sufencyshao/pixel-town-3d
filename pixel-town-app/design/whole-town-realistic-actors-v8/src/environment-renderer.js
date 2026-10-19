import * as THREE from 'three';
import {SeasonalVegetation} from './seasonal-vegetation.js';
import {ExtendedWeather} from './extended-weather.js';
import {EnvironmentState,WEATHER,solar,clamp} from './environment-state.js';

const vertex=`varying vec3 vDir; void main(){vDir=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`;
const skyFragment=`precision highp float;
varying vec3 vDir;uniform vec3 uSky,uCloud;uniform float uTime,uCover,uNight,uFlash;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+1.),f.x),f.y);}
float fbm(vec2 p){return .56*noise(p)+.28*noise(p*2.1)+.12*noise(p*4.3)+.04*noise(p*8.1);}
void main(){vec3 dir=normalize(vDir);vec2 p=dir.xz*4.5/(.45+abs(dir.y));p+=vec2(uTime*.006,uTime*.002);float n=fbm(p);float clouds=smoothstep(.84-uCover*.66,.98-uCover*.60,n);vec3 sky=uSky*mix(.80,1.12,clamp(dir.y*.5+.5,0.,1.));vec3 c=mix(sky,uCloud,clouds*.94);float star=step(.9988,hash(floor(dir.xz*900.)))*uNight*(1.-clouds)*.5;c+=star;c+=uFlash*.18;gl_FragColor=vec4(c,1.);#include <tonemapping_fragment>
#include <colorspace_fragment>
}`.replace(';#include',';\n#include');

const rainVertex=`
#include <common>
#include <logdepthbuf_pars_vertex>
attribute vec3 seed;attribute float tip;uniform float uTime,uSpeed,uWind,uLength;uniform sampler2D uHeight;varying float vAlpha;
void main(){float x=-135.+mod(seed.x*300.+uTime*uWind,300.);float z=-115.+mod(seed.z*225.+uTime*uWind*.3,225.);float y=mod(seed.y*44.-uTime*uSpeed,44.)-tip*uLength;float ground=texture2D(uHeight,vec2(((x+135.)/.75+.5)/401.,((z+115.)/.75+.5)/301.)).r;vAlpha=step(ground+.18,y);vec4 mvPosition=modelViewMatrix*vec4(x-tip*uWind*.08,y,z,1.);gl_Position=projectionMatrix*mvPosition;
#include <logdepthbuf_vertex>
}`;
const rainFragment=`
#include <common>
#include <logdepthbuf_pars_fragment>
varying float vAlpha;uniform float uOpacity;uniform vec3 uRainColor;
void main(){if(vAlpha<.5)discard;gl_FragColor=vec4(uRainColor,uOpacity);
#include <logdepthbuf_fragment>
#include <tonemapping_fragment>
#include <colorspace_fragment>
}`;

const splashVertex=`
#include <common>
#include <logdepthbuf_pars_vertex>
attribute vec3 splashSeed;varying vec2 vUv;varying float vAge;uniform float uTime;uniform sampler2D uHeight;
void main(){vUv=uv;vAge=fract(uTime*1.7+splashSeed.y);float x=-135.+splashSeed.x*300.,z=-115.+splashSeed.z*225.;float ground=texture2D(uHeight,vec2(((x+135.)/.75+.5)/401.,((z+115.)/.75+.5)/301.)).r;float radius=.12+vAge*.42;vec4 mvPosition=modelViewMatrix*vec4(x+position.x*radius,ground+.035,z+position.y*radius,1.);gl_Position=projectionMatrix*mvPosition;
#include <logdepthbuf_vertex>
}`;
const splashFragment=`
#include <common>
#include <logdepthbuf_pars_fragment>
varying vec2 vUv;varying float vAge;
void main(){float r=length(vUv-.5)*2.;float ring=smoothstep(.65,.80,r)*(1.-smoothstep(.86,1.,r));gl_FragColor=vec4(.65,.78,.84,ring*(1.-vAge)*.30);
#include <logdepthbuf_fragment>
}`;

export class TownEnvironment {
  constructor(scene,camera,renderer,meta,data,onChange){
    this.scene=scene;this.camera=camera;this.renderer=renderer;this.meta=meta;this.data=data;this.onChange=onChange;
    this.state=new EnvironmentState();this.seconds=0;this.flash=0;this.flashEnabled=!matchMedia('(prefers-reduced-motion: reduce)').matches;this.sound=false;this.nextLightning=10;this.lightningCount=0;this.lastShadow=-99;this.materials=[];this.lampMaterials=[];this.rainCount=0;this.asset=null;
    this.ambient=new THREE.HemisphereLight('#d7e6f0','#676c4d',1.7);scene.add(this.ambient);
    this.sun=new THREE.DirectionalLight('#fff1d8',2.4);this.sun.target.position.set(15,0,0);scene.add(this.sun,this.sun.target);
    this.sun.castShadow=true;this.sun.shadow.mapSize.set(1024,1024);Object.assign(this.sun.shadow.camera,{left:-200,right:200,top:160,bottom:-160,near:50,far:900});this.sun.shadow.bias=-.0003;this.sun.shadow.normalBias=.12;
    this.moon=new THREE.DirectionalLight('#8da8df',.16);this.moon.position.set(-160,240,-200);scene.add(this.moon);
    renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;
    this.sky=new THREE.Mesh(new THREE.SphereGeometry(1000,32,16),new THREE.ShaderMaterial({vertexShader:vertex,fragmentShader:skyFragment,side:THREE.BackSide,depthWrite:false,depthTest:false,uniforms:{uSky:{value:new THREE.Color()},uCloud:{value:new THREE.Color()},uTime:{value:0},uCover:{value:.1},uNight:{value:0},uFlash:{value:0}}}));this.sky.renderOrder=-100;this.sky.frustumCulled=false;scene.add(this.sky);
    this.root=new THREE.Group();this.root.name='TimeWeatherRuntime';scene.add(this.root);
    const g=data.grid;this.heightTexture=new THREE.DataTexture(new Float32Array(g.heights),g.nx,g.nz,THREE.RedFormat,THREE.FloatType);this.heightTexture.minFilter=this.heightTexture.magFilter=THREE.NearestFilter;this.heightTexture.needsUpdate=true;
    let seed=42;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
    const max=12000,positions=new Float32Array(max*6),seeds=new Float32Array(max*6),tips=new Float32Array(max*2);
    for(let i=0;i<max;i++){const a=[random(),random(),random()];seeds.set(a,i*6);seeds.set(a,i*6+3);tips[i*2+1]=1;}
    const rg=new THREE.BufferGeometry();rg.setAttribute('position',new THREE.BufferAttribute(positions,3));rg.setAttribute('seed',new THREE.BufferAttribute(seeds,3));rg.setAttribute('tip',new THREE.BufferAttribute(tips,1));
    this.rain=new THREE.LineSegments(rg,new THREE.ShaderMaterial({vertexShader:rainVertex,fragmentShader:rainFragment,transparent:true,depthWrite:false,uniforms:{uTime:{value:0},uSpeed:{value:12},uWind:{value:1},uLength:{value:1},uHeight:{value:this.heightTexture},uOpacity:{value:.4},uRainColor:{value:new THREE.Color('#b7d5e2')}}}));this.rain.frustumCulled=false;this.rain.name='Rain';this.root.add(this.rain);
    const sg=new THREE.InstancedBufferGeometry().copy(new THREE.PlaneGeometry(2,2));const ss=new Float32Array(700*3);for(let i=0;i<ss.length;i++)ss[i]=random();sg.setAttribute('splashSeed',new THREE.InstancedBufferAttribute(ss,3));sg.instanceCount=0;
    this.splashes=new THREE.Mesh(sg,new THREE.ShaderMaterial({vertexShader:splashVertex,fragmentShader:splashFragment,transparent:true,depthWrite:false,side:THREE.DoubleSide,uniforms:{uTime:{value:0},uHeight:{value:this.heightTexture}}}));this.splashes.frustumCulled=false;this.root.add(this.splashes);
    const canvas=document.createElement('canvas');canvas.width=canvas.height=64;const ctx=canvas.getContext('2d'),gradient=ctx.createRadialGradient(32,32,0,32,32,32);gradient.addColorStop(0,'rgba(255,225,153,1)');gradient.addColorStop(.25,'rgba(255,213,129,.45)');gradient.addColorStop(1,'rgba(255,198,110,0)');ctx.fillStyle=gradient;ctx.fillRect(0,0,64,64);const glowMap=new THREE.CanvasTexture(canvas);
    const lp=new THREE.BufferGeometry();lp.setAttribute('position',new THREE.Float32BufferAttribute(data.lamps.flat(),3));this.halos=new THREE.Points(lp,new THREE.PointsMaterial({map:glowMap,color:'#ffcc7f',size:1.5,transparent:true,depthWrite:false,blending:THREE.AdditiveBlending}));this.root.add(this.halos);
    this.pools=new THREE.InstancedMesh(new THREE.PlaneGeometry(8,8),new THREE.MeshBasicMaterial({map:glowMap,color:'#ffc36a',transparent:true,depthWrite:false,blending:THREE.AdditiveBlending,side:THREE.DoubleSide,opacity:.45}),data.lamps.length);
    const matrix=new THREE.Matrix4(),q=new THREE.Quaternion().setFromEuler(new THREE.Euler(-Math.PI/2,0,0));data.lamps.forEach((p,i)=>{matrix.compose(new THREE.Vector3(p[0],.125,p[2]),q,new THREE.Vector3(1,1,1));this.pools.setMatrixAt(i,matrix)});this.pools.instanceMatrix.needsUpdate=true;this.root.add(this.pools);
    this.nearLights=Array.from({length:8},()=>{const l=new THREE.PointLight('#ffd49b',0,13,2);scene.add(l);return l});
    const boltPoints=[];for(let i=0;i<11;i++)boltPoints.push(new THREE.Vector3(155+(i%2?3:-3),90-i*7,-70+i*.5));this.bolt=new THREE.Line(new THREE.BufferGeometry().setFromPoints(boltPoints),new THREE.LineBasicMaterial({color:'#dbe8ff',transparent:true,opacity:0}));this.root.add(this.bolt);this.extended=new ExtendedWeather(this);this.vegetation=new SeasonalVegetation(this);
  }
  attach(asset){
    this.asset=asset;const seen=new Set();
    asset.traverse(o=>{if(!o.isMesh)return;o.receiveShadow=true;const mats=Array.isArray(o.material)?o.material:[o.material];o.castShadow=!mats.some(m=>m.transparent)&&!o.name.startsWith('T__');for(const m of mats){if(seen.has(m))continue;seen.add(m);if(/^(asphalt|path|stone|road|tile)(\.|$)/.test(m.name))this.materials.push({m,color:m.color.clone(),roughness:m.roughness});}});
    const glow=asset.children.find(o=>o.name==='T__Lamp_Glow');glow?.traverse(o=>{if(o.isMesh)for(const m of (Array.isArray(o.material)?o.material:[o.material]))if(!this.lampMaterials.includes(m))this.lampMaterials.push(m)});
    this.extended.attach(asset);this.vegetation.attach(asset);this.renderer.shadowMap.needsUpdate=true;this.update(0,{target:new THREE.Vector3(),interior:false,lampsVisible:true});
  }
  triggerLightning(){
    if(!['storm','typhoon'].includes(this.state.weather)||!this.flashEnabled)return false;
    this.flash=.75;this.lightningCount++;this.bolt.position.x=(this.lightningCount%3-1)*7;this.nextLightning=this.seconds+8+(this.lightningCount*7%9);if(this.sound)this.thunder();return true;
  }
  enableSound(value){this.sound=value;if(value){const AC=window.AudioContext||window.webkitAudioContext;if(AC){this.audio??=new AC();this.audio.resume();}}}
  thunder(){
    const ac=this.audio;if(!ac||ac.state!=='running')return;const duration=2.8,buffer=ac.createBuffer(1,Math.floor(ac.sampleRate*duration),ac.sampleRate),a=buffer.getChannelData(0);let n=0;
    for(let i=0;i<a.length;i++){n=.95*n+.05*(Math.random()*2-1);a[i]=n*Math.pow(1-i/a.length,2);}
    const src=ac.createBufferSource();src.buffer=buffer;const filter=ac.createBiquadFilter();filter.type='lowpass';filter.frequency.value=230;const gain=ac.createGain();gain.gain.value=.7;src.connect(filter).connect(gain).connect(ac.destination);src.start(ac.currentTime+.6);src.onended=()=>{src.disconnect();filter.disconnect();gain.disconnect()};
  }
  update(dt,{target,interior=false,lampsVisible=true}={}){
    this.seconds+=dt;this.state.advance(dt);const s=this.state.snapshot(),v=s.visual;
    if(['storm','typhoon'].includes(s.weather)&&this.seconds>=this.nextLightning&&v.rain>.7)this.triggerLightning();
    if(!['storm','typhoon'].includes(s.weather))this.flash=0;this.flash=Math.max(0,this.flash-dt*4.5);const f=this.flashEnabled?this.flash:0;
    this.sky.position.copy(this.camera.position);const su=this.sky.material.uniforms;
    const dayColor=new THREE.Color('#8fbcd2').lerp(new THREE.Color('#596771'),v.dark),nightColor=new THREE.Color('#101a30');su.uSky.value.copy(nightColor).lerp(dayColor,s.daylight);
    if(s.dusk>0&&v.dark<.5)su.uSky.value.lerp(new THREE.Color('#d7997b'),s.dusk*.3*s.daylight);
    su.uCloud.value.copy(new THREE.Color('#273247')).lerp(new THREE.Color('#e6e6df').lerp(new THREE.Color('#737f86'),v.dark),s.daylight);su.uCover.value=v.cloud;su.uTime.value=this.seconds;su.uNight.value=s.night;su.uFlash.value=f;
    this.scene.fog??=new THREE.FogExp2('#8695a2',.0001);this.scene.fog.color.copy(su.uSky.value);this.scene.fog.density=v.fog;
    this.ambient.intensity=.34+s.daylight*(1.22-v.dark*.45)+f*.8;this.ambient.color.set(s.daylight>.3?'#d9e7ee':'#879ec5');
    this.sun.intensity=Math.max(0,s.elevation)*3.0*(1-v.dark*.88)+f*.8;this.sun.color.set(s.elevation<.35?'#ffd2a2':'#fff2db');this.sun.position.copy(this.sun.target.position).addScaledVector(new THREE.Vector3(...s.sunDirection),350);
    this.moon.intensity=.28*s.night*(1-v.dark*.55);this.renderer.toneMappingExposure=1.04;
    if(Math.abs(this.seconds-this.lastShadow)>1){this.renderer.shadowMap.needsUpdate=true;this.lastShadow=this.seconds;}
    for(const {m,color,roughness} of this.materials){m.color.copy(color).multiplyScalar(1-.22*s.wetness);m.roughness=THREE.MathUtils.lerp(roughness,/asphalt/.test(m.name)?.20:.37,s.wetness);}
    const night=s.night;for(const m of this.lampMaterials)m.emissiveIntensity=.015+night*5;
    this.halos.visible=this.pools.visible=lampsVisible&&night>.01;this.halos.material.opacity=night*.7;this.pools.material.opacity=night*(.40+s.wetness*.12);
    const t=target||this.camera.position,near=[...this.data.lamps].sort((a,b)=>(a[0]-t.x)**2+(a[2]-t.z)**2-((b[0]-t.x)**2+(b[2]-t.z)**2));
    this.nearLights.forEach((l,i)=>{l.position.set(...near[i]);l.intensity=lampsVisible?night*45:0;});
    this.rainCount=Math.round(v.rain*12000);this.rain.geometry.setDrawRange(0,this.rainCount*2);this.rain.visible=this.rainCount>15&&!interior;
    const ru=this.rain.material.uniforms;ru.uTime.value=this.seconds;ru.uSpeed.value=10+v.rain*15;ru.uWind.value=v.wind;ru.uLength.value=.8+v.rain*1.8;ru.uOpacity.value=.16+v.rain*.15;ru.uRainColor.value.set(night>.5?'#a4c6e8':'#b9d3df');
    this.splashes.visible=this.rain.visible;this.splashes.geometry.instanceCount=Math.round(v.rain*700);this.splashes.material.uniforms.uTime.value=this.seconds;
    this.extended.update(s,this.seconds,interior);this.vegetation.update(s,this.seconds,interior);this.bolt.visible=f>0;this.bolt.material.opacity=f;this.onChange?.(s);return s;
  }
  snapshot(){return {...this.state.snapshot(),rainCount:this.rainCount,lampsOn:this.state.snapshot().night>.5,lampCount:this.data.lamps.length,activePointLights:this.nearLights.filter(l=>l.intensity>.1).length,lightningCount:this.lightningCount,flash:this.flash,rainVisible:this.rain.visible,wetMaterials:this.materials.length,...this.extended.snapshot(),...this.vegetation.snapshot()};}
}
