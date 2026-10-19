'use strict';
const {spawn}=require('child_process'),path=require('path');
let electron;try{electron=require('electron')}catch{electron=require('../../node_modules/electron')}
const env={...process.env};delete env.ELECTRON_RUN_AS_NODE;
const child=spawn(electron,[path.join(__dirname,'town-3d-renderer.cjs')],{stdio:'inherit',env});child.on('error',e=>{console.error(e);process.exitCode=1});child.on('exit',c=>process.exitCode=c||0);
