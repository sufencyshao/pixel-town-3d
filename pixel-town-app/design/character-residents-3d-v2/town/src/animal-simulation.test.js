import test from 'node:test';
import assert from 'node:assert/strict';
import {NavGrid,AnimalLife} from './animal-simulation.js';
const grid={origin:[0,0],cols:20,rows:20,spacing:.5,cells:Array.from({length:400},(_,i)=>i),heights:Array(400).fill(.05)};
const h={...grid,id:'park',name:'公园',center:[4,.05,4],shelter:[1,.05,1],food:[2,.05,2],drink:[2,.05,3],humanSpawn:[3,.05,3],perches:[[5,2,5],[6,2,5]],petIds:['dog-a','dog-b','cat-a','bird-a']};
const animals=[['dog-a','狗'],['dog-b','狗'],['cat-a','猫'],['bird-a','鸟']].map(([id,species])=>({id,name:id,species,breed:'test',radius:species==='鸟'?.08:.2,height:.4,actions:['Idle','Walk','Run','Eat','Rest','Fly']}));
function make(){return new AnimalLife(animals,{habitats:[h],humanNavigation:grid},{seed:17})}
function step(life,seconds){for(let i=0;i<seconds*30;i++)life.update(1/30,{hour:10,weather:'sunny',season:'spring'});}
test('navigation routes around blocked cells and forbids diagonal corner cutting',()=>{const g=new NavGrid({...grid,cells:grid.cells.filter(i=>i%20!==10||i>300)});const p=g.path([1,1],[8,1]);assert.ok(p.length>3);assert.ok(p.every(x=>g.legal(x[0],x[1])));assert.ok(p.some(x=>x[1]>7));});
test('feeding has approach and completion, not an immediate status change',()=>{const l=make();const a=l.animals[0];a.hunger=.8;assert.equal(l.command(a.id,'feed').ok,true);assert.notEqual(l.human.phase,'feeding');step(l,35);assert.ok(a.hunger<.2);assert.ok(l.events.some(e=>e.kind==='feed-complete'));});
test('social interaction reserves two compatible animals and completes',()=>{const l=make();assert.equal(l.command('dog-a','social').ok,true);step(l,45);assert.ok(l.events.some(e=>e.kind==='social-complete'));assert.ok(l.animals.every(a=>!a.partner));});
test('fetch is limited to dogs and ball returns',()=>{const l=make();assert.equal(l.command('cat-a','fetch').ok,false);assert.equal(l.command('dog-a','fetch').ok,true);step(l,55);assert.ok(l.events.some(e=>e.kind==='fetch-complete'));});
test('bad weather interrupts play and starts shelter travel',()=>{const l=make();l.command('dog-a','social');for(let i=0;i<400;i++)l.update(.05,{hour:10,weather:'storm',season:'summer'});assert.ok(l.animals.every(a=>['shelter','rest'].includes(a.state)));assert.equal(l.human.task,null);});
test('pause freezes movement, needs, and interaction clocks',()=>{const l=make();step(l,1);l.paused=true;const before=JSON.stringify(l.snapshot());step(l,4);assert.equal(JSON.stringify(l.snapshot()),before);});
test('long activity remains finite and on legal habitat ground',()=>{const l=make();step(l,120);for(const a of l.animals){assert.ok(a.position.every(Number.isFinite));if(a.air<=.4)assert.ok(a.grid.legal(a.position[0],a.position[2]));assert.ok(a.energy>=0&&a.energy<=1);}assert.equal(l.animals.length,4);});
test('cancel releases reservations and resets human task',()=>{const l=make();l.command('dog-a','pet');l.cancel();assert.equal(l.human.task,null);assert.ok(l.animals.every(a=>!a.reserved));});

test('friendly cat and dog can greet without chase play',()=>{const l=make();assert.equal(l.command('cat-a','social').ok,true);step(l,45);assert.ok(l.events.some(e=>e.kind==='social-complete'&&e.ids.includes('cat-a')));});
test('a flight request in midair does not reset to an old perch',()=>{const l=make(),a=l.get('bird-a');l.fly(a);l.update(.1);const before=a.position.slice(),flight=a.flight;l.fly(a);assert.equal(a.flight,flight);l.update(.1);assert.ok(Math.hypot(...a.position.map((v,i)=>v-before[i]))<.3);});
