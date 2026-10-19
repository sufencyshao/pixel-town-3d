from pathlib import Path
import json
R=Path(__file__).resolve().parent.parent;m=json.loads((R/'manifest.json').read_text())
def pt(x,y):return 90+(x+42.5)*11,140+(27.5-y)*11
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="920" viewBox="0 0 1120 920"><rect width="1120" height="920" fill="#f5f1e7"/><style>text{font-family:PingFang SC,Microsoft YaHei,sans-serif;fill:#405748}.title{font-size:31px}.name{font-size:18px;font-weight:600}.label{font-size:15px}.small{font-size:12px}</style><text x="70" y="57" class="title">H 区 · 日常商业街</text><text x="70" y="89" class="label">85 × 55 m ｜已有咖啡厅 + 本次新建 5 间小店｜上北下南</text>']
def rect(x,y,w,d,col,stroke='none'):
 a,b=pt(x,y+d);s.append(f'<rect x="{a}" y="{b}" width="{w*11}" height="{d*11}" fill="{col}" stroke="{stroke}" rx="2"/>')
def text(x,y,t,cls='label'):
 a,b=pt(x,y);s.append(f'<text x="{a}" y="{b}" text-anchor="middle" class="{cls}">{t}</text>')
rect(-42.5,-27.5,85,55,'#d8e1cb','#91a485')
for a,b,c,d in m['paths']:rect(a,b,c-a,d-b,'#eee6d5')
rect(-37.85,4.52,22.7,3,'#d4c3a6')
notes=['18 座室内 + 4 座露台','展示 / 品尝 / 后场烘焙','16 座餐区 / 独立厨房','蔬果 / 干货 / 后仓','鲜花 / 绿植 / 花艺台','3 剪发位 / 2 洗发位']
for i,b in enumerate(m['buildings']):
 x,y=b['center'];w,d=b['size'];col=['#c2ceba','#d9b6a3','#d8c49b','#baceb4','#b8cbc2','#bacdd3'][i]
 rect(x-w/2,y-d/2,w,d,col,'#82947c');text(x,y+2,b['id']+' '+b['name'],'name');text(x,y-.2,f'{w:g} × {d:g} m · 单层','small');text(x,y-2.3,notes[i],'small')
 ey=b['entry'][1];text(x,ey-.95 if b['door']=='s' else ey+1.3,'▼ 顾客入口' if b['door']=='s' else '顾客入口 ▲','small')
 rx,ry=b['rear'];text(rx,ry+1.2 if b['door']=='s' else ry-1.3,'后门','small')
text(0,-2,'4.5 m 东西步行巷 · 店前外摆与绿化退让');text(-24,22,'北侧收货步道','small');text(24,22,'北侧收货步道','small');text(-24,-23.8,'南侧收货步道','small');text(24,-23.8,'南侧收货步道','small')
text(0,29.2,'↑ E 区 · 大树广场');text(-36,-26.6,'西接 G 区田园','small');text(34,-26.6,'东接 I 区旅店','small')
s+=['<text x="70" y="793" class="label">北排：咖啡、烘焙、家常餐饮；南排：日常采购、花艺与理发。</text><text x="70" y="826" class="label">保留六栋原规划中心；咖啡厅按原尺寸纳入，后门连接独立收货步道。</text><text x="70" y="859" class="label">同一工程含六店室内、店前外摆、自然花灌木、树荫座椅及四向区块接口。</text><text x="70" y="897" class="small">静态设计 V1 / 2026-10-15 / 待视觉反馈；整镇装配、营业逻辑、人物行为、碰撞与寻路尚未接入</text></svg>']
(R/'布局示意.svg').write_text('\n'.join(s))
