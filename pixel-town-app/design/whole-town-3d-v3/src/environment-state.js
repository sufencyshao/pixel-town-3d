export const WEATHER = Object.freeze({
  sunny: {name:'晴天',cloud:.12,dark:.02,rain:0,wind:.7,fog:.00006,wet:0},
  cloudy: {name:'多云',cloud:.55,dark:.18,rain:0,wind:1.1,fog:.00013,wet:0},
  overcast: {name:'阴天',cloud:.96,dark:.66,rain:0,wind:.8,fog:.00032,wet:0},
  lightRain: {name:'小雨',cloud:.95,dark:.58,rain:.18,wind:1.1,fog:.00040,wet:.35},
  rain: {name:'中雨',cloud:1,dark:.72,rain:.48,wind:1.8,fog:.00057,wet:.68},
  heavyRain: {name:'大雨',cloud:1,dark:.87,rain:.85,wind:2.5,fog:.00075,wet:1},
  storm: {name:'雷暴',cloud:1,dark:.97,rain:1,wind:3.6,fog:.00083,wet:1}
});
export const clamp=(x,a=0,b=1)=>Math.min(b,Math.max(a,x));
export const smooth=(a,b,x)=>{const t=clamp((x-a)/(b-a));return t*t*(3-2*t);};
export function solar(hour){
  const elevation=Math.sin((hour-6)/24*Math.PI*2);
  const daylight=smooth(-.12,.22,elevation);
  return {elevation,daylight,night:1-smooth(-.10,.08,elevation),dusk:1-smooth(0,.40,Math.abs(elevation))};
}
export class EnvironmentState {
  constructor(){this.elapsed=8*3600;this.rate=60;this.paused=false;this.weather='sunny';this.autoWeather=false;this.visual={...WEATHER.sunny};this.wetness=0;this.lastWeatherSlot=0;this.events=[];}
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
      const sequence=['sunny','cloudy','overcast','lightRain','rain','heavyRain','storm','cloudy'];
      this.setWeather(sequence[slot%sequence.length],false);
    }
    this.lastWeatherSlot=slot;
    const target=WEATHER[this.weather],a=1-Math.exp(-dt/1.4);
    for(const key of ['cloud','dark','rain','wind','fog'])this.visual[key]+=(target[key]-this.visual[key])*a;
    // Paving dries more slowly than it becomes wet. Animation continues when only game time pauses.
    this.wetness+=(target.wet-this.wetness)*(1-Math.exp(-dt/(target.wet>this.wetness?5:22)));
    return this.elapsed!==before;
  }
  snapshot(){return {day:this.day,hour:this.hour,clock:this.clock,rate:this.rate,paused:this.paused,weather:this.weather,autoWeather:this.autoWeather,visual:{...this.visual},wetness:this.wetness,...solar(this.hour)};}
}
