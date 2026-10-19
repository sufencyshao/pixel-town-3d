'use strict';
const {spawn}=require('child_process');
const path=require('path');
// Node resolution finds this project's dependency first, then the original runtime.
const child=spawn(require('electron'),[path.resolve(__dirname,'..'),...process.argv.slice(2)],{stdio:'inherit',env:process.env});
child.on('error',e=>{console.error(e.message);process.exit(1);});
child.on('exit',code=>process.exit(code||0));
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>child.kill(signal));
