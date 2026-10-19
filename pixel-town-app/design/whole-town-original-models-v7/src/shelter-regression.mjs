import {readFileSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {AnimalLife} from './animal-simulation.js';
const root=fileURLToPath(new URL('../',import.meta.url));
const profiles=JSON.parse(readFileSync(root+'reference/runtime-animal-manifest.json')).animals;
const navigation=JSON.parse(readFileSync(root+'reference/navigation.json'));
const cases=[];
for(let seed=1;seed<=12;seed++){
 const sim=new AnimalLife(profiles,navigation,{seed});
 for(let i=0;i<900;i++)sim.update(.05,{hour:12,weather:'sunny'});
 for(let i=0;i<2400;i++)sim.update(.05,{hour:12,weather:'rain'});
 const failures=sim.animals.filter(a=>a.state!=='rest'||Math.hypot(a.position[0]-a.restSlot[0],a.position[2]-a.restSlot[2])>.15);
 cases.push({seed,pass:failures.length===0,failures:failures.map(a=>({id:a.id,state:a.state,position:a.position,rest:a.restSlot,path:a.path}))});
}
const pass=cases.every(c=>c.pass);
writeFileSync(root+'qa/shelter-regression.json',JSON.stringify({cases,status:pass?'PASS':'FAIL'},null,2));
console.log('Shelter regression:',cases.filter(c=>c.pass).length+'/'+cases.length);
if(!pass)process.exitCode=1;
