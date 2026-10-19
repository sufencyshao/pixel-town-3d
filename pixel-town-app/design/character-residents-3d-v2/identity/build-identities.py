"""Create the manually reviewed 45-resident appearance design manifest.

Read-only inputs: original roster and PNG frames. Outputs stay in this folder.
The appearance rows below were reviewed against all 45 source frames and the
eight back-view frames. Numeric body measurements are new 3D design choices.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path('/Users/summerwindy/Desktop/AI Chat')
OUT = Path(__file__).parent
ROSTER = ROOT / 'pixel_town_assets/roster.json'

# style | hair | skin | eye | upper | upper colour | lower | lower colour |
# shoes | shoe colour | accessories | visible identity points
ROWS = '''
short|#252420|#F5CEA6|#6B4429|tshirt|#20242B|jeans|#38648C|sneakers|#EDE9DF||黑色蓬松短发；棕色眼睛；原图白色短袖T恤；蓝色翻边牛仔裤；浅白运动鞋
bob|#302825|#F7D8B6|#543B2A|dress|#F5EBD8|dress|#F5EBD8|maryjane|#262321||齐下巴深棕短发；奶油白短袖分层裙；黑色花朵印花；白袜黑色搭带鞋
sidepart|#3D2C21|#F7D5AF|#503527|apron|#171A18|trousers|#242829|workshoes|#25251F||蓬松侧分棕发；白色衬衫卷袖；纯黑长围裙；深灰长裤；闭眼笑是原帧表情
short|#2E2721|#FCEBD4|#4F382C|chefcoat|#F4F2EA|trousers|#253044|workshoes|#292724|bakerhat,buttons|宽白色软面包帽；黑色短发；白色双排扣厨衣；深蓝灰裤；黑色工作鞋
spiky|#35251A|#F4BB86|#513624|shirt|#A7282C|jeans|#334B65|workboots|#705039|toolbelt,tools,belt|短棕发向上梳；浓直眉与方下颌；红黑格纹衬衫；蓝牛仔裤；腰带与工具袋；棕工作靴
short|#29221D|#F9D9B0|#583A24|uniform|#0D5F2E|uniform|#176D37|workshoes|#29281F|cap,badge,tie,satchel,belt|绿色有檐制服帽和金徽；绿制服与金色滚边；白衬衫领黑领带；棕色斜挎邮包；黑鞋
short|#201F1C|#F9D7AF|#4A3124|uniform|#0B1838|uniform|#152341|workshoes|#22282B|cap,badge,epaulettes,belt|深蓝警帽金徽；深蓝长袖制服；肩章胸徽与腰带；短黑发；正直浓眉
sidepart|#201F1D|#F8D6AE|#4B3326|coat|#EEEDE8|trousers|#222933|dressshoes|#292A28|glasses,stethoscope,belt|黑色侧分刘海；黑框长方眼镜；白大褂；浅蓝衬衫；深色裤；颈挂听诊器
short|#25221A|#A6572C|#3F2418|shirt|#516736|shorts|#52683B|rubberboots|#795030|strawhat,belt|宽檐草帽；深棕肤色；橄榄绿卷袖工装；绿短裤；棕色高筒园艺靴
long|#2B201A|#EACAA6|#5E432B|jacket|#33231E|jeans|#2F4864|boots|#392E26|guitar,belt|深棕凌乱中长发覆盖耳侧；棕黑皮夹克；白内搭；蓝牛仔裤；肩背木色吉他
short|#29241D|#F8D9B3|#513B29|chefcoat|#ECEEE9|trousers|#202125|workshoes|#2D2D27|chefhat,scarf,buttons|高白色厨师帽；红色颈巾；白色双排扣厨衣；黑长裤；笑眼与微红脸颊
singlebraid|#3E2F28|#F8DDBD|#5D3D27|dress|#F3E2C4|dress|#F3E2C4|maryjane|#342B23|bouquet,ribbon|侧面单条长棕辫；奶油色泡袖碎花裙；腰部蝴蝶结；手持白黄小花束；白袜黑搭带鞋
bun|#2E2520|#F8D8BC|#583D2B|uniform|#F4A3B7|skirt|#F4A3B7|maryjane|#2C2726|pastryhat,buttons|两侧圆发髻；粉色糕点软帽；粉色双排扣短袖制服与短裙；白袜黑鞋；笑眼
bob|#322721|#F6D9BB|#62432D|jacket|#DBC39D|dress|#F1EBDE|maryjane|#302A24|glasses,book|棕色短直发；细框眼镜；米色开衫内搭白裙；手持蓝封面书；白袜黑搭带鞋
bob|#2B2320|#F7D9BD|#593D2B|uniform|#F4B3CA|skirt|#F4B3CA|maryjane|#2C2728|nursehat,redcross,stethoscope|深棕齐颈发；白护士帽红十字；粉色护士服与裙；听诊器；白袜黑搭带鞋
bun|#2D2824|#F1D7B6|#624734|cardigan|#184C35|skirt|#EEDDBD|maryjane|#2E2B24|glasses,book|深色头发向后盘成低发髻；圆眼镜；墨绿开衫；米色及膝裙；怀抱棕色书；白袜黑鞋
ponytail|#4F3022|#F4D1AD|#67462B|vest|#194C3A|skirt|#262827|workshoes|#2C2924|apron,badge|低棕马尾；白卷袖衬衫与深绿马甲；棕色系腰围裙覆盖深色裙；黑色工作鞋
bob|#332923|#F0D2AE|#65492F|apron|#EDE7D8|jeans|#314F75|maryjane|#2A2726|beret,gloves,paintmarks|黑色贝雷帽；棕色不齐短发；白T上方彩色颜料围裙；蓝牛仔裤；浅绿手套
ponytail|#2A2623|#F7DABB|#553B2B|scrubs|#9DC7EE|scrubs|#9DC7EE|sneakers|#F1EFE7|stethoscope,hairtie|黑色齐颈发搭高小马尾；蓝色发圈；淡蓝上下分体医护服；颈挂听诊器；白运动鞋
ponytail|#4B3227|#F3D3B0|#5C3B28|hoodie|#CDB0E0|skirt|#28282F|sneakers|#2A292B|backpack,hairtie|棕色短发半扎小马尾；浅紫帽衫；黑色短裙；浅棕双肩包；白袜黑鞋
spiky|#B64A15|#EAA16B|#3C281C|uniform|#1C2F4B|uniform|#1F3049|workboots|#232328|reflective-stripes,badge,belt|橘棕上竖短发；深蓝消防服；胸臂腰与小腿黄色反光条；黑腰带与靴
short|#2C1B18|#955028|#34241B|vest|#4E735A|trousers|#202A3D|workshoes|#644329|glasses,badge|深棕肤色；短卷棕发；圆黑框眼镜；白卷袖衬衫绿马甲；深蓝裤；棕鞋
short|#D6D5D0|#EDAA72|#463326|overalls|#355D99|overalls|#355D99|workboots|#6D452B|strawhat,moustache,buttons|灰白眉鬓与白胡子；红带宽檐草帽；红格衬衫；蓝色背带裤；棕色工作鞋；鼻头较圆
short|#28231D|#D9945F|#413124|uniform|#759FC8|uniform|#19253F|dressshoes|#26272B|cap,tie,moustache,badge,belt|深蓝金徽司机帽；细黑胡须；浅蓝短袖衬衫；红领带；深蓝裤；黑皮鞋
swept|#A4A09D|#D9A271|#4D3525|apron|#733A7E|trousers|#262226|workshoes|#25242B|earring|银灰向上后梳的蓬发；黑短袖；紫色工作围裙；深色裤鞋；单侧小耳饰
short|#24232C|#BE6C32|#402A1D|apron|#F5DEB8|jeans|#244B68|workshoes|#26282C||乌黑短卷发；暖棕肤色；蓝色卷袖衬衫；奶油白围裙；深蓝裤；黑工作鞋
swept|#8C8787|#E9AC7B|#4F372A|sweater|#0E5555|trousers|#493A38|dressshoes|#67442D|glasses|灰色后梳短发与灰眉；方黑框眼镜；白衬衫领；蓝绿色毛衣；棕灰裤与棕鞋；年长面容
short|#261D1D|#844226|#2E201A|overalls|#D94708|overalls|#D94708|workboots|#643F29|beard,oilmarks|深棕肤色；黑短发与浓黑全胡须；亮橘色维修连体工装；深色油污补斑；棕靴
swept|#793E21|#E5A16E|#5B3923|vest|#633A24|trousers|#474334|dressshoes|#543A29|moustache,buttons,badge|棕色波浪短发；棕色上翘胡须；白短袖衬衫与棕马甲金扣；橄榄灰裤；圆润脸和腹部
long|#6B351C|#E5AA7A|#397549|apron|#65937F|trousers|#483A28|workboots|#5F402A|earring,flower-emblem|偏分棕色波浪及肩发；绿色眼睛；米白卷袖衬衫；灰绿花朵围裙；棕裤与棕靴
short|#312323|#8D482C|#352319|uniform|#1C2C48|uniform|#1D2D48|workboots|#25242A|reflective-stripes,badge,belt|深棕肤色；贴头短卷黑发；深蓝消防服；黄色反光条与胸徽；黑腰带与靴
bob|#AE351D|#EDAD77|#453025|apron|#F14F32|jeans|#264266|workshoes|#68432B|badge|红橘色齐颈短发；黄短袖翻领衬衫；红橘围裙；蓝裤；棕鞋
twinbraid|#24231D|#E7A16A|#4D3220|overalls|#515C29|overalls|#515C29|workboots|#6A482C|strawhat,earring,buttons|绿色帽带草帽；前侧两条黑辫；米白卷袖衬衫；橄榄绿背带裤；棕靴
short|#929294|#E8AE83|#5C4030|uniform|#275E49|uniform|#142447|dressshoes|#25282A|cap,tie,badge|灰色耳侧短发；深蓝金徽司机帽；墨绿制服外套金扣和金袖口；白领黑领带；深蓝裤；年长面容
swept|#E3B653|#E3A777|#4C2C30|uniform|#743F8E|trousers|#29262E|workshoes|#29252A|glasses,earring,scissors|金黄色蓬松短卷发；紫色上挑猫眼镜；金耳环；紫色短袖工服；腰侧剪刀；黑裤鞋
ponytail|#57301F|#95502D|#3C251C|apron|#29519D|trousers|#253753|workshoes|#2C272A|hoop-earrings,hairtie,cup-emblem|深棕肤色；高卷发侧马尾金发圈；金色大圈耳环；米色短袖衬衫；蓝围裙白咖啡杯标；深裤黑鞋
spiky|#9F3519|#D99462|#4F2F22|overalls|#7B2536|overalls|#7B2536|workboots|#65422B|earring,buttons|赤棕色短碎翘发；金色耳钉；黑短袖；酒红色背带工装裤；金搭扣；棕工作靴
bob|#24232C|#ECAC77|#4D3425|uniform|#526331|trousers|#323725|workshoes|#62452E|satchel,badge,earring|黑色齐下巴短发；橄榄绿短袖邮服；金黄斜挎邮包；深绿裤；棕鞋；金色小耳饰
singlebraid|#242533|#E9A675|#433124|uniform|#172644|uniform|#162543|workboots|#26252C|badge,epaulettes,belt|深蓝黑侧分发；后侧单条长辫；无帽深蓝短袖警服；金胸徽肩章；黑腰带靴
bob|#61351F|#EBB58A|#60422F|coat|#F1F0EA|scrubs|#147C80|sneakers|#E8E8E2|glasses,stethoscope,earring|棕色波浪短发；圆黑框眼镜；金小耳饰；白大褂；蓝绿色医护内搭和裤；听诊器；白鞋
long|#C6C4D8|#F5D6C9|#2485DC|dress|#84B2EA|dress|#84B2EA|maryjane|#5688D0|crown,pointed-ears,earring,neck-jewel|银灰长波浪发带淡紫冷光；明显尖耳；蓝色大眼；蓝宝石银冠和垂饰；浅蓝宝石领饰；蓝白花瓣短裙；蓝鞋
bob|#E8E6F1|#F7E3D4|#45AAE7|coat|#F3B8D3|shorts|#F5E9EE|boots|#DD7EAC|horns,tail,hairbeads,ribbon|白色齐肩发与浅紫发梢；一对浅白弯角；蓝色眼睛；深蓝蝴蝶结与串球发饰；粉白长袖外套；白短裤袜；粉靴；紫色尖球尾巴
long|#4A2D20|#F1D2AE|#A56A3C|dress|#F1DFC3|dress|#F1DFC3|flats|#E9CAAD||深棕偏分长波浪发；棕色眼睛；奶油色长袖长连衣裙；双手放在腹前；米色平底鞋
bob|#342C27|#F5D9B8|#6A4328|dress|#F0E4CC|dress|#F0E4CC|maryjane|#282525||深棕色短直发；奶油色层叠短袖裙；黑色花朵印花；白短袜黑色搭带鞋
long|#302A2E|#F4D6B4|#765038|tshirt|#F3F1EA|skirt|#242329|sneakers|#68656C|glasses,graphic-tee|黑色长卷发与齐刘海；粗黑大方框眼镜；白色图案T恤；中央红黄小图案；黑短裙；白袜灰黑运动鞋
'''.strip().splitlines()

# height in m; build; shoulder / waist / hip full widths in m; inseam-like
# crotch-to-floor fraction; head size multiplier; face width multiplier; age look.
DESIGN = [
 (1.760,'lean-athletic',.455,.315,.350,.490,1.00,1.00,'young-adult'),
 (1.620,'balanced',.365,.278,.377,.480,1.02,.97,'young-adult'),
 (1.790,'slender',.425,.300,.345,.505,.98,.96,'young-adult'),
 (1.670,'compact-stocky',.455,.360,.400,.465,1.05,1.08,'adult'),
 (1.880,'broad-muscular',.565,.430,.430,.480,1.00,1.15,'mature-adult'),
 (1.730,'wiry',.430,.306,.340,.500,.99,.96,'young-adult'),
 (1.840,'solid-athletic',.500,.370,.390,.490,.98,1.05,'adult'),
 (1.820,'slender',.435,.310,.355,.510,.98,.98,'mature-adult'),
 (1.710,'sturdy',.475,.360,.375,.470,1.04,1.04,'adult'),
 (1.810,'long-limbed-lean',.422,.295,.337,.515,1.00,.96,'young-adult'),
 (1.700,'compact',.455,.360,.395,.475,1.04,1.06,'adult'),
 (1.580,'petite-slender',.348,.260,.361,.480,1.03,.95,'young-adult'),
 (1.550,'compact-rounded',.360,.294,.390,.455,1.06,1.03,'young-adult'),
 (1.650,'slender',.360,.270,.370,.485,1.00,.98,'adult'),
 (1.600,'balanced',.365,.280,.380,.478,1.02,.99,'young-adult'),
 (1.640,'slender',.350,.270,.365,.480,1.00,.96,'mature-adult'),
 (1.690,'balanced',.380,.293,.394,.490,.98,1.00,'mature-adult'),
 (1.660,'lean',.360,.270,.365,.510,.99,1.00,'young-adult'),
 (1.570,'petite',.345,.263,.355,.475,1.05,.95,'young-adult'),
 (1.630,'slim',.350,.265,.360,.500,1.01,.96,'young-adult'),
 (1.860,'powerful-athletic',.530,.405,.415,.495,.98,1.09,'adult'),
 (1.740,'stocky',.480,.390,.410,.470,1.04,1.08,'adult'),
 (1.680,'broad-elder',.460,.410,.415,.460,1.07,1.10,'elder'),
 (1.780,'regular',.465,.365,.385,.485,1.02,1.04,'mature-adult'),
 (1.830,'lean',.440,.325,.360,.510,.99,1.00,'mature-adult'),
 (1.720,'sturdy',.480,.380,.400,.480,1.04,1.08,'adult'),
 (1.750,'slim-elder',.430,.335,.360,.480,1.03,1.03,'elder'),
 (1.890,'broad-muscular',.565,.430,.435,.485,1.00,1.12,'adult'),
 (1.705,'rounded',.510,.465,.450,.445,1.07,1.14,'mature-adult'),
 (1.770,'slender',.410,.300,.370,.515,1.00,.99,'adult'),
 (1.800,'athletic',.465,.340,.400,.500,1.00,1.04,'adult'),
 (1.595,'compact-broad',.405,.330,.410,.470,1.04,1.03,'adult'),
 (1.675,'sturdy',.415,.335,.415,.465,1.03,1.05,'adult'),
 (1.615,'balanced-elder',.385,.325,.390,.470,1.04,1.06,'elder'),
 (1.645,'rounded',.400,.320,.420,.480,1.05,1.05,'mature-adult'),
 (1.725,'athletic',.420,.310,.405,.510,.99,1.02,'adult'),
 (1.695,'compact-muscular',.445,.350,.420,.480,1.02,1.06,'adult'),
 (1.585,'petite-balanced',.370,.295,.380,.480,1.04,1.02,'adult'),
 (1.755,'long-limbed-athletic',.425,.310,.395,.510,.99,1.00,'adult'),
 (1.665,'regular',.380,.295,.390,.490,1.01,1.03,'mature-adult'),
 (1.465,'petite-fantasy',.325,.245,.325,.455,1.12,.98,'youthful-fantasy'),
 (1.200,'childlike-fantasy',.300,.250,.280,.430,1.28,1.08,'childlike-fantasy'),
 (1.735,'slender',.360,.270,.380,.500,.98,.96,'young-adult'),
 (1.565,'petite',.340,.255,.350,.475,1.06,.98,'young-adult'),
 (1.605,'compact',.350,.270,.360,.485,1.04,1.00,'young-adult'),
]

BACK_IDS = ['12_florist_female','16_librarian_female','17_cafeowner_female',
            '19_vet_female','20_student_female','33_farmer_female',
            '36_barista_female','39_police_female']

DETAILS = {
 '01_hero_male': {'sourceTopColor':'#F4F2EB','sourceTopType':'tshirt'},
 '02_hero_female': {'pattern':'black-flower','patternColor':'#242421'},
 '03_barista_male': {'underlayerType':'shirt','underlayerColor':'#ECEDE7','sleeveLength':'rolled-elbow'},
 '04_baker_male': {'hatColor':'#F2F0E7'},
 '05_carpenter_male': {'pattern':'plaid','patternColor':'#342023','sleeveLength':'rolled-elbow'},
 '06_postman_male': {'hatColor':'#0D5F2E','accessoryColor':'#826136','trimColor':'#D9AE37'},
 '07_police_male': {'hatColor':'#0B1838','trimColor':'#D2AB47'},
 '08_doctor_male': {'underlayerType':'shirt','underlayerColor':'#88B7E4','glassesShape':'rectangular'},
 '09_gardener_male': {'hatColor':'#D8B967','sleeveLength':'rolled-elbow'},
 '10_musician_male': {'underlayerType':'tshirt','underlayerColor':'#E9E5DC','guitarColor':'#9A5828'},
 '11_chef_male': {'hatColor':'#F1F0E7','scarfColor':'#A62A21'},
 '12_florist_female': {'pattern':'small-flowers','patternColor':'#B09B75','hairDetail':'single side braid','bowColor':'#C9C2B7'},
 '13_pastrychef_female': {'hairDetail':'twin round buns','hatColor':'#F7B4C3'},
 '14_teacher_female': {'underlayerType':'dress','underlayerColor':'#F1EBDE','glassesShape':'oval','bookColor':'#234A7B'},
 '15_nurse_female': {'hatColor':'#F6F1EA','crossColor':'#CD5474'},
 '16_librarian_female': {'hairDetail':'low centered bun','glassesShape':'round','bookColor':'#8C6D43'},
 '17_cafeowner_female': {'hairDetail':'low ponytail','underlayerType':'shirt','underlayerColor':'#EDEBE2','apronColor':'#795135'},
 '18_artist_female': {'underlayerType':'tshirt','underlayerColor':'#ECEAE0','hatColor':'#242320','pattern':'paint-splashes'},
 '19_vet_female': {'hairDetail':'bob with small high ponytail','hairtieColor':'#346195'},
 '20_student_female': {'hairDetail':'half-up short ponytail','backpackColor':'#B99969'},
 '21_firefighter_male': {'trimColor':'#E8BF1E'},
 '22_grocer_male': {'hairDetail':'short close curls','underlayerType':'shirt','underlayerColor':'#F3F0E7','glassesShape':'round'},
 '23_farmer_male': {'underlayerType':'shirt','underlayerColor':'#A73A31','pattern':'plaid','hatColor':'#DFA548','hatBandColor':'#A73B26','facialHairColor':'#DDDCD5'},
 '24_driver_male': {'hatColor':'#172D58','tieColor':'#8D2D2B','facialHairColor':'#332A23'},
 '25_hairdresser_male': {'hairDetail':'tall swept-back silver quiff','underlayerType':'tshirt','underlayerColor':'#282226'},
 '26_baker_male': {'hairDetail':'short soft curls','underlayerType':'shirt','underlayerColor':'#2C6790'},
 '27_librarian_male': {'glassesShape':'rectangular','collarColor':'#F2EBE1'},
 '28_mechanic_male': {'facialHairColor':'#261D1D','pattern':'oil-spots','patternColor':'#623B27'},
 '29_innkeeper_male': {'facialHairColor':'#743C20','underlayerType':'shirt','underlayerColor':'#F3EDE2','buttonColor':'#DBAC38'},
 '30_florist_male': {'hairDetail':'shoulder-length side-part waves','underlayerType':'shirt','underlayerColor':'#EFE0BF','emblemColor':'#E99CC4'},
 '31_firefighter_female': {'hairDetail':'close cropped curls','trimColor':'#E8BF1E'},
 '32_grocer_female': {'underlayerType':'shirt','underlayerColor':'#E6B54C'},
 '33_farmer_female': {'underlayerType':'shirt','underlayerColor':'#EAD5AC','hatColor':'#DFA548','hatBandColor':'#466730'},
 '34_driver_female': {'hatColor':'#172D58','trimColor':'#DDAF38','collarColor':'#F2EFE7'},
 '35_hairdresser_female': {'hairDetail':'short voluminous blonde curls','glassesShape':'cat-eye','glassesColor':'#542263','earringColor':'#E4BF49'},
 '36_barista_female': {'hairDetail':'high curly side ponytail','underlayerType':'shirt','underlayerColor':'#EFE0BF','hairtieColor':'#DDAF23','earringColor':'#E2B63D','emblemColor':'#EBEBE5'},
 '37_carpenter_female': {'underlayerType':'tshirt','underlayerColor':'#292328','buttonColor':'#D7A838'},
 '38_postal_female': {'satchelColor':'#E4A92E','earringColor':'#D7AC45'},
 '39_police_female': {'hairDetail':'one long centered back braid','trimColor':'#D7AA3F'},
 '40_doctor_female': {'underlayerType':'scrubs','underlayerColor':'#147C80','glassesShape':'round'},
 'hai-qin-yan': {'hairDetail':'long silver lavender waves','hemColor':'#DDE7FB','crownColor':'#D9DCE6','gemColor':'#287DE1','earShape':'pointed','dressSilhouette':'short layered petal skirt'},
 'kanna': {'hairDetail':'straight bob with pale lavender tips','hairTipColor':'#C5A3E2','hornColor':'#EDF4FA','hairbeadsColor':'#353B78','tailColor':'#AC87D5','underlayerColor':'#F5EBEE','coatTrimColor':'#EFEDEB'},
 'rui': {'hairDetail':'long side-part waves','dressSilhouette':'ankle-length gathered long-sleeve dress'},
 'xin': {'pattern':'black-flower','patternColor':'#282626'},
 'xin-fragrance': {'hairDetail':'long curls with straight fringe','glassesShape':'large-square','glassesColor':'#242124','emblemColor':'#CB472F'},
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(name, value):
    tmp = OUT / (name + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(OUT / name)


roster = json.loads(ROSTER.read_text())['characters']
assert len(roster) == len(ROWS) == len(DESIGN) == 45
characters, reference_hashes, supplement_hashes = [], [], []
for source, row, d in zip(roster, ROWS, DESIGN):
    a = row.split('|')
    assert len(a) == 12, (source['id'], len(a))
    hairstyle, hair, skin, eye, top, tc, bottom, bc, shoe, sc, acc, identity = a
    base = ROOT / 'pixel_town_assets' / source['assetFolder']
    frame = base / ('frame_01.png' if source['kind'] == 'human' else 'frames/idle/frame_01.png')
    observed = identity.split('；')
    features = dict(hairStyle=hairstyle, hairColor=hair, skinColor=skin, eyeColor=eye,
                    topType=top, topColor=tc, bottomType=bottom, bottomColor=bc,
                    shoeType=shoe, shoeColor=sc,
                    accessories=acc.split(',') if acc else [], distinctive=observed.copy())
    features.update(DETAILS.get(source['id'], {}))
    if source['id'] == '13_pastrychef_female':
        features['hairStyle'] = 'twin-buns'
    if source['id'] in ['22_grocer_male','26_baker_male','35_hairdresser_female']:
        features['hairStyle'] = 'curly'
    accessory_aliases = {
        'earring':'earrings','hoop-earrings':'earrings_hoop',
        'satchel':'pouch','hairtie':'hairtie','ribbon':'bow',
        'pastryhat':'bakerhat_pink','pointed-ears':'pointed_ears',
        'hairbeads':'hair_beads','neck-jewel':'neck_jewel',
        'reflective-stripes':'reflective_stripes','paintmarks':'paint_marks',
        'flower-emblem':'flower_emblem','cup-emblem':'cup_emblem',
        'graphic-tee':'graphic_tee','oilmarks':'oil_marks',
    }
    canonical = []
    for accessory in features['accessories']:
        token = accessory_aliases.get(accessory, accessory)
        if accessory == 'cap':
            token = ('cap_postal' if source['id'].startswith('06_') else
                     'cap_police' if source['id'].startswith('07_') else 'cap_driver')
        elif accessory == 'glasses':
            token = 'glasses_round' if features.get('glassesShape') in ['round','oval'] else 'glasses_square'
            if features.get('glassesShape') == 'cat-eye':
                token = 'glasses_cat_eye'
        elif accessory == 'scarf':
            token = 'scarf_red'
        canonical.append(token)
    features['accessories'] = canonical
    design = dict(zip(['height','build','shoulder','waist','hip','legRatio','headScale','faceWidth','ageStyle'],d))
    char = {k:source[k] for k in ['id','name','kind','role']}
    char['sex'] = {'男':'male','女':'female'}.get(source['sex'],source['sex'])
    char['referencePath'] = str(frame)
    char['referenceRelativePath'] = str(frame.relative_to(ROOT))
    char['features'] = features
    char['design'] = design
    char['observed'] = observed
    char['inferred'] = ['height、build、shoulder、waist、hip、legRatio、headScale、faceWidth均为本轮新3D设计值，并非原2D已有数值设定。',
                        'ageStyle仅为保持外观年龄感的制作描述，不声称角色实际年龄。',
                        '色值为原帧对应色块的代表性建模色；原帧有明暗及抗锯齿，不要求3D逐像素复制。']
    if source['id'] == '01_hero_male':
        char['designOverrides'] = {'basis':'selected-C-approved','topColor':'#20242B','topType':'tshirt',
                                   'reason':'按主任务指令沿用用户已选并看过的C V1.1黑T、蓝裤、浅鞋；原始2D白T事实单独保留。'}
        char['inferred'].append('黑色T恤是selected-C-approved外观覆盖；原2D frame_01为白色T恤。')
        features['distinctive'] = ['黑色蓬松短发','棕色眼睛','本批沿用已选C V1.1黑T外观','蓝色翻边牛仔裤','浅白运动鞋']
    if source['id'] in BACK_IDS:
        back = base / 'frame_10.png'
        char['supplementaryReferencePaths'] = [str(back)]
        supplement_hashes.append({'id':source['id'],'path':str(back),'sha256':digest(back)})
    if source['id'] == '33_farmer_female':
        char['observed'].append('正面为两条前侧辫；原背面帧辫子像素汇成单条中辫，源图各视图有简化差异。')
        char['inferred'].append('3D采用连贯双辫，优先保持原正面身份辨识点。')
    if source['id'] in ['hai-qin-yan','kanna']:
        char['inferred'].append('保留原图幻想/幼态外观，单独设计头身和身高；不套用统一成年人体型。')
    characters.append(char)
    reference_hashes.append({'id':source['id'],'name':source['name'],'path':str(frame),'sha256':digest(frame)})

result = {
 'schemaVersion':1,
 'purpose':'45位居民原2D身份视觉审计及C方向自然比例3D建模输入',
 'created':'2026-10-18',
 'scope':{'regularHumans':40,'companions':5,'total':45,'sourceChanged':False},
 'designParameterUnits':{'height':'metres, sole to crown, excluding hats/horns/hair volume',
  'shoulder':'metres, full shoulder breadth','waist':'metres, full transverse waist breadth',
  'hip':'metres, full transverse hip breadth','legRatio':'crotch-to-floor / height',
  'headScale':'head size multiplier relative to the C natural adult base',
  'faceWidth':'face transverse width multiplier relative to C natural adult face'},
 'sourcePolicy':'原frame_01及补充背面帧视觉核对，原2D、API和存档不修改；职业只读roster中的role。',
 'decisions':[
  '数值身高、身材与比例均为新增设计，逐人不同；未从旧像素身高推导真实厘米数。',
  '阿澈原帧白T与已选C V1.1黑T有差异，本批按主任务决定沿用selected-C-approved黑T，并显式记录覆盖。',
  '33禾青前后辫子简化不一致，3D取正面双辫保持身份；其余发型优先结合背面帧核对。',
  '所有图片联系表仅用于审阅，透明原图只读；图中缩放为最近邻。',
  '本JSON是建模输入和身份审计，不能单独代表45个3D模型已完成或已获用户视觉签收。'],
 'characters':characters,
}
atomic_json('identities.json',result)
atomic_json('protected-source-hashes.json', {'roster':{'path':str(ROSTER),'sha256':digest(ROSTER)},
            'references':reference_hashes,'supplementaryReferences':supplement_hashes})

assert len({c['id'] for c in characters}) == 45
assert len({c['design']['height'] for c in characters}) == 45
assert all(c['features']['hairColor'].startswith('#') for c in characters)
assert all(c['referencePath'] and Path(c['referencePath']).exists() for c in characters)
print('Wrote 45 characters, 45 unique heights, 53 source PNG hashes and roster hash.')
