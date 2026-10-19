(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory(require('./appearance'),require('./parametric-avatar'),require('./preset-avatar'));
  else root.PixelAvatar=factory(root.Appearance,root.ParametricAvatar,root.PresetAvatar);
})(typeof globalThis!=='undefined'?globalThis:this,function(Appearance,ParametricAvatar,PresetAvatar){
  'use strict';
  function renderPixels(input,frame=1){
    const a=Appearance.normalize(input);
    return a.styleMode==='preset'?PresetAvatar.renderPixels(a,frame):ParametricAvatar.renderPixels(a,frame);
  }
  function getFaceRegion(input){return Appearance.normalize(input).styleMode==='preset'?PresetAvatar.faceRegion:ParametricAvatar.faceRegion;}
  return {renderPixels,getFaceRegion,width:ParametricAvatar.width,height:ParametricAvatar.height,faceRegion:ParametricAvatar.faceRegion};
});
