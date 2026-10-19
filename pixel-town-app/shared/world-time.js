(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory();
  else root.WorldTime=factory();
})(typeof globalThis==='object'?globalThis:this,function(){
  'use strict';
  const sunrise=360,sunset=1080,dayLength=1440;
  // Cyclic lighting keyframes, all measured in game minutes.
  const colors=[
    [0,'#14223f','#344251','#263b40',1],
    [300,'#182746','#4a4d67','#2c4048',1],
    [330,'#7a779b','#d8a0a1','#8a888b',.75],
    [360,'#d6b2b7','#ffe0a5','#ebddc8',.35],
    [420,'#d5e9f1','#f9efd6','#f9faf1',0],
    [720,'#dceef4','#f6f4df','#fbfcf5',0],
    [1020,'#c6d5e5','#f4d2a2','#f5ebd8',.08],
    [1080,'#847da7','#f0b38c','#c4b4aa',.4],
    [1140,'#243452','#65637a','#34474a',.95],
    [1260,'#14223f','#344251','#263b40',1],
    [1440,'#14223f','#344251','#263b40',1]
  ];
  const rgb=hex=>[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));
  const mix=(a,b,t)=>'rgb('+rgb(a).map((n,i)=>Math.round(n+(rgb(b)[i]-n)*t)).join(',')+')';
  function minuteOfDay(clock){
    if(typeof clock!=='number'||!Number.isFinite(clock))throw new TypeError('小镇时间无效');
    return ((clock%dayLength)+dayLength)%dayLength;
  }
  function format(clock){const minute=minuteOfDay(clock);return String(Math.floor(minute/60)).padStart(2,'0')+':'+String(Math.floor(minute%60)).padStart(2,'0');}
  function sample(clock){
    const minute=minuteOfDay(clock);
    const end=colors.findIndex(k=>k[0]>minute),a=colors[end-1],b=colors[end],t=(minute-a[0])/(b[0]-a[0]);
    const night=a[4]+(b[4]-a[4])*t;
    const phase=minute>=330&&minute<420?'dawn':minute>=420&&minute<1020?'day':minute>=1020&&minute<1140?'dusk':'night';
    const labels={dawn:'日出',day:'白昼',dusk:'日落',night:'夜晚'};
    const sunProgress=Math.max(0,Math.min(1,(minute-sunrise)/(sunset-sunrise)));
    const moonProgress=((minute-sunset+dayLength)%dayLength)/(dayLength-(sunset-sunrise));
    const body=(visible,progress)=>({visible,progress,x:8+84*progress,y:184-132*Math.sin(Math.PI*progress)});
    return {day:Math.max(1,Math.floor(clock/dayLength)+1),minute,time:format(clock),phase,label:labels[phase],night,
      sky:mix(a[1],b[1],t),horizon:mix(a[2],b[2],t),ground:mix(a[3],b[3],t),
      ink:mix('#8c9a84','#c2d1cf',night),grid:mix('#e4ebdc','#40595f',night),
      spriteBrightness:1-night*.22,spriteWarmth:Math.max(0,1-Math.abs(minute-360)/90,1-Math.abs(minute-1080)/90)*.12,
      sun:body(minute>=sunrise&&minute<sunset,sunProgress),moon:body(minute>=sunset||minute<sunrise,moonProgress)};
  }
  function next(clock,minute){
    minuteOfDay(clock);
    if(!Number.isInteger(minute)||minute<0||minute>=dayLength)throw new TypeError('请选择有效时刻');
    const target=Math.floor(clock/dayLength)*dayLength+minute;
    return target>clock?target:target+dayLength;
  }
  return {sample,format,minuteOfDay,next,sunrise,sunset,dayLength};
});
