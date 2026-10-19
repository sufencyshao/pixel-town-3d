'use strict';
const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'..'),r=path.join(root,'design/town-ai-v9'),b=path.join(root,'design/whole-town-realistic-actors-v8');
function dependency(name){try{return require(name)}catch{return require(path.join(root,'design/river-park-3d-v1/node_modules',name))}}
async function main(){
 require('./build-town-3d-capabilities');
 const esbuild=dependency('esbuild');
 await esbuild.build({entryPoints:[path.join(r,'src/viewer.js')],bundle:true,format:'iife',minify:true,outfile:path.join(r,'viewer.bundle.js'),nodePaths:[path.join(root,'node_modules'),path.join(root,'design/river-park-3d-v1/node_modules')],logLevel:'info'});
 const read=p=>fs.readFileSync(p,'utf8'),json=p=>JSON.parse(read(p)),js=v=>JSON.stringify(v).replace(/<\//g,'<\\/'),enc=p=>fs.readFileSync(p).toString('base64');
 const index=json(path.join(b,'reference/asset-index.json')),motions=json(path.join(b,'reference/animation-models.json'));
 let s=read(path.join(b,'template.html')).replace('现成人物与动物 V8','三维 AI 生活 V9');
 s=s.replace('<meta charset="utf-8">',`<meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src blob:; object-src 'none'; base-uri 'none'">`);
 s=s.replace('<aside>','<aside>'+read(path.join(r,'panel.html'))).replace('</style>',read(path.join(r,'panel.css'))+'</style>');
 s=s.replace('本版尚未接自主寻路','AI 已接公共步道导航');
 s=s.replace('<script>window.TOWN_META=','<script>window.TOWN_CAPABILITIES='+read(path.join(r,'capabilities.json'))+';window.TOWN_NAVIGATION='+read(path.join(b,'reference/navigation.json'))+';window.TOWN_PUBLIC_CATALOG='+js(json(path.join(r,'catalog-public.json')))+';</script><script>window.TOWN_META=');
 const replacements={__META__:read(path.join(b,'manifest.json')),__ENV__:read(path.join(b,'environment-data.json')),__ASSET__:js(enc(path.join(b,'Town-complete.glb'))),__ACTORS__:read(path.join(b,'actors.json')),__MODELS__:js(Object.fromEntries(Object.entries(index).map(([k,p])=>[k,enc(path.join(b,p))]))),__MOTION_META__:js(motions),__MOTIONS__:js(Object.fromEntries(motions.map(m=>[m.id,enc(path.join(b,'animations',m.id+'.glb'))]))),__PENDING__:read(path.join(b,'reference/pending-animals.json')),__VIEWER__:read(path.join(r,'viewer.bundle.js'))};
 for(const [key,value] of Object.entries(replacements))s=s.replace(key,()=>value);
 const target=path.join(r,'三维小镇-AI生活.html'),tmp=target+'.tmp';fs.writeFileSync(tmp,s);fs.renameSync(tmp,target);console.log('V9 HTML bytes',Buffer.byteLength(s));
}
main().catch(e=>{console.error(e);process.exitCode=1});
