(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Appearance = factory();
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const select = (key, label, group, values) => ({ key, label, group, type: 'select', options: values.split('|').map(item => { const [value, title] = item.split(':'); return { value, label: title }; }) });
  const color = (key, label, group) => ({ key, label, group, type: 'color' });
  const originalColor = (key, label) => ({ ...color(key, label, 'preset'), allowOriginal: true });
  const range = (key, label, group, max) => ({ key, label, group, type: 'range', min: 0, max, step: 1 });
  const gamePresets = [
    ['01_hero_male','轻装男生','male'],['02_hero_female','田园女孩','female'],
    ['03_barista_male','咖啡少年','male'],['10_musician_male','街角乐手','male'],
    ['12_florist_female','花店日常','female'],['16_librarian_female','书香少女','female'],
    ['18_artist_female','彩绘女孩','female'],['20_student_female','校园日常','female']
  ].map(([id,label,gender])=>({id,label,gender,assetFolder:'characters/'+id}));
  const fields = [
    select('gender', '性别表达', 'identity', 'male:男生|female:女生|nonbinary:中性'), color('skin', '肤色', 'identity'),
    select('faceShape', '脸型', 'face', 'round:圆脸|oval:鹅蛋脸|square:方脸|soft:柔和脸'),
    select('hairStyle', '发型', 'hair', 'bob:波波头|pixie:精灵短发|short:短发|long:长发|ponytail:马尾|twintails:双马尾|bun:丸子头|curly:卷发|bald:光头'),
    select('bangs', '刘海', 'hair', 'straight:齐刘海|side:侧刘海|curtain:窗帘刘海|none:无刘海'), color('hairColor', '发色', 'hair'),
    select('brows', '眉形', 'face', 'soft:柔和眉|straight:平眉|arched:弯眉|thick:浓眉|none:无眉'), color('browColor', '眉色', 'face'),
    select('eyes', '眼型', 'face', 'round:圆眼|almond:杏眼|sleepy:困倦眼|smile:笑眼|sharp:锐利眼'), color('eyeColor', '瞳色', 'face'),
    select('nose', '鼻型', 'face', 'button:圆鼻|small:小鼻|pointed:尖鼻|flat:平鼻'),
    select('mouth', '嘴型', 'face', 'small:小嘴|wide:宽嘴|smile:微笑|pout:嘟嘴'),
    select('expression', '表情', 'face', 'neutral:平静|happy:开心|shy:害羞|serious:认真|surprised:惊讶|sad:难过'),
    range('blush', '腮红', 'face', 3), range('freckles', '雀斑', 'face', 3),
    range('height', '身高', 'body', 4), range('build', '体型', 'body', 4), range('shoulders', '肩宽', 'body', 4), range('chest', '胸部轮廓', 'body', 4),
    select('outfit', '上装', 'clothes', 'shirt:衬衫|hoodie:连帽衫|dress:连衣裙|overalls:背带装|suit:西装|sweater:毛衣|jacket:夹克'),
    color('clothesColor', '上装颜色', 'clothes'), color('accentColor', '衣服配色', 'clothes'),
    select('bottom', '下装', 'clothes', 'pants:长裤|shorts:短裤|skirt:裙子'), color('bottomColor', '下装颜色', 'clothes'),
    select('shoes', '鞋型', 'accessories', 'sneakers:运动鞋|boots:靴子|flats:平底鞋|sandals:凉鞋'), color('shoeColor', '鞋色', 'accessories'),
    select('hat', '帽子', 'accessories', 'none:无帽子|cap:棒球帽|beanie:针织帽|straw:草帽|beret:贝雷帽'), color('hatColor', '帽色', 'accessories'),
    select('accessory', '配饰', 'accessories', 'none:无配饰|glasses:方框眼镜|roundGlasses:圆框眼镜|ribbon:蝴蝶结|earrings:耳饰'), color('accessoryColor', '配饰颜色', 'accessories'),
    select('styleMode','形象方案','mode','preset:游戏预设形象|custom:自由捏脸'),
    select('avatarPreset','基础形象','preset',gamePresets.map(p=>p.id+':'+p.label).join('|')),
    originalColor('presetHairColor','发色'),originalColor('presetClothesColor','服装配色'),
    originalColor('presetSkinColor','肤色'),originalColor('presetEyeColor','瞳色'),
    select('presetAccessory','附加组件','preset','none:无附加组件|glasses:方框眼镜|roundGlasses:圆框眼镜|ribbon:蝴蝶结|scarf:围巾')
  ];
  const defaults = Object.freeze({ gender: 'nonbinary', skin: '#F5D5C1', faceShape: 'oval', hairStyle: 'bob', bangs: 'curtain', hairColor: '#5E4941', brows: 'soft', browColor: '#695049', eyes: 'almond', eyeColor: '#6D8A82', nose: 'small', mouth: 'smile', expression: 'neutral', blush: 1, freckles: 0, height: 3, build: 1, shoulders: 1, chest: 1, outfit: 'shirt', clothesColor: '#EAE2CD', accentColor: '#74948A', bottom: 'pants', bottomColor: '#6C817B', shoes: 'flats', shoeColor: '#705B4B', hat: 'none', hatColor: '#C79368', accessory: 'none', accessoryColor: '#D78591' });
  const currentDefaults = Object.freeze({...defaults,styleMode:'preset',avatarPreset:gamePresets[0].id,presetHairColor:'original',presetClothesColor:'original',presetSkinColor:'original',presetEyeColor:'original',presetAccessory:'none'});
  const byKey = new Map(fields.map(field => [field.key, field]));
  function normalize(input) {
    if (input === undefined) return { ...currentDefaults };
    if (!input || typeof input !== 'object' || Array.isArray(input) || ![Object.prototype, null].includes(Object.getPrototypeOf(input))) throw new TypeError('外观配置必须是普通对象');
    const result = { ...currentDefaults };
    // Existing saves have exactly the former 30 fields and keep their original renderer.
    if (!Object.hasOwn(input,'styleMode')) result.styleMode='custom';
    for (const key of Reflect.ownKeys(input)) {
      const field = byKey.get(key), value = input[key];
      if (!field) throw new TypeError('未知外观字段: ' + String(key));
      if (field.type === 'select' && !field.options.some(option => option.value === value)) throw new TypeError('无效外观选项: ' + key);
      if (field.type === 'color' && !(field.allowOriginal && value === 'original') && (typeof value !== 'string' || !/^#[0-9a-f]{6}$/i.test(value))) throw new TypeError('无效六位颜色: ' + key);
      if (field.type === 'range' && (!Number.isInteger(value) || value < field.min || value > field.max)) throw new TypeError('无效外观数值: ' + key);
      result[key] = field.type === 'color' && value !== 'original' ? value.toUpperCase() : value;
    }
    return result;
  }
  const palettes = { skin: ['#F8D7B5','#E8AE88','#CA8D65','#9C654E','#6D463A'], hairColor: ['#392E37','#734C37','#BC7D45','#E2BD75','#A66C94','#5D808C'], browColor: ['#46333B','#734C37','#9A713E'], eyeColor: ['#427D84','#53699C','#987346','#6D9864','#9E607D'], clothesColor: ['#739D87','#7E9CBE','#D38483','#C4A2CA','#D5AF68','#4B6279'], accentColor: ['#F3D59B','#F4E6CE','#BD655F','#A4C8BE'], bottomColor: ['#394C65','#70545F','#58726B','#AD8E76'], shoeColor: ['#FAEBD3','#4B4051','#A96661'], hatColor: ['#C79368','#4E7686','#B86270','#8F8DBB'], accessoryColor: ['#D78591','#F4C86F','#395D6B','#A8C8C0'] };
  const pick = values => values[Math.floor(Math.random() * values.length)];
  function randomize() {
    // Start from a designed wardrobe so random faces keep a coherent outfit and palette.
    const appearance = {...pick(presets).appearance};
    for(const key of ['gender','faceShape','hairStyle','bangs','eyes','nose','mouth'])appearance[key]=pick(byKey.get(key).options).value;
    appearance.skin=pick(palettes.skin);appearance.hairColor=pick(palettes.hairColor);appearance.browColor=appearance.hairColor;
    appearance.eyeColor=pick(palettes.eyeColor);appearance.expression=pick(['neutral','happy','shy']);
    for(const key of ['build','shoulders','chest'])appearance[key]=pick([1,1,2,2,3]);
    appearance.height=Math.floor(Math.random()*5);appearance.blush=pick([0,1,1,2]);appearance.freckles=pick([0,0,1,2]);
    return normalize(appearance);
  }
  const presets = [
    { id: 'mint', label: '薄荷日常', appearance: normalize() },
    { id: 'sunny', label: '暖阳出游', appearance: normalize({ gender:'female', hairStyle:'ponytail', bangs:'side', hairColor:'#AA7854', browColor:'#77563F', eyes:'round', eyeColor:'#8C704C', outfit:'overalls', clothesColor:'#F2E5CD', accentColor:'#D4BC8A', bottom:'shorts', bottomColor:'#7F9FAD', hat:'straw', hatColor:'#D9B777', shoes:'sandals', shoeColor:'#92775B', accessory:'ribbon', accessoryColor:'#E0A189', expression:'happy',freckles:1 }) },
    { id: 'midnight', label: '午夜街角', appearance: normalize({ gender:'male', skin:'#C9977F', hairStyle:'short', bangs:'side', hairColor:'#3D3E47', browColor:'#494049', eyes:'sharp', eyeColor:'#9C8060', outfit:'jacket', clothesColor:'#65768D', accentColor:'#E3D8C1', bottomColor:'#444B5E', shoes:'boots', shoeColor:'#625048', accessory:'earrings', accessoryColor:'#D2B373' }) },
    { id: 'rose', label: '玫瑰下午茶', appearance: normalize({ gender:'female', hairStyle:'long', bangs:'curtain', hairColor:'#805966', outfit:'dress', clothesColor:'#CDA0AB', accentColor:'#F2DED0', bottom:'skirt', bottomColor:'#BB8F9D', shoes:'flats', shoeColor:'#B68B83', accessory:'ribbon', accessoryColor:'#F2DED0', expression:'shy' }) },
    { id: 'sora', label: '海盐少年', appearance: normalize({ gender:'male', skin:'#F0CCB0', faceShape:'soft', hairStyle:'pixie',bangs:'side',hairColor:'#655444',browColor:'#655444',eyes:'round',eyeColor:'#65869B',outfit:'hoodie',clothesColor:'#94B4C1',accentColor:'#EEE4CF',bottomColor:'#6B778A',shoes:'sneakers',shoeColor:'#E6DECB',height:4,shoulders:2 }) },
    { id: 'peach', label: '蜜桃假日', appearance: normalize({ gender:'female', skin:'#F5D5C1', faceShape:'round',hairStyle:'twintails',bangs:'straight',hairColor:'#9C6858',browColor:'#80554A',eyes:'smile',outfit:'sweater',clothesColor:'#DEB3A0',accentColor:'#F4E3CC',bottom:'skirt',bottomColor:'#AE927B',shoes:'flats',shoeColor:'#865F55',accessory:'ribbon',accessoryColor:'#E7CD9B',expression:'happy',blush:2,height:2 }) },
    { id: 'forest', label: '森间来信', appearance: normalize({ gender:'nonbinary',skin:'#BD8D71',hairStyle:'curly',bangs:'none',hairColor:'#4F3F38',browColor:'#59443A',eyes:'almond',eyeColor:'#838F61',outfit:'jacket',clothesColor:'#879E80',accentColor:'#E8D9BA',bottomColor:'#8F7E6C',shoes:'boots',shoeColor:'#705741',hat:'beret',hatColor:'#B69B77',accessory:'roundGlasses',accessoryColor:'#B5986B',freckles:1 }) },
    { id: 'moon', label: '月光花园', appearance: normalize({ gender:'female',skin:'#F0D1BE',faceShape:'soft',hairStyle:'bun',bangs:'curtain',hairColor:'#B8B3B8',browColor:'#8F8290',eyes:'almond',eyeColor:'#8A789B',outfit:'dress',clothesColor:'#AFABCA',accentColor:'#EEE1CC',bottom:'skirt',bottomColor:'#9D98B8',shoes:'flats',shoeColor:'#8C8499',accessory:'earrings',accessoryColor:'#DCC992',expression:'neutral' }) }
  ];
  presets.forEach(p=>{p.appearance.styleMode='custom';});
  const customDefaults = Object.freeze({...currentDefaults,styleMode:'custom'});
  return { defaults:currentDefaults, customDefaults, fields, presets, gamePresets, normalize, randomize };
});
