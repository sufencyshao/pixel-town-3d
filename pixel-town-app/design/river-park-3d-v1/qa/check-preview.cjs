const {chromium}=require('/Users/summerwindy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const base='http://127.0.0.1:58709/';
 await page.goto(base+'river-park-3d-v1/河岸公园-离线预览.html');await page.waitForFunction(()=>window.parkViewer?.current);
 const result={views:[],errors};
 for(const mode of ['overview','plan','vet','pets','stage','river','habitat']){
  await page.locator('[data-view="'+mode+'"]').click();await page.waitForTimeout(180);
  result.views.push(await page.evaluate(()=>({mode:parkViewer.mode,meshCount:(()=>{let n=0;parkViewer.current.traverse(o=>{if(o.isMesh)n++});return n;})(),roof:parkViewer.current.getObjectByName('Vet_Roof').visible,vetFront:parkViewer.current.getObjectByName('Vet_Front').visible})));
 }
 await page.locator('[data-view="overview"]').click();await page.waitForTimeout(200);await page.screenshot({path:path.join(__dirname,'desktop.png')});
 await page.locator('#roof').uncheck();if(await page.evaluate(()=>parkViewer.current.getObjectByName('Vet_Roof').visible))throw Error('Roof toggle failed');
 await page.locator('#auto').check();if(!await page.evaluate(()=>parkViewer.controls.autoRotate))throw Error('autorotate failed');await page.locator('#auto').uncheck();
 const dl=page.waitForEvent('download');await page.locator('#download').click();result.glbDownload=(await dl).suggestedFilename();
 const cap=page.waitForEvent('download');await page.locator('#capture').click();result.capture=(await cap).suggestedFilename();
 await page.setViewportSize({width:390,height:844});await page.locator('[data-view="overview"]').click();await page.waitForTimeout(250);await page.screenshot({path:path.join(__dirname,'mobile.png'),fullPage:true});
 result.mobile=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,canvasWidth:document.querySelector('canvas').getBoundingClientRect().width}));
 if(result.mobile.scrollWidth>390)throw Error('mobile overflow');
 await page.goto('file://'+path.resolve(__dirname,'../河岸公园-离线预览.html'));await page.waitForFunction(()=>window.parkViewer?.current);result.fileOfflineLoaded=true;
 await browser.close();if(errors.length)throw Error(errors.join('\n'));fs.writeFileSync(path.join(__dirname,'browser-checks.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
})().catch(e=>{console.error(e);process.exit(1)});
