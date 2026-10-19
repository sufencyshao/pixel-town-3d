from pathlib import Path
import json,math
R=Path(__file__).resolve().parent.parent
m=json.loads((R/'manifest.json').read_text());S=['<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="1080" viewBox="0 0 1280 1080"><rect width="1280" height="1080" fill="#f6f3e8"/><g font-family="PingFang SC,Microsoft YaHei,sans-serif" fill="#405741"><text x="80" y="62" font-size="34">F 区 · 河岸公园</text><text x="80" y="98" font-size="16">公园核心 53.75 × 55 m · 河流、对岸与桥梁为相邻环境衔接示意</text>']
def pt(x,y):return (90+(x+26.875)*10,160+(40-y)*10)
def poly(ps,col,stroke='none',dash=''):
 pts=' '.join(f'{pt(x,y)[0]},{pt(x,y)[1]}' for x,y in ps);S.append(f'<polygon points="{pts}" fill="{col}" stroke="{stroke}" stroke-dasharray="{dash}"/>')
def rect(x,y,w,d,col,label=None,stroke='none',dash=''):
 poly([(x-w/2,y-d/2),(x+w/2,y-d/2),(x+w/2,y+d/2),(x-w/2,y+d/2)],col,stroke,dash)
 if label:txt(x,y,label,16)
def txt(x,y,t,size=14):
 a,b=pt(x,y);S.append(f'<text x="{a}" y="{b+5}" text-anchor="middle" font-size="{size}">{t}</text>')
def shore(y):return 32.5+6.5*(y/40)**2
ys=[-40+i for i in range(81)]
poly([(21.5,-40)]+[(shore(y),y) for y in ys]+[(21.5,40),(21.5,27.5),(-26.875,27.5),(-26.875,-27.5),(21.5,-27.5)],'#d8e2c6')
poly([(shore(y),y) for y in ys]+[(shore(y)+20,y) for y in reversed(ys)],'#a2cbd0')
poly([(shore(y)+20,y) for y in ys]+[(72,40),(72,-40)],'#d4e0bc')
for p in m['pathPolygons']:poly(p,'#eee5d2')
for y in [35,-36.25]:rect(47.5,y,46.25,4.75,'#d8c09d','北桥' if y>0 else '南桥')
rect(-10.875,11,23,13,'#c1d2c8','F01 兽医小屋');txt(-10.875,8,'候诊 · 检查 · 护理',12)
rect(-14,-13,19,19,'#b6cc96','宠物活动草地','#91a66e');txt(-14,-16,'双门入口 / 遮阴 / 活动设施',11)
rect(9,-19,10,6,'#d1b996','小舞台');txt(9,-8,'观众长椅',13)
for x in [6,11.3]:
 for y in [-6.3,-9.2,-12.1]:rect(x,y,3.5,.64,'#879c80')
rect(shore(2)+1.5,2,10,8,'#d7c19e','观景台')
for x,y in [(6,20),(16,22),(18,9),(5,8),(9,26)]:
 a,b=pt(x,y);S.append(f'<circle cx="{a}" cy="{b}" r="14" fill="#90a776"/>')
a,b=pt(12,15);S.append(f'<ellipse cx="{a}" cy="{b}" rx="22" ry="19" fill="#96c6c9"/>');txt(12,11,'安静栖息角',15)
for x,y in [(-24,23),(-17,24),(-6,24),(-24,-26),(-16,-25.5),(-6,-25),(2,-25),(18,-25),(-21,-20),(-6.8,-8),(60,-25),(69,-18),(60,-10),(70,0),(60,12),(69,22),(62,29)]:
 a,b=pt(x,y);S.append(f'<circle cx="{a}" cy="{b}" r="13" fill="#99ad7f"/>')
rect(0,0,53.75,55,'none',None,'#657d55','6 5')
txt(0,30,'↑ 河畔住宅',16);txt(-31,0,'← 广场',15);txt(0,-31,'↓ 到达区',16);txt(46,20,'河流',18);txt(65,4,'自然岸线',15)
S.append('<text x="1180" y="175" font-size="22">N ↑</text><path d="M90 1010h100m-100 -6v12m100 -12v12" stroke="#405741" stroke-width="2"/><text x="120" y="1037" font-size="14">10 m</text><text x="320" y="1024" font-size="14">虚线框为 F 区原地块边界；河岸最终与总图装配时校准。</text></g></svg>')
(R/'布局示意.svg').write_text(''.join(S))
