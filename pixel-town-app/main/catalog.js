'use strict';
// 01..20 的 11/12 已签收为背走；欢呼使用 animation.json 中独立图集。
const specs = [
  ['01_hero_male','阿澈','自由职业者','开朗、好奇、乐于助人','骑车、探索新地方','爽朗，喜欢主动提问'],
  ['02_hero_female','小满','小镇居民','温柔、好奇、有主见','散步、收集小花','轻快，善于关心别人的细节'],
  ['03_barista_male','林屿','咖啡师','健谈、随和、偶尔偷懒','手冲咖啡、听故事','幽默，常用咖啡作比喻'],
  ['04_baker_male','麦麦','面包师','热心、乐天、踏实','烘焙、分享新配方','直白亲切，爱邀请别人试吃'],
  ['05_carpenter_male','大森','木匠','木讷、可靠、耐心','木工、修理旧物','话少，喜欢给出实际帮助'],
  ['06_postman_male','小路','邮差','活泼、守时、爱八卦','跑步、认识新朋友','语速轻快，爱分享沿途见闻'],
  ['07_police_male','程正','社区警察','认真、克制、外冷内热','晨跑、照顾邻里','简洁严肃，关心藏在提醒里'],
  ['08_doctor_male','许衡','医生','冷静、细致、理性','阅读、下棋','温和准确，不随便下结论'],
  ['09_gardener_male','阿禾','园丁','乐观、朴实、喜欢自然','种花、晒太阳','慢悠悠，常聊季节与植物'],
  ['10_musician_male','迟野','乐手','慢热、独立、敏感','吉他、独处','短句，有时用音乐表达感受'],
  ['11_chef_male','陈锅','厨师','自信、豪爽、爱张罗','做饭、研究调味','热闹，喜欢招呼大家吃饭'],
  ['12_florist_female','花音','花店店主','浪漫、体贴、善解人意','插花、观察小镇','柔和细腻，记得别人的喜好'],
  ['13_pastrychef_female','糖糖','糕点师','可爱、认真、爱分享','甜品、拍照','活泼，谈到配方会格外认真'],
  ['14_teacher_female','温书','小学老师','耐心、温柔、有原则','读书、手工','善于倾听，清楚地表达界限'],
  ['15_nurse_female','苏晴','护士','热情、细心、责任感强','散步、照顾朋友','亲切，习惯询问对方状态'],
  ['16_librarian_female','知秋','图书管理员','慢热、严谨、安静','文学、整理书架','克制，熟悉以后会聊很多'],
  ['17_cafeowner_female','沈知','咖啡馆店长','干练、直率、关心伙伴','咖啡、经营小店','利落，偶尔调侃熟人'],
  ['18_artist_female','鹿眠','画家','慵懒、敏感、富有想象力','画画、看云','随性，用细小观察开启话题'],
  ['19_vet_female','安安','兽医助理','腼腆、温柔、喜爱动物','小动物、记录日常','柔软，熟悉后才会主动讲话'],
  ['20_student_female','夏芽','大学生','元气、爱玩、容易分心','游戏、运动、新鲜事','活力十足，经常提议一起玩']
];
const legacyCatalog = specs.map(([asset,name,occupation,personality,likes,speakingStyle], i) => ({ asset,name,occupation, gender: i < 11 && i !== 1 ? '男' : '女', persona: { personality, likes, speakingStyle, background: `搬来小镇生活的${occupation}，希望慢慢认识邻居。` } }));
const { loadRoster, normalizePersona } = require('./assets');
const Life = require('../shared/life');
const Emotions = require('../shared/emotions');
const roster = loadRoster();
const catalog = roster.characters.length ? roster.characters.map((p, i) => ({
  ...p, asset: p.assetFolder.split('/').pop(), occupation: p.role || '小镇居民',
  gender: p.sex === 'male' || p.sex === '男' ? '男' : p.sex === 'female' || p.sex === '女' ? '女' : '未指定', persona: normalizePersona(p.persona),
  catalogId: p.id, kind: p.kind
})) : legacyCatalog.map(p => ({ ...p, kind: 'human', assetFolder: 'characters/' + p.asset, presets: [] }));
const petCatalog = roster.pets.map(p => ({ ...p, asset: p.assetFolder.split('/').pop(),
  catalogId: p.id, occupation: p.animal?.species || '动物', persona: normalizePersona(p.persona),
  gender: p.sex === 'male' ? '雄' : p.sex === 'female' ? '雌' : '未设定' }));
const ACTIONS = require('../shared/actions').labels;
const ZONES = { work:{x:350,y:290}, rest:{x:1240,y:710}, play:{x:1230,y:290}, chat:{x:790,y:510} };
function createResident(index, enabled = false) {
  const item = catalog[index % catalog.length];
  const clone = Math.floor(index / catalog.length);
  return { ...structuredClone(item), id:`resident-${index+1}`, name:item.name+(clone ? ` ${clone+1}` : ''), enabled, model:{providerId:'demo',model:'demo',temperature:0.8,maxTokens:300}, profileMd:item.profileMd||'', memory:[], relationships:{}, messages:[], mood:'calm', energy:80, social:65, happiness:75, x:420+(index%5)*190, y:350+Math.floor(index/5)*130%400, action:'idle', remaining:2+index%7, target:null, bubble:'', bubbleUntil:0, thought:'', thoughtUntil:0, behaviorSource:'local', behaviorStatus:'acting', intentVersion:0, decisionAt:0, thinking:false };
}
function createPet(index, enabled = false) {
  const p = petCatalog[index];
  if (!p) throw new Error('动物形象不存在');
  return { ...createResident(index, enabled), ...structuredClone(p), id: 'pet-' + p.catalogId,
    enabled, x: 300 + index % 8 * 140, y: 500 + Math.floor(index / 8) * 110,
    action: 'idle', needs: { hunger: 25, thirst: 20, safety: 85, stimulation: 50 },
    observation: { senses: [], need: 'rest' }, messages: [], relationships: {} };
}
function migrateState(state) {
  state.pets ||= [];
  state.worldInfo=Life.world(state.worldInfo);
  for (const r of state.residents) {
    const p = catalog.find(c => c.asset === r.asset);
    if (p) for (const key of ['kind', 'catalogId', 'assetFolder', 'presets', 'animation', 'sprite']) r[key] = structuredClone(p[key]);
    r.kind = p?.kind || 'human';
    r.thought ||= '';r.thoughtUntil ||= 0;r.behaviorSource ||= 'local';r.behaviorStatus ||= 'acting';r.intentVersion ||= 0;
    if(!r.profileMd&&p?.profileMd)r.profileMd=p.profileMd;
    if(!Array.isArray(r.schedule)&&Array.isArray(p?.schedule))r.schedule=structuredClone(p.schedule);
    r.life=Life.profile(r.life,r);
    r.emotion=Emotions.normalize(r,state.clock);r.mood=Emotions.mood(r.happiness);
  }
  for (let i = 0; i < catalog.length; i++) if (!state.residents.some(r => r.asset === catalog[i].asset)) {
    const r = createResident(i);
    let id = 'resident-' + (i + 1), suffix = 1;
    while (state.residents.some(x => x.id === id)) id = 'resident-' + (i + 1) + '-new-' + suffix++;
    r.id = id;r.life=Life.profile(null,r); state.residents.push(r);
  }
  for (let i = 0; i < petCatalog.length; i++) {
    const p = petCatalog[i], old = state.pets.find(r => r.catalogId === p.catalogId);
    if (!old) state.pets.push(createPet(i));
    else for (const key of ['kind', 'animal', 'assetFolder', 'presets', 'animation', 'sprite']) old[key] = structuredClone(p[key]);
  }
  return state;
}
function initialState() {
  const residents = catalog.map((_,i)=>createResident(i,[1,2,8,15,17,19].includes(i)));
  return { version:1, clock:9*60, running:true, speed:1, autonomous:false, apiInterval:60, dailyLimit:100, grid:true, zones:true, residents, pets:petCatalog.map((_,i)=>createPet(i)), providers:[{id:'demo', name:'本地规则（无需 API）', type:'demo', models:['demo'], baseUrl:'',apiKey:''}], events:[], stats:[], lastApiAt:0 };
}
module.exports = { catalog, petCatalog, ACTIONS, ZONES, createResident, createPet, migrateState, initialState };
