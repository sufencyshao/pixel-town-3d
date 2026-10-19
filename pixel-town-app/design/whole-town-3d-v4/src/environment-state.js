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
export const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
export const smooth=(a,b,x)=>{const t=clamp((x-a)/(b-a));return t*t*(3-2*t);};
export function solar(hour){
  const elevation=Math.sin((hour-6)/24*Math.PI*2);
  const daylight=smooth(-.12,.22,elevation);
  return {elevation,daylight,night:1-smooth(-.10,.08,elevation),dusk:1-smooth(0,.40,Math.abs(elevation))};
}
export class EnvironmentState {
  constructor(){this.elapsed=8*3600;this.rate=60;this.paused=false;this.weather='sunny';this.autoWeather=false;this.visual={...WEATHER.sunny};this.wetness=0;this.snowDepth=0;this.riverRise=0;this.lastWeatherSlot=0;this.events=[];}
  get hour(){return (this.elapsed%86400)/3600;}
  get day(){return Math.floor(this.elapsed/86400)+1;}
  get clock(){const mins=Math.floor(this.elapsed/60)%1440;return `${String(Math.floor(mins/60)).padStart(2,'0')}:${String(mins%60).padStart(2,'0')}`;}
  setHour(hour){if(!Number.isFinite(hour))return;this.elapsed=Math.floor(this.elapsed/86400)*86400+clamp(hour,0,23.999)*3600;this.lastWeatherSlot=Math.floor(this.elapsed/10800);}
  setWeather(key,manual=true){if(!WEATHER[key])throw new Error('Unknown weather '+key);this.weather=key;if(manual)this.autoWeather=false;}
  advance(dt){
    if(!Number.isFinite(dt)||dt<0)throw new Error('Invalid delta time');
    const before=this.elapsed;
    if(!this.paused)this.elapsed+=dt*this.rate;
    const slot=Math.floor(this.elapsed/10800);
    if(this.autoWeather&&slot!==this.lastWeatherSlot){
      const sequence=['sunny','cloudy','overcast','lightRain','rain','heavyRain','storm','cloudy','lightSnow','snow','heavySnow','windy'];
      this.setWeather(sequence[slot%sequence.length],false);
    }
    this.lastWeatherSlot=slot;
    const target=WEATHER[this.weather],a=1-Math.exp(-dt/1.4);
    for(const key of ['cloud','dark','rain','snow','wind','fog','tornado'])this.visual[key]+=(target[key]-this.visual[key])*a;
    // Paving dries more slowly than it becomes wet. Animation continues when only game time pauses.
    this.wetness+=(target.wet-this.wetness)*(1-Math.exp(-dt/(target.wet>this.wetness?5:22)));
    // Accumulation uses preview seconds, like the precipitation, even while the clock is paused.
    // Lighter snowfall preserves earlier deep snow; use resetSurface() for a fresh comparison.
    if(target.snow>0)this.snowDepth+=Math.max(0,target.snowCap-this.snowDepth)*(1-Math.exp(-dt/18));
    else this.snowDepth*=Math.exp(-dt/(target.rain>0?25:90));
    this.riverRise+=(target.river-this.riverRise)*(1-Math.exp(-dt/(target.river>this.riverRise?14:42)));
    return this.elapsed!==before;
  }
  resetSurface(){this.snowDepth=0;this.riverRise=0;this.wetness=0;}
  previewSettled(){const w=WEATHER[this.weather];this.snowDepth=w.snowCap;this.riverRise=w.river;this.wetness=w.wet;for(const k of ['cloud','dark','rain','snow','wind','fog','tornado'])this.visual[k]=w[k];}
  snapshot(){return {day:this.day,hour:this.hour,clock:this.clock,rate:this.rate,paused:this.paused,weather:this.weather,autoWeather:this.autoWeather,visual:{...this.visual},wetness:this.wetness,snowDepth:this.snowDepth,riverRise:this.riverRise,...solar(this.hour)};}
}
