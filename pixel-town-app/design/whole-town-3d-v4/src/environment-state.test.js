import {test} from 'node:test';
import assert from 'node:assert/strict';
import {EnvironmentState,WEATHER,solar} from './environment-state.js';
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
 assert.equal(s.weather,'lightRain');s.setWeather('sunny');assert.equal(s.autoWeather,false);
 s.advance(600);assert.equal(s.weather,'sunny');
});
test('invalid input cannot poison state',()=>{
 const s=new EnvironmentState();s.setHour(NaN);assert.equal(s.hour,8);
 assert.throws(()=>s.advance(-1));assert.throws(()=>s.setWeather('unknown-weather'));
});
test('fresh light medium and heavy snow accumulate toward distinct depths',()=>{
 const depths=[];for(const key of ['lightSnow','snow','heavySnow']){const s=new EnvironmentState();s.paused=true;s.setWeather(key);s.advance(180);depths.push(s.snowDepth);assert.ok(Math.abs(s.snowDepth-WEATHER[key].snowCap)<.0001);assert.equal(s.riverRise,0);assert.equal(s.visual.rain,0);}
 assert.ok(depths[0]<depths[1]&&depths[1]<depths[2]);
});
test('lighter snow preserves previous heavy snow and sunshine melts gradually',()=>{
 const s=new EnvironmentState();s.setWeather('heavySnow');s.advance(180);const depth=s.snowDepth;s.setWeather('lightSnow');s.advance(20);assert.equal(s.snowDepth,depth);s.setWeather('sunny');s.advance(10);assert.ok(s.snowDepth>0&&s.snowDepth<depth);s.advance(900);assert.ok(s.snowDepth<.0001);
});
test('river rise scales with rainfall and typhoon remains below bank level',()=>{
 const levels=[];for(const key of ['lightRain','rain','heavyRain','storm','typhoon']){const s=new EnvironmentState();s.setWeather(key);s.advance(180);levels.push(s.riverRise);assert.ok(s.riverRise<=.68);assert.ok(Math.abs(s.riverRise-WEATHER[key].river)<.0001);}
 assert.ok(levels.every((x,i)=>!i||x>levels[i-1]));
});
test('river recedes gradually after rain and clock jumps do not alter surface water',()=>{
 const s=new EnvironmentState();s.setWeather('typhoon');s.advance(90);const level=s.riverRise;s.setHour(12);assert.equal(s.riverRise,level);s.setWeather('sunny');s.advance(10);assert.ok(s.riverRise>0&&s.riverRise<level);s.advance(800);assert.ok(s.riverRise<1e-8);
});
test('surface reset and settled preview keep weather and clock intact',()=>{
 const s=new EnvironmentState();s.setWeather('heavySnow');s.previewSettled();assert.equal(s.snowDepth,.30);const time=s.elapsed;s.resetSurface();assert.equal(s.snowDepth,0);assert.equal(s.riverRise,0);assert.equal(s.elapsed,time);assert.equal(s.weather,'heavySnow');s.setWeather('typhoon');s.previewSettled();assert.equal(s.riverRise,.68);assert.equal(s.visual.wind,12);
});
test('surface accumulation is independent of rendering frame rate',()=>{
 for(const key of ['heavySnow','typhoon']){const a=new EnvironmentState(),b=new EnvironmentState();a.setWeather(key);b.setWeather(key);a.advance(20);for(let i=0;i<1200;i++)b.advance(1/60);assert.ok(Math.abs(a.snowDepth-b.snowDepth)<1e-10);assert.ok(Math.abs(a.riverRise-b.riverRise)<1e-10);}
});
test('extreme wind and tornado have distinct combinations and clear on switch',()=>{
 assert.equal(WEATHER.windy.rain,0);assert.ok(WEATHER.typhoon.wind>WEATHER.windy.wind);assert.equal(WEATHER.typhoon.rain,1);const s=new EnvironmentState();s.setWeather('tornado');s.advance(20);assert.ok(s.visual.tornado>.99);s.setWeather('sunny');s.advance(20);assert.ok(s.visual.tornado<.00001);assert.ok(s.visual.wind<.71);
});
