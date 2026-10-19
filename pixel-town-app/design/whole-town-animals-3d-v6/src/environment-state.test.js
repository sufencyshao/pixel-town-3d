import {test} from 'node:test';
import assert from 'node:assert/strict';
import {EnvironmentState,WEATHER,solar,SEASONS,chooseWeather,weatherAllowed} from './environment-state.js';
test('midnight rolls to the next day without losing simulated time',()=>{
 const s=new EnvironmentState();s.setHour(23.99);s.rate=60;s.advance(1);
 assert.equal(s.day,2);assert.ok(Math.abs(s.hour-(.99*3600+60-3600)/3600)<1e-8);
});
test('pausing stops the clock but allows weather transitions',()=>{
 const s=new EnvironmentState();s.paused=true;s.setWeather('heavyRain');s.advance(8);
 assert.equal(s.hour,8);assert.ok(s.visual.rain>.8);assert.ok(s.wetness>.7);
});
test('all speeds are frame-rate independent',()=>{
 for(const rate of [1,60,240,1440]){
  const a=new EnvironmentState(),b=new EnvironmentState();a.rate=b.rate=rate;
  a.advance(2);for(let i=0;i<120;i++)b.advance(1/60);
  assert.ok(Math.abs(a.elapsed-b.elapsed)<1e-6);
 }
});
test('night lights fade on and off around sunset and sunrise',()=>{
 assert.equal(solar(12).night,0);assert.equal(solar(0).night,1);
 assert.ok(solar(18).night>0&&solar(18).night<1);
 assert.ok(solar(18.5).night>solar(17.5).night);
 assert.ok(solar(5.5).night>solar(6.5).night);
});
test('rain levels are ordered and dry weather clears rain while ground dries gradually',()=>{
 assert.equal(Object.keys(WEATHER).length,13);
 assert.ok(WEATHER.lightRain.rain<WEATHER.rain.rain&&WEATHER.rain.rain<WEATHER.heavyRain.rain);
 const s=new EnvironmentState();s.setWeather('storm');s.advance(20);const wet=s.wetness;
 s.setWeather('sunny');s.advance(8);assert.ok(s.visual.rain<.01);assert.ok(s.wetness<wet&&s.wetness>.4);
 s.advance(150);assert.ok(s.wetness<.002);
});
test('automatic weather advances once per three simulated hours; manual selection takes over',()=>{
 const s=new EnvironmentState();s.autoWeather=true;s.setHour(8.99);s.advance(1);
 assert.equal(s.weather,chooseWeather('spring',3));s.setWeather('sunny');assert.equal(s.autoWeather,false);
 s.advance(600);assert.equal(s.weather,'sunny');
});
test('invalid input cannot poison state',()=>{
 const s=new EnvironmentState();s.setHour(NaN);assert.equal(s.hour,8);
 assert.throws(()=>s.advance(-1));assert.throws(()=>s.setWeather('unknown-weather'));
});
test('fresh light medium and heavy snow accumulate toward distinct depths',()=>{
 const depths=[];for(const key of ['lightSnow','snow','heavySnow']){const s=new EnvironmentState();s.paused=true;s.setSeason('winter');s.setWeather(key);s.advance(180);depths.push(s.snowDepth);assert.ok(Math.abs(s.snowDepth-WEATHER[key].snowCap)<.0001);assert.equal(s.riverRise,0);assert.equal(s.visual.rain,0);}
 assert.ok(depths[0]<depths[1]&&depths[1]<depths[2]);
});
test('lighter snow preserves previous heavy snow and sunshine melts gradually',()=>{
 const s=new EnvironmentState();s.setSeason('winter');s.setWeather('heavySnow');s.advance(180);const depth=s.snowDepth;s.setWeather('lightSnow');s.advance(20);assert.equal(s.snowDepth,depth);s.setWeather('sunny');s.advance(10);assert.ok(s.snowDepth>0&&s.snowDepth<depth);s.advance(900);assert.ok(s.snowDepth<.0001);
});
test('river rise scales with rainfall and typhoon remains below bank level',()=>{
 const levels=[];for(const key of ['lightRain','rain','heavyRain','storm','typhoon']){const s=new EnvironmentState();s.setSeason('summer');s.setWeather(key);s.advance(180);levels.push(s.riverRise);assert.ok(s.riverRise<=.68);assert.ok(Math.abs(s.riverRise-WEATHER[key].river)<.0001);}
 assert.ok(levels.every((x,i)=>!i||x>levels[i-1]));
});
test('river recedes gradually after rain and clock jumps do not alter surface water',()=>{
 const s=new EnvironmentState();s.setSeason('summer');s.setWeather('typhoon');s.advance(90);const level=s.riverRise;s.setHour(12);assert.equal(s.riverRise,level);s.setWeather('sunny');s.advance(10);assert.ok(s.riverRise>0&&s.riverRise<level);s.advance(800);assert.ok(s.riverRise<1e-8);
});
test('surface reset and settled preview keep weather and clock intact',()=>{
 const s=new EnvironmentState();s.setSeason('winter');s.setWeather('heavySnow');s.previewSettled();assert.equal(s.snowDepth,.30);const time=s.elapsed;s.resetSurface();assert.equal(s.snowDepth,0);assert.equal(s.riverRise,0);assert.equal(s.elapsed,time);assert.equal(s.weather,'heavySnow');s.setSeason('summer');s.setWeather('typhoon');s.previewSettled();assert.equal(s.riverRise,.68);assert.equal(s.visual.wind,12);
});
test('surface accumulation is independent of rendering frame rate',()=>{
 for(const key of ['heavySnow','typhoon']){const a=new EnvironmentState(),b=new EnvironmentState();a.setSeason(key==='heavySnow'?'winter':'summer');b.setSeason(key==='heavySnow'?'winter':'summer');a.setWeather(key);b.setWeather(key);a.advance(20);for(let i=0;i<1200;i++)b.advance(1/60);assert.ok(Math.abs(a.snowDepth-b.snowDepth)<1e-10);assert.ok(Math.abs(a.riverRise-b.riverRise)<1e-10);}
});
test('extreme wind and tornado have distinct combinations and clear on switch',()=>{
 assert.equal(WEATHER.windy.rain,0);assert.ok(WEATHER.typhoon.wind>WEATHER.windy.wind);assert.equal(WEATHER.typhoon.rain,1);const s=new EnvironmentState();s.setWeather('tornado');s.advance(20);assert.ok(s.visual.tornado>.99);s.setWeather('sunny');s.advance(20);assert.ok(s.visual.tornado<.00001);assert.ok(s.visual.wind<.71);
});

test('seasonal solar arc has longer summer days, shorter winter days and different noons',()=>{
 const spring=solar(12,'spring'),summer=solar(12,'summer'),winter=solar(12,'winter');
 assert.ok(summer.dayLength>spring.dayLength&&spring.dayLength>winter.dayLength);
 assert.ok(summer.sunrise<spring.sunrise&&summer.sunset>spring.sunset);
 assert.ok(summer.altitude>spring.altitude&&spring.altitude>winter.altitude);
 for(const key of Object.keys(SEASONS))for(const hour of [0,6,12,18,23.99]){const s=solar(hour,key);assert.ok(Math.abs(Math.hypot(...s.sunDirection)-1)<1e-10);}
 assert.ok(solar(5.5,'summer').altitude>0&&solar(5.5,'winter').altitude<0);
 assert.ok(solar(18.5,'summer').night<.5&&solar(18.5,'winter').night>.5);
});
test('nonwinter snow and winter thunderstorms cannot be selected by any state entry',()=>{
 for(const season of Object.keys(SEASONS))for(const key of Object.keys(WEATHER)){
  const s=new EnvironmentState();s.setSeason(season);const old=s.weather,result=s.setWeather(key);
  assert.equal(result,weatherAllowed(key,season));if(!result)assert.equal(s.weather,old);
  if(season!=='winter'&&WEATHER[key].snow)assert.equal(result,false);
  if(season==='winter'&&['storm','typhoon','tornado'].includes(key))assert.equal(result,false);
 }
});
test('changing season repairs incompatible weather and clears forbidden particles immediately',()=>{
 const s=new EnvironmentState();s.setSeason('winter');s.setWeather('heavySnow');s.previewSettled();s.setSeason('spring');
 assert.equal(s.weather,'cloudy');assert.equal(s.visual.snow,0);assert.equal(s.snowDepth,.3);s.advance(10);assert.ok(s.snowDepth<.3&&s.snowDepth>0);
 s.setSeason('summer');s.setWeather('storm');s.setSeason('winter');assert.equal(s.weather,'cloudy');
 s.setSeason('summer');s.setWeather('typhoon');s.autoWeather=true;s.setSeason('winter');assert.ok(weatherAllowed(s.weather,'winter'));assert.equal(s.autoWeather,true);
});
test('a twelve-day calendar crosses all four seasons, including winter snow to spring',()=>{
 const s=new EnvironmentState();s.rate=1;
 for(const season of ['summer','autumn','winter','spring']){s.advance(12*86400);assert.equal(s.season,season);assert.equal(s.seasonDay,1);}
 const w=new EnvironmentState();w.setSeason('winter');w.setWeather('heavySnow');w.previewSettled();w.rate=1;w.advance(12*86400);assert.equal(w.season,'spring');assert.equal(w.visual.snow,0);assert.ok(weatherAllowed(w.weather,'spring'));
});
test('manual season switching preserves day, time, speed, pause, surfaces and auto weather choice',()=>{
 const s=new EnvironmentState();s.elapsed=6*86400+10*3600;s.rate=240;s.paused=true;s.autoWeather=true;s.riverRise=.4;
 s.setSeason('autumn');assert.equal(s.day,7);assert.equal(s.hour,10);assert.equal(s.seasonDay,1);assert.equal(s.rate,240);assert.equal(s.paused,true);assert.equal(s.riverRise,.4);assert.equal(s.autoWeather,true);
 s.setAutoSeasons(false);s.paused=false;s.advance(30*86400/240);assert.equal(s.season,'autumn');
 s.setAutoSeasons(true);s.advance(12*86400/240);assert.equal(s.season,'winter');
});
test('pause blocks seasonal advancement and time-of-day scrubbing never changes the season',()=>{
 const s=new EnvironmentState();s.setSeason('summer');s.paused=true;s.advance(1e6);assert.equal(s.season,'summer');assert.equal(s.day,1);
 s.setHour(23.99);assert.equal(s.season,'summer');assert.equal(s.day,1);
});
test('seasonal weighted weather is reproducible, never forbidden and summer favors strong events',()=>{
 const counts={};for(const season of Object.keys(SEASONS)){
  counts[season]=0;const all=new Set();for(let slot=0;slot<10000;slot++){
   const key=chooseWeather(season,slot);assert.equal(key,chooseWeather(season,slot));assert.ok(weatherAllowed(key,season));all.add(key);
   if(['heavyRain','storm','typhoon','windy'].includes(key))counts[season]++;
  }
  for(const key of Object.keys(SEASONS[season].weights))assert.ok(all.has(key));
 }
 assert.ok(counts.summer>counts.spring*3&&counts.summer>counts.autumn*3&&counts.summer>counts.winter*3);
});
test('automatic weather includes summer typhoons and winter snowfall over complete season samples',()=>{
 for(const season of ['spring','summer','autumn','winter']){
  const s=new EnvironmentState();s.setSeason(season);s.setAutoSeasons(false);s.autoWeather=true;s.rate=1;const seen=new Set();
  for(let i=0;i<500;i++){s.advance(10800);assert.ok(weatherAllowed(s.weather,season));seen.add(s.weather);}
  if(season==='summer')assert.ok(seen.has('typhoon')&&seen.has('storm'));
  if(season==='winter')assert.ok(seen.has('snow')&&seen.has('heavySnow')&&!seen.has('storm'));
 }
});
test('invalid seasons cannot change the calendar',()=>{const s=new EnvironmentState();assert.throws(()=>s.setSeason('unknown'));assert.equal(s.season,'spring');});
