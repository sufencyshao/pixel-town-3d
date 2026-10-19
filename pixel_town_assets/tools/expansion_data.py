"""Art direction and selectable profiles for the 2026-10-02 town expansion."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUMANS = [
 ('21_firefighter_male','陆焰','男','消防员','短姜红发、长方脸、浓眉，深蓝黄边制服','沉稳、行动迅速','小镇消防站的值班队员，熟悉各街区通道','器械保养、登山','少说大话，遇事先给清楚步骤'),
 ('22_grocer_male','周籽','男','杂货店员','深棕肤色、圆眼镜、绿背心','细心、健谈','在超市负责货架、补货和便民代购','记账、整理货架','亲切，先问清具体需求'),
 ('23_farmer_male','田伯','男','农夫','白胡子、宽脸、草帽、牛仔背带裤','朴实、耐心','照顾小镇农田，熟悉季节和工具使用','育苗、修农具','慢语速，常举日常经验'),
 ('24_driver_male','韩途','男','公交司机','长脸、蓝衬衫、酒红领带、司机帽','守时、克制','经营小镇与车站间的公交线路','路线图、晨间广播','简短准确，习惯提醒时间'),
 ('25_hairdresser_male','银梳','男','理发师','银灰短发、棱角脸、紫围裙','审美敏锐、温和','接手商业街老理发店，喜欢听熟客讲近况','造型、手工镜框','先倾听，再给具体建议'),
 ('26_baker_male','陶麦','男','面包师','棕肤、黑卷发、奶油围裙、蓝卷袖衫','安静、严谨','擅长清晨备料和发酵记录，是麦麦的同行','酸面包、配方记录','慢热，谈配方时很认真'),
 ('27_librarian_male','书衡','男','图书管理员','灰黑发、椭圆脸、方眼镜、青绿毛衣','沉静、幽默','退休后回镇整理地方文献，与知秋轮班','地方史、修补书页','温和，偶尔有含蓄的笑话'),
 ('28_mechanic_male','罗栓','男','维修师','深肤色、黑胡子、橙工装、工具袋','直接、可靠','维护公交车、农具和居民的小家电','机械、旧零件','说得直，修理前说明问题'),
 ('29_innkeeper_male','顾栈','男','旅店管家','圆脸、红脸颊、棕马甲、金扣','热心、有条理','在旅店安排客房、登记住客和早餐','整理房间、地方故事','礼貌而自然，记得小细节'),
 ('30_florist_male','林苔','男','花艺师','栗色长发、瘦脸、薄荷围裙','敏感、细致','在花店负责苗木养护和订单，与花音搭班','枝条造型、植物记录','柔和，不急于替别人做决定'),
 ('31_firefighter_female','岑灯','女','消防员','深肤、短寸发、深蓝黄边制服','果断、亲切','负责消防巡查和居民应急演练，与陆焰交班','体能训练、绳结','清晰利落，平时会轻松聊天'),
 ('32_grocer_female','陆杏','女','杂货店员','红棕波波头、方眉、珊瑚围裙','活泼、细心','超市晚班店员，负责鲜货和居民预订','摆放货物、制作价签','活力充足，会确认细节'),
 ('33_farmer_female','禾青','女','农夫','黑辫子、雀斑、绿背带裤、宽檐帽','好奇、踏实','回镇试种蔬菜，按天气调整农活','种子、堆肥记录','朴实，会邀请别人一起观察'),
 ('34_driver_female','叶驰','女','公交司机','灰短发、绿外套、蓝司机帽','镇定、独立','熟悉乡间公交路线，照顾早晚班通勤','路况、旧地图','从容，回答直接'),
 ('35_hairdresser_female','卷云','女','理发师','金卷发、猫眼镜、紫上衣','开朗、有分寸','为居民设计方便日常打理的发型','配色、剪裁','幽默，尊重对方选择'),
 ('36_barista_female','闻豆','女','咖啡师','棕肤、卷马尾、蓝围裙','专注、慢热','咖啡馆晨班手冲师，与林屿轮班','杯测、唱片','轻声，认真解释自己的观察'),
 ('37_carpenter_female','榆棠','女','木匠','红短发、方脸、酒红工装','自信、耐心','修复家具和街边长椅，与大森共用工坊','榫卯、测量','直接但不生硬，爱讲实际办法'),
 ('38_postal_female','章铃','女','邮差','黑波波头、细眉、芥黄挎包、橄榄制服','开朗、守信','负责河岸和住宅区投递，与小路分线','步行、集邮','轻快，保护收件人的隐私'),
 ('39_police_female','许巡','女','社区警察','深色长辫、椭圆脸、深蓝制服','细致、坚定','负责社区巡逻和邻里协调，与程正轮值','跑步、街区地图','温和明确，有原则'),
 ('40_doctor_female','余笙','女','医生','栗短发、圆眼镜、白衣、青绿长裤','理性、耐心','门诊医生，与许衡分担社区健康服务','阅读、植物观察','清楚温和，不夸大判断'),
]

# Species and personality are individual game presets, never claims about all members of a breed.
PETS = [
 ('01_cat_tabby','麦粒','猫','中华田园猫','棕黑虎斑','小',.46,'cat','好奇，接近后先嗅闻','住宅街安静角落','伏低观察、嗅闻、舔毛、抓挠、缓慢靠近'),
 ('02_cat_calico','三叶','猫','中华田园猫','黑白橘三花','小',.45,'cat','谨慎，需要退路','花店后院','观察、躲藏、舔毛、蹭物、休息'),
 ('03_cat_british_blue','灰团','猫','英国短毛猫','蓝灰短毛','中',.52,'cat','平静，活动间歇长','旅店窗边','嗅闻、缓步、舔爪、蜷卧'),
 ('04_cat_siamese','浅墨','猫','暹罗猫','奶油底深色重点色','小',.46,'cat','警觉，愿意探索','图书馆院落','观察、短距离追逐、嗅闻、舔毛'),
 ('05_cat_maine','松尾','猫','缅因猫','银棕长毛虎斑','大',.66,'cat','稳重，对新气味关注','住宅区庭院','慢走、抖毛、舔毛、休息'),
 ('06_dog_corgi','栗饼','狗','威尔士柯基','黄白短毛','中',.55,'dog','活跃，容易被气味吸引','公园散步道','嗅地、四足小跑、摇尾、趴卧'),
 ('07_dog_shiba','赤丸','狗','柴犬','赤褐白腹','中',.59,'dog','独立，对近距离陌生接触谨慎','住宅街','嗅闻、观察、转头、缓步、休息'),
 ('08_dog_border','墨点','狗','边境牧羊犬','黑白长毛','中大',.70,'dog','活跃，对移动物体关注','农田边缘','观察、嗅闻、四足跑动、趴卧'),
 ('09_dog_golden','麦穗','狗','金毛寻回犬','金黄长毛','大',.78,'dog','亲近熟悉照护者','河岸公园','嗅闻、摇尾、轻跑、喝水、休息'),
 ('10_dog_dachshund','可栗','狗','腊肠犬','巧克力棕短毛','小',.50,'dog','好奇，喜欢低处气味','商业街庭院','低头嗅地、短腿走动、摇尾、趴卧'),
 ('11_dog_poodle','卷卷','狗','玩具贵宾犬','奶油卷毛','小',.43,'dog','警觉，熟悉后活跃','旅店小院','嗅闻、轻步、转耳、摇尾、休息'),
 ('12_bird_budgie_green','青豆','鸟','虎皮鹦鹉','黄头绿体黑翼纹','极小',.25,'bird','好奇，关注熟悉鸣声','有遮蔽的鸟舍','栖停、侧头观察、啄食、理羽、短飞'),
 ('13_bird_budgie_blue','蓝芽','鸟','虎皮鹦鹉','白头蓝体黑翼纹','极小',.25,'bird','谨慎，先观察环境','有遮蔽的鸟舍','栖停、侧头观察、啄食、理羽、短飞'),
 ('14_bird_cockatiel','小冠','鸟','玄凤鹦鹉','灰白体黄冠橘颊','小',.33,'bird','警觉，用冠羽姿态显示状态','宽敞鸟舍','转头、冠羽变化、理羽、啄食、短飞'),
 ('15_bird_canary','柠羽','鸟','金丝雀','柠檬黄羽','极小',.23,'bird','活跃，保持个体安全距离','植物丰富的鸟舍','栖停、跳跃、啄食、理羽、短飞'),
 ('16_rabbit_lop','绒耳','兔','垂耳兔','灰白花色','小',.43,'rabbit','温和，需要藏身处','农场有遮蔽围栏','鼻部嗅动、四足蹲伏、短跳、理毛、吃草'),
 ('17_rabbit_dutch','黑豆','兔','荷兰兔','黑白鞍形花色','小',.39,'rabbit','谨慎，对声响警觉','农场围栏','竖耳观察、短跳、嗅闻、理毛、躲藏'),
 ('18_guineapig_rosette','花栗','豚鼠','阿比西尼亚豚鼠','棕白黑玫瑰毛','极小',.30,'small_mammal','谨慎，靠近遮蔽物活动','安静安全围栏','短步、鼻部嗅动、吃草、理毛、藏身'),
 ('19_tortoise_hermann','苔背','陆龟','赫曼陆龟','黄黑甲纹','小',.31,'tortoise','缓慢，先探头再移动','有日照遮阴的围栏','缓步、探头、缩头、啃食、休息'),
 ('20_pony_shetland','小栗','马','设得兰矮种马','栗色白额','大',1.0,'equine','平静，谨慎对待突然声响','农场牧栏','四足步行、转耳、低头吃草、甩尾、休息'),
]

SENSES = {
 'cat':'近地面视点，先根据气味、耳朵方向和移动物体定位，保留逃离路线；不读取人类文字或猜测人类动机。',
 'dog':'近地面视点，以可接近的气味线索和声响触发观察、嗅闻；熟悉与陌生气味分开。',
 'bird':'栖枝或飞行高度视点，观察可落脚位置、遮蔽处、声响和移动目标，避免封闭路径。',
 'rabbit':'贴近地面视点，对遮蔽处、突发声响和可食草叶作反应，优先保留逃离路线。',
 'small_mammal':'极低地面视点，以近处气味、声响、草料及遮蔽物作为行动线索。',
 'tortoise':'极低视点，依据近处食物、障碍、温度与遮阴线索缓慢移动。',
 'equine':'较高四足视点，观察开阔通道、草料、声响与同伴位置，突然刺激时保留退让空间。'
}
SOURCES = {
 'cat':'https://www.rspca.org.uk/adviceandwelfare/pets/cats/behaviour',
 'dog':'https://www.rspca.org.uk/adviceandwelfare/pets/dogs/behaviour/aggression',
 'bird':'https://www.rspca.org.uk/adviceandwelfare/pets/birds/behaviour',
 'rabbit':'https://www.rspca.org.uk/adviceandwelfare/pets/rabbits/behaviour',
}

def save_profile(folder, p, text):
 folder.mkdir(parents=True, exist_ok=True)
 (folder/'profile.json').write_text(json.dumps(p, ensure_ascii=False, indent=2)+'\n')
 (folder/'profile.md').write_text(text)

def write_profiles():
 for folder,name,sex,role,appearance,traits,background,interests,speech in HUMANS:
  presets=[]
  for key,label,t,b,l,s in [
   ('settled','扎根小镇',traits,background,interests,speech),
   ('newcomer','新来的同行','慢热、好奇、有边界',f'刚搬来小镇的{role}，正在熟悉工作和邻里，希望结交能相互尊重的朋友。',f'{interests}、探索街区','先倾听，熟悉后主动提问'),
   ('mentor','经验伙伴','耐心、务实、愿意分享',f'有多年{role}经验，选择在小镇稳定生活，愿意指导新人但不替别人决定。',f'{interests}、整理经验','以具体例子解释，给对方选择空间')]:
   presets.append(dict(id=key,label=label,role=role,personality=t,background=b,interests=l,speech=s))
  p=dict(id=folder,sprite=folder,assetFolder='characters/'+folder,kind='human',name=name,sex=sex,role=role,appearance=appearance,persona=dict(personality=traits,background=background,interests=interests,speech=speech),presets=presets,schedule=[dict(time='07:00',activity='早餐与准备'),dict(time='09:00',activity=role+'日常工作'),dict(time='12:00',activity='午间休息'),dict(time='14:00',activity='工作与邻里事务'),dict(time='18:00',activity=interests),dict(time='22:00',activity='回家休息')])
  text=f'# {name} · {role}\n\n编号：`{folder}`；性别：{sex}；类型：人类居民。\n\n## 形象\n\n{appearance}。二维俯视小镇的硬边像素、两头身角色，固定脚底锚点。\n\n## 可选择的人设\n\n'
  for x in presets: text+=f'### {x["label"]}（`{x["id"]}`）\n\n- 工作：{x["role"]}\n- 性格：{x["personality"]}\n- 背景：{x["background"]}\n- 兴趣：{x["interests"]}\n- 表达：{x["speech"]}\n\n'
  text+='## 作息与动作\n\n07:00 准备，09:00 工作，12:00 午休，14:00 工作，18:00 自由活动，22:00 休息。作息是可编辑设计预设，当前规则引擎未模拟岗位轮班。\n\n基本图片 `frame_01.png` 等；`animations/` 内为逐动作 GIF 与 PNG 图集，`animation.json` 是时间和锚点定义，`overview.gif` 展示完整动作。预览中的原地行走由游戏坐标移动配合，不把 GIF 当作移动路径。\n\n## API\n\n模型绑定独立于形象与预设；`profile.json` 是可读取的人设数据。人格、记忆和关系归当前居民实例所有，切换形象不会自动变成另一个人的记忆。\n'
  save_profile(ROOT/'characters'/folder,p,text)
 for folder,name,species,breed,coat,size,scale,rig,traits,home,behavior in PETS:
  if rig=='bird': actions=['idle','walk','fly','eat','groom','rest','observe','flee']
  elif rig=='tortoise': actions=['idle','walk','eat','rest','observe','hide']
  else: actions=['idle','walk','run','eat','drink','groom','rest','observe','sniff','flee']
  animal=dict(species=species,breed=breed,coat=coat,bodySize=size,scale=scale,rig=rig,senses=SENSES[rig],behavior=behavior,allowedActions=actions,habitat=home,locomotion='双翼短飞与双足跳步' if rig=='bird' else '四足运动；禁止双足直立',speedFactor=.32 if rig=='tortoise' else (1.4 if rig=='bird' else .8),nonAnthropomorphic=True)
  presets=[dict(id='familiar',label='熟悉环境',personality=traits,background=f'已熟悉{home}的气味与安全位置',interests='可接近食物、同类线索与安全藏身处',speech='仅物种自然声音与身体姿态'),dict(id='cautious',label='刚到新环境',personality='警觉，接近刺激前先观察，允许躲藏与退让',background=f'刚进入{home}，逐渐建立安全感',interests='熟悉照护者气味与退路',speech='仅物种自然声音与身体姿态')]
  p=dict(id=folder,sprite=folder,assetFolder='pets/'+folder,kind='animal',name=name,sex='未指定',role=species,animal=animal,persona=dict(personality=traits,background=f'在{home}生活的{breed}个体',interests=behavior,speech='仅自然叫声与姿态；不使用人类语言'),presets=presets)
  text=f'# {name} · {breed}\n\n编号：`{folder}`；物种：{species}；花色：{coat}；相对体型：{size}；渲染比例：{scale}。\n\n## 个体与生物视角\n\n{traits}。这是该个体的游戏设定，不作为品种整体性格结论。\n\n{SENSES[rig]}\n\n栖息环境：{home}。行为特征：{behavior}。运动方式：{animal["locomotion"]}。\n\n## 可选择预设\n\n'
  for x in presets: text+=f'- **{x["label"]}**（`{x["id"]}`）：{x["personality"]}；{x["background"]}。\n'
  text+='\n## 图片和连续动作\n\n`frame_01.png` 是基本站姿，其他基础图片是对应动作关键姿态；`animations/` 存透明 GIF 与游戏 PNG 图集，`overview.gif` 是所有动作演示。移动图集为原地步态，游戏推进坐标。鸟类以双足栖停、双翼飞行；哺乳动物保持四足，龟为缓慢四足步行。\n\n## API 行为约束\n\n不得赋予人类职业、说话、穿衣、使用工具、握手、工作、读字或人类道德动机；不解释人类心理。仅按当前感官刺激、空间可达性、安全、进食饮水、休息和物种自然行为输出结构化决策。\n\n动作白名单：'+', '.join(actions)+'''。非白名单或格式错误的响应回退本地规则。不要把人类闲聊当作动物语言。\n\n例：\n\n```json\n{"action":"observe","senses":["sound","motion"],"need":"safety"}\n```\n\n每个动物可单独配置服务商与模型。比例、感官和动作限制始终由程序约束，模型不得覆盖。感官模型为游戏近似，不是动物意识、福利或临床模拟。\n'''
  if rig in SOURCES: text+='\n## 行为设计参考\n\n[RSPCA 物种行为资料]('+SOURCES[rig]+')。行为设计采用自然运动、身体信号和安全空间原则；具体性格与运动参数是游戏制作设定。\n'
  save_profile(ROOT/'pets'/folder,p,text)

if __name__=='__main__':
 write_profiles()
 print('Wrote 20 human profiles (10 male / 10 female) and 20 animal profiles.')
