const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const path=require('path'),fs=require('fs');
const root=path.resolve(__dirname,'..');
(async()=>{const browser=await chromium.launch({channel:'chrome',headless:true});try{
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 await page.goto(process.env.PREVIEW_URL||'http://127.0.0.1:49329/阿澈-C方向-离线预览.html');await page.waitForFunction(()=>avatarStudio.ready);
 await page.click('[data-action="Wave"]');
 const output=path.join(root,'qa','wave-'+(process.env.CAPTURE_LABEL||'after'));fs.mkdirSync(output,{recursive:true});
 for(const [name,camera] of [['front',[0,1.4,2.3]],['side',[2.5,1.4,0]],['back',[0,1.4,-2.3]]]){
  await page.evaluate(c=>{avatarStudio.camera.position.set(...c);avatarStudio.controls.target.set(.25,1.22,0);avatarStudio.controls.update();avatarStudio.seconds=1},camera);
  for(const phase of [125,375]){
   await page.locator('#timeline').evaluate((el,value)=>{el.value=String(value);el.dispatchEvent(new Event('input',{bubbles:true}))},phase);await page.waitForTimeout(80);
   await page.locator('#stage').screenshot({path:path.join(output,name+'-'+phase+'.png')});
  }
 }
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
