'use strict';
const path=require('path');
const {spawn}=require('child_process');
let electron;
try{electron=require('electron');}catch{electron=require('../../node_modules/electron');}
const env={...process.env};delete env.ELECTRON_RUN_AS_NODE;
const child=spawn(electron,[path.join(__dirname,'renderer.test.cjs')],{stdio:'inherit',env});
child.on('error',error=>{console.error(error.message);process.exitCode=1;});
child.on('exit',code=>{process.exitCode=code||0;});
