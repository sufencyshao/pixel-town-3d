'use strict';
const fs=require('fs'),path=require('path'),os=require('os'),crypto=require('crypto');
function platformAppData({platform=process.platform,env=process.env,home=os.homedir()}={}){
  if(platform==='win32')return env.APPDATA||path.join(home,'AppData','Roaming');
  if(platform==='darwin')return path.join(home,'Library','Application Support');
  return env.XDG_CONFIG_HOME||path.join(home,'.config');
}
function prepare3DData({support=platformAppData(),env=process.env,pid=process.pid}={}){
  if(env.PIXEL_TOWN_DATA_DIR)return env.PIXEL_TOWN_DATA_DIR;
  const dir=path.join(support,'pixel-town-life-3d-v9'),source=path.join(support,'pixel-town-life','town.json'),target=path.join(dir,'town.json');
  fs.mkdirSync(dir,{recursive:true,mode:0o700});
  if(!fs.existsSync(target)&&fs.existsSync(source)){
    const tmp=target+'.seed-'+pid,journalTemp=path.join(dir,'.journal-seed-'+pid);
    try{
      fs.copyFileSync(source,tmp,fs.constants.COPYFILE_EXCL);fs.chmodSync(tmp,0o600);
      const sourceHash=crypto.createHash('sha256').update(fs.readFileSync(tmp)).digest('hex');
      const journals=path.join(path.dirname(source),'journals'),destination=path.join(dir,'journals');
      if(fs.existsSync(journals)&&!fs.existsSync(destination)){fs.cpSync(journals,journalTemp,{recursive:true,errorOnExist:true,force:false});fs.renameSync(journalTemp,destination);}
      fs.writeFileSync(path.join(dir,'source.json'),JSON.stringify({source,sha256:sourceHash,copiedAt:new Date().toISOString(),platform:process.platform,mode:'one-time independent 3D workspace'},null,2),{mode:0o600});
      fs.renameSync(tmp,target);
    }finally{if(fs.existsSync(tmp))fs.unlinkSync(tmp);if(fs.existsSync(journalTemp))fs.rmSync(journalTemp,{recursive:true,force:true});}
  }
  env.PIXEL_TOWN_DATA_DIR=dir;return dir;
}
module.exports={platformAppData,prepare3DData};
