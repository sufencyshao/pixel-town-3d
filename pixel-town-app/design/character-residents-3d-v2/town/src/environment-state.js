const weather=(name,params)=>({name,cloud:.12,dark:.02,rain:0,snow:0,snowCap:0,river:0,wind:.7,fog:.00006,wet:0,tornado:0,...params});
export const WEATHER = Object.freeze({
 sunny:weather('晴天',{}),
 cloudy:weather('多云',{cloud:.55,dark:.18,wind:1.1,fog:.00013}),
 overcast:weather('阴天',{cloud:.96,dark:.66,wind:.8,fog:.00032}),
 lightRain:weather('小雨',{cloud:.95,dark:.58,rain:.18,river:.12,wind:1.1,fog:.00040,wet:.35}),
 rain:weather('中雨',{cloud:1,dark:.72,rain:.48,river:.30,wind:1.8,fog:.00057,wet:.68}),
 heavyRain:weather('大雨',{cloud:1,dark:.87,rain:.85,river:.50,wind:2.5,fog:.00075,wet:1}),
 storm:weather('雷暴',{cloud:1,dark:.97,rain:1,river:.60,wind:3.6,fog:.00083,wet:1}),
 lightSnow:weather('小雪',{cloud:.82,dark:.26,snow:.22,snowCap:.03,wind:.9,fog:.00038}),
 snow:weather('中雪',{cloud:.96,dark:.40,snow:.55,snowCap:.12,wind:1.8,fog:.00058}),
 heavySnow:weather('大雪',{cloud:1,dark:.55,snow:1,snowCap:.30,wind:3.4,fog:.00095}),
 windy:weather('大风',{cloud:.56,dark:.26,wind:7.5,fog:.00024}),
 typhoon:weather('台风',{cloud:1,dark:1,rain:1,river:.68,wind:12,fog:.0014,wet:1}),
 tornado:weather('龙卷风',{cloud:1,dark:.90,rain:.18,river:.12,wind:9,fog:.00065,wet:.3,tornado:1})
});
// Stylized northern-hemisphere climate. Weights are game design values, not forecasts.
export const SEASON_DAYS=12;
export const SEASONS=Object.freeze({
 spring:{name:'春季',declination:0,leaf:'#9bbf69',leafLight:'#c3d68b',grass:'#9cb580',flower:1,foliage:.94,note:'嫩叶与春花 · 晴雨相间，偶有雷暴',weights:{sunny:26,cloudy:26,overcast:14,lightRain:18,rain:10,heavyRain:2,storm:1,windy:3}},
 summer:{name:'夏季',declination:23.44,leaf:'#4c8051',leafLight:'#76a35b',grass:'#7c9b63',flower:.82,foliage:1,note:'浓绿盛夏 · 白昼最长，强风雨事件较多',weights:{sunny:18,cloudy:15,overcast:6,lightRain:7,rain:10,heavyRain:15,storm:12,windy:10,typhoon:6,tornado:1}},
 autumn:{name:'秋季',declination:0,leaf:'#bc7043',leafLight:'#e0b257',grass:'#b3a078',flower:.38,foliage:.82,note:'金黄与橙红 · 起风时落叶飘舞，偶有秋雨台风',weights:{sunny:34,cloudy:28,overcast:12,lightRain:10,rain:6,heavyRain:2,storm:1,windy:6,typhoon:1}},
 winter:{name:'冬季',declination:-23.44,leaf:'#93816b',leafLight:'#ad9d82',grass:'#b7af96',flower:0,foliage:.10,note:'落叶疏枝与枯草 · 白昼最短，可下雪，无雷暴',weights:{sunny:26,cloudy:19,overcast:14,lightRain:3,rain:1,heavyRain:1,windy:4,lightSnow:16,snow:11,heavySnow:5}}
});
export const SEASON_KEYS=Object.keys(SEASONS);
export const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
export const smooth=(a,b,x)=>{const t=clamp((x-a)/(b-a));return t*t*(3-2*t);};
export function weatherAllowed(key,season){
 if(!WEATHER[key]||!SEASONS[season])return false;
 if(WEATHER[key].snow>0)return season==='winter';
 if(['storm','typhoon','tornado'].includes(key)&&season==='winter')return false;
 if(key==='typhoon')return ['summer','autumn'].includes(season);
 return true;
}
export function chooseWeather(season,slot){
 const entries=Object.entries(SEASONS[season].weights),total=entries.reduce((v,[,w])=>v+w,0);
 // Stable hash makes the same game interval reproducible without API or random network input.
 let seed=(slot+1)^Math.imul(SEASON_KEYS.indexOf(season)+1,0x9e3779b9);
 seed=Math.imul(seed^(seed>>>16),0x21f0aaad);seed=Math.imul(seed^(seed>>>15),0x735a2d97);seed^=seed>>>15;
 let pick=(seed>>>0)/4294967296*total;
 for(const [key,weight] of entries){pick-=weight;if(pick<0)return key;}
 return entries.at(-1)[0];
}
export function solar(hour,season='spring'){
 const rad=Math.PI/180,latitude=32*rad,declination=(SEASONS[season]||SEASONS.spring).declination*rad;
 const h=(hour-12)/24*Math.PI*2;
 const east=-Math.cos(declination)*Math.sin(h),north=Math.cos(latitude)*Math.sin(declination)-Math.sin(latitude)*Math.cos(declination)*Math.cos(h);
 const elevation=Math.sin(latitude)*Math.sin(declination)+Math.cos(latitude)*Math.cos(declination)*Math.cos(h);
 const sunsetAngle=Math.acos(clamp(-Math.tan(latitude)*Math.tan(declination),-1,1));
 const dayLength=sunsetAngle/Math.PI*24;
 return {elevation,altitude:Math.asin(clamp(elevation,-1,1))/rad,sunDirection:[east,elevation,-north],dayLength,sunrise:12-dayLength/2,sunset:12+dayLength/2,
 daylight:smooth(-.12,.22,elevation),night:1-smooth(-.10,.08,elevation),dusk:1-smooth(0,.40,Math.abs(elevation))};
}
export class EnvironmentState {
 constructor(){this.elapsed=8*3600;this.rate=60;this.paused=false;this.weather='sunny';this.autoWeather=false;this.visual={...WEATHER.sunny};this.wetness=0;this.snowDepth=0;this.riverRise=0;this.lastWeatherSlot=0;this.events=[];this.seasonAnchorDay=1;this.seasonAnchor=0;this.autoSeasons=true;this.activeSeason='spring';}
 get hour(){return (this.elapsed%86400)/3600;}
 get day(){return Math.floor(this.elapsed/86400)+1;}
 get season(){return SEASON_KEYS[(this.seasonAnchor+(this.autoSeasons?Math.floor((this.day-this.seasonAnchorDay)/SEASON_DAYS):0))%4];}
 get seasonDay(){return this.autoSeasons?(this.day-this.seasonAnchorDay)%SEASON_DAYS+1:1;}
 get clock(){const mins=Math.floor(this.elapsed/60)%1440;return `${String(Math.floor(mins/60)).padStart(2,'0')}:${String(mins%60).padStart(2,'0')}`;}
 setHour(hour){if(!Number.isFinite(hour))return;this.elapsed=Math.floor(this.elapsed/86400)*86400+clamp(hour,0,23.999)*3600;this.lastWeatherSlot=Math.floor(this.elapsed/10800);}
 setSeason(key){if(!SEASONS[key])throw new Error('Unknown season '+key);this.seasonAnchor=SEASON_KEYS.indexOf(key);this.seasonAnchorDay=this.day;this.syncSeason();}
 setAutoSeasons(value){const key=this.season;this.autoSeasons=!!value;this.seasonAnchor=SEASON_KEYS.indexOf(key);this.seasonAnchorDay=this.day;}
 syncSeason(){
  if(this.activeSeason===this.season)return;
  this.activeSeason=this.season;
  if(!weatherAllowed(this.weather,this.season))this.setWeather(this.autoWeather?chooseWeather(this.season,Math.floor(this.elapsed/10800)):'cloudy',false);
  // No lingering forbidden precipitation, tornado or lightning after crossing a seasonal boundary.
  if(this.season!=='winter')this.visual.snow=0;
  if(this.season==='winter')this.visual.tornado=0;
 }
 setWeather(key,manual=true){if(!WEATHER[key])throw new Error('Unknown weather '+key);if(!weatherAllowed(key,this.season))return false;this.weather=key;if(manual)this.autoWeather=false;return true;}
 advance(dt){
  if(!Number.isFinite(dt)||dt<0)throw new Error('Invalid delta time');
  const before=this.elapsed;
  if(!this.paused)this.elapsed+=dt*this.rate;
  this.syncSeason();
  const slot=Math.floor(this.elapsed/10800);
  if(this.autoWeather&&slot!==this.lastWeatherSlot)this.setWeather(chooseWeather(this.season,slot),false);
  this.lastWeatherSlot=slot;
  const target=WEATHER[this.weather],a=1-Math.exp(-dt/1.4);
  for(const key of ['cloud','dark','rain','snow','wind','fog','tornado'])this.visual[key]+=(target[key]-this.visual[key])*a;
  this.wetness+=(target.wet-this.wetness)*(1-Math.exp(-dt/(target.wet>this.wetness?5:22)));
  if(target.snow>0)this.snowDepth+=Math.max(0,target.snowCap-this.snowDepth)*(1-Math.exp(-dt/18));
  else this.snowDepth*=Math.exp(-dt/(this.season==='summer'?18:target.rain>0?25:this.season==='spring'?45:90));
  this.riverRise+=(target.river-this.riverRise)*(1-Math.exp(-dt/(target.river>this.riverRise?14:42)));
  return this.elapsed!==before;
 }
 resetSurface(){this.snowDepth=0;this.riverRise=0;this.wetness=0;}
 previewSettled(){const w=WEATHER[this.weather];this.snowDepth=w.snowCap;this.riverRise=w.river;this.wetness=w.wet;for(const k of ['cloud','dark','rain','snow','wind','fog','tornado'])this.visual[k]=w[k];}
 snapshot(){return {day:this.day,hour:this.hour,clock:this.clock,rate:this.rate,paused:this.paused,weather:this.weather,autoWeather:this.autoWeather,season:this.season,seasonDay:this.seasonDay,seasonDays:SEASON_DAYS,autoSeasons:this.autoSeasons,visual:{...this.visual},wetness:this.wetness,snowDepth:this.snowDepth,riverRise:this.riverRise,...solar(this.hour,this.season)};}
}
