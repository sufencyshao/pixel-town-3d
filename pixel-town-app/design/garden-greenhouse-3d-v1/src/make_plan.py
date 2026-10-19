from pathlib import Path
R=Path(__file__).resolve().parent.parent
S=['<svg xmlns="http://www.w3.org/2000/svg" width="1300" height="1040" viewBox="0 0 1300 1040"><rect width="1300" height="1040" fill="#f6f3e8"/><g font-family="PingFang SC,Microsoft YaHei,sans-serif" fill="#405741"><text x="70" y="65" font-size="34">G 区 · 田园与温室</text><text x="70" y="100" font-size="16" fill="#7c876d">75 × 55 m · 北接手作区 / 东接商业街 / 南接后勤路</text>']
def pt(x,y):return (90+(x+37.5)*14,160+(27.5-y)*14)
def rect(x,y,w,d,color,label=None):
 a,b=pt(x-w/2,y+d/2);S.append(f'<rect x="{a}" y="{b}" width="{w*14}" height="{d*14}" fill="{color}" rx="3"/>')
 if label:
  a,b=pt(x,y);S.append(f'<text x="{a}" y="{b+6}" text-anchor="middle" font-size="18">{label}</text>')
def txt(x,y,t,size=14):
 a,b=pt(x,y);S.append(f'<text x="{a}" y="{b}" text-anchor="middle" font-size="{size}">{t}</text>')
rect(0,0,75,55,'#d9e2c4')
for x,y,w,d in [(-3,0,3,55),(0,-25,75,4),(0,0,75,3),(15.375,24,39.75,1.8),(34.4,13,1.8,23),(-20,-12.75,29,2.5),(-20,-13.4,2.5,20),(-5,11.5,4,3),(5.875,-15,14.75,2.4),(22.375,-23,3,4),(-.1,-6.5,2.8,2)]:rect(x,y,w,d,'#f2ead5')
rect(-19.75,11.5,25.5,13,'#b7d5cf','G01 四季温室')
txt(-19.75,8.5,'六组育苗台 · 两块香草床')
for i,(x,y) in enumerate([(-27,-7.5),(-13,-7.5),(-27,-18),(-13,-18)]):
 rect(x,y,11,7.5,'#b69c7e',['01 叶菜','02 茄果','03 根茎','04 香草'][i])
 for k in range(5):
  a,b=pt(x-4.5,y-2.6+k*1.3);S.append(f'<path d="M{a} {b}h126" stroke="#788d61" stroke-width="3" opacity=".4"/>')
rect(22.375,-15,18.25,12,'#d8ccb4','G02 园艺工具屋')
txt(22.375,-17.5,'工具 · 换盆 · 分拣')
rect(4.8,-6.5,7,6,'#c8b798','休憩廊架')
for x in [3,5.9,8.8]:rect(x,-20,2.4,2.4,'#a99070')
txt(6,-17.8,'堆肥角')
rect(26.275,-7.3,2.4,.8,'#8aaca4');rect(30.175,-7.1,2.1,2.1,'#8aaca4');txt(24,-5.4,'洗手 / 雨水桶')
for y in [7,14.4,21]:
 for x in [9,19.7,29]:
  a,b=pt(x,y);S.append(f'<circle cx="{a}" cy="{b}" r="32" fill="#90a572"/><circle cx="{a+12}" cy="{b-8}" r="4" fill="#c38469"/>')
txt(19,2.4,'九株果树 · 季节采收')
txt(-20,23,'自然花边与缓冲绿化')
txt(-3,29,'↑ 北 · 手作工作区',17);txt(41,0,'→ 商业街',16);txt(0,-31,'南侧后勤路 · 工具屋备货与堆肥作业',17)
S.append('<text x="1210" y="180" font-size="20">N ↑</text><path d="M100 995h140m-140 -6v12m140 -12v12" stroke="#405741" stroke-width="2"/><text x="150" y="1025" font-size="14">10 m</text></g></svg>')
(R/'布局示意.svg').write_text(''.join(S))
