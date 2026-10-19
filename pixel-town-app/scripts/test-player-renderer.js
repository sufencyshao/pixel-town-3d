'use strict';
const path=require('node:path');
const {spawn}=require('node:child_process');
let electron;try{electron=require('electron');}catch{electron=require('../../node_modules/electron');}
const env={...process.env};delete env.ELECTRON_RUN_AS_NODE;
const child=spawn(electron,[path.join(__dirname,'player-renderer.cjs')],{stdio:'inherit',env});
child.on('error',e=>{console.error(e.message);process.exitCode=1;});child.on('exit',code=>process.exitCode=code||0);
