from pathlib import Path
import json
R=Path(__file__).resolve().parent.parent;m=json.loads((R/'manifest.json').read_text());p=json.loads((R/'paving-layout.json').read_text())
def pt(x,y):return (90+(x+42.5)*10,135+(27.5-y)*10)
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="820" viewBox="0 0 1040 820"><rect width="1040" height="820" fill="#f4f0e5"/><style>text{font-family:PingFang SC,Microsoft YaHei,sans-serif;fill:#405748}.title{font-size:32px}.name{font-size:20px;font-weight:600}.label{font-size:15px}.small{font-size:13px}</style><text x="70" y="60" class="title">E 区 · 小镇客厅</text><text x="70" y="92" class="label">85 × 55 m ｜大树广场 · 周末市集 · 四向连接｜上北下南</text>']
def rect(x,y,w,d,col,stroke='none'):
 a,b=pt(x,y+d);s.append(f'<rect x="{a}" y="{b}" width="{w*10}" height="{d*10}" fill="{col}" stroke="{stroke}"/>')
def circle(x,y,r,col,stroke='none',sw=1):
 a,b=pt(x,y);s.append(f'<circle cx="{a}" cy="{b}" r="{r*10}" fill="{col}" stroke="{stroke}" stroke-width="{sw}"/>')
def text(x,y,t,cls='label'):
 a,b=pt(x,y);s.append(f'<text x="{a}" y="{b}" text-anchor="middle" class="{cls}">{t}</text>')
rect(-42.5,-27.5,85,55,'#d5dec5','#8d9e83')
for poly in p['positive']:
 points=' '.join(f'{pt(x,y)[0]},{pt(x,y)[1]}' for x,y in poly);s.append(f'<polygon points="{points}" fill="#ebe1cc"/>')
circle(0,-2.5,18,'none','#b4a58b');circle(0,-2.5,5.1,'#b89b76');circle(0,-2.5,3.8,'#9caf82');circle(0,-2.5,2.5,'#7f9b6e')
text(0,7.5,'大树广场','name');text(0,-12,'直径 36 m · 连续绕行');text(0,-2.2,'树荫环座','small')
for i,stall in enumerate(m['marketStalls']):
 x,y=stall['center'];rect(x-2.4,y-1.5,4.8,3,['#a7b9a3','#cfac98','#a5b9bb'][i%3]);text(x,y-.45,['鲜蔬','面包','鲜花','陶作','旧书','木作'][i],'small')
text(-29,3.5,'周末市集','name');text(-29,.8,'六个摊位 · 日常可移走','small')
circle(28,7,4.85,'#f7f3e7','#b4a58b');circle(28,7,4.3,'#91b9bd');text(28,7.5,'浅水景');text(28,5.3,'水深约 25 cm','small')
rect(22,-18,14,8,'#c5c4a3','#8a9f83');text(29,-13,'阅读廊架');text(29,-15.5,'座椅 · 小圆桌','small')
text(-12,22,'公告与换书');text(-12,19.8,'活动信息 / 交流','small');text(10.5,22,'饮水便民点','small')
for x,y in [(-36,23),(-26,22),(22,23),(35,22),(-34,-23),(-23,-24),(9,-24),(39,-22),(-8,-24.6)]:circle(x,y,1.4,'#9aaf84')
text(0,25,'↑ 服务区','small');text(0,-25.8,'↓ 商业街','small');text(-38,-3,'← 工坊','small');text(38,-3,'河岸 →','small')
s+=['<text x="70" y="731" class="label">日常：收起摊位与旗帜，保留活动空地；周末：六摊位围合西侧市集。</text><text x="70" y="760" class="label">主步道宽 4.5 m；环座、水池、便民设施与主要通行带分开布置。</text><text x="70" y="794" class="small">静态场景设计 V1 / 2026-10-14 / 人物活动、交易、流水与寻路尚未接入</text></svg>']
(R/'布局示意.svg').write_text('\n'.join(s))
