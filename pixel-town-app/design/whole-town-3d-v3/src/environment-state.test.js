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
 assert.equal(Object.keys(WEATHER).length,7);
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
 assert.throws(()=>s.advance(-1));assert.throws(()=>s.setWeather('snow'));
});
