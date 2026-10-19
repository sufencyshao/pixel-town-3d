const {chromium}=require('/Users/summerwindy/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const base='http://127.0.0.1:58709/';
 await page.goto(base+'garden-greenhouse-3d-v1/田园与温室-离线预览.html');await page.waitForFunction(()=>window.gardenViewer?.current);
 const result={views:[],errors};
 for(const mode of ['overview','plan','greenhouse','tool','fields','orchard']){
  await page.locator('[data-view="'+mode+'"]').click();await page.waitForTimeout(180);
  result.views.push(await page.evaluate(()=>({mode:gardenViewer.mode,meshCount:(()=>{let n=0;gardenViewer.current.traverse(o=>{if(o.isMesh)n++});return n;})(),roof:gardenViewer.current.getObjectByName('Greenhouse_Roof').visible,toolFront:gardenViewer.current.getObjectByName('Tool_Front').visible})));
 }
 await page.locator('[data-view="overview"]').click();await page.waitForTimeout(200);await page.screenshot({path:path.join(__dirname,'desktop.png')});
 await page.locator('#roof').uncheck();if(await page.evaluate(()=>gardenViewer.current.getObjectByName('Tool_Roof').visible))throw Error('Roof toggle failed');
 await page.locator('#auto').check();if(!await page.evaluate(()=>gardenViewer.controls.autoRotate))throw Error('autorotate failed');await page.locator('#auto').uncheck();
 const dl=page.waitForEvent('download');await page.locator('#download').click();result.glbDownload=(await dl).suggestedFilename();
 const cap=page.waitForEvent('download');await page.locator('#capture').click();result.capture=(await cap).suggestedFilename();
 await page.setViewportSize({width:390,height:844});await page.locator('[data-view="overview"]').click();await page.waitForTimeout(250);await page.screenshot({path:path.join(__dirname,'mobile.png'),fullPage:true});
 result.mobile=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,canvasWidth:document.querySelector('canvas').getBoundingClientRect().width}));
 if(result.mobile.scrollWidth>390)throw Error('mobile overflow');
 await page.goto('file://'+path.resolve(__dirname,'../田园与温室-离线预览.html'));await page.waitForFunction(()=>window.gardenViewer?.current);result.fileOfflineLoaded=true;
 await page.setViewportSize({width:1440,height:1000});await page.goto(base+'residential-3d-v1/住宅模型-离线预览.html?building=hero');await page.waitForFunction(()=>window.housingViewer?.current&&housingViewer.key==='hero');
 result.heroMeshCount=await page.evaluate(()=>{let n=0;housingViewer.current.traverse(o=>{if(o.isMesh)n++});return n;});await page.screenshot({path:path.join(__dirname,'hero-garden.png')});
 await browser.close();if(errors.length)throw Error(errors.join('\n'));fs.writeFileSync(path.join(__dirname,'browser-checks.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
})().catch(e=>{console.error(e);process.exit(1)});
