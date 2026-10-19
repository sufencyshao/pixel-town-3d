from pathlib import Path
import json
R=Path(__file__).resolve().parent.parent;m=json.loads((R/'manifest.json').read_text())
def pt(x,y):return 90+(x+42.5)*11,140+(31.25-y)*11
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="1000" viewBox="0 0 1120 1000"><rect width="1120" height="1000" fill="#f5f1e7"/><style>text{font-family:PingFang SC,Microsoft YaHei,sans-serif;fill:#405748}.title{font-size:31px}.name{font-size:20px;font-weight:600}.label{font-size:15px}.small{font-size:12px}</style><text x="70" y="57" class="title">B 区 · 公共服务庭院</text><text x="70" y="89" class="label">85 × 62.5 m ｜已有 2 栋 + 本次新建 4 栋｜上北下南</text>']
def rect(x,y,w,d,col,stroke='none'):
 a,b=pt(x,y+d);s.append(f'<rect x="{a}" y="{b}" width="{w*11}" height="{d*11}" fill="{col}" stroke="{stroke}" rx="2"/>')
def text(x,y,t,cls='label'):
 a,b=pt(x,y);s.append(f'<text x="{a}" y="{b}" text-anchor="middle" class="{cls}">{t}</text>')
def circle(x,y,r,col):
 a,b=pt(x,y);s.append(f'<circle cx="{a}" cy="{b}" r="{r*11}" fill="{col}"/>')
rect(-42.5,-31.25,85,62.5,'#d8e1cb','#91a485')
for a,b,c,d in m['paths']:rect(a,b,c-a,d-b,'#eee6d5')
for b in m['buildings']:
 x,y=b['center'];w,d=b['size'];col={'B01':'#d8c49b','B02':'#c2ceba','B03':'#b8cbc2','B04':'#d9b6a3','B05':'#baceb4','B06':'#bacdd3'}[b['id']]
 rect(x-w/2,y-d/2,w,d,col,'#82947c');text(x,y+2.3,b['id']+' '+b['name'],'name')
 text(x,y-.1,f'{w:g} × {d:g} m · '+('两层' if b['floors']==2 else '单层'),'small')
 summaries={'B01':'24 个学生座位 · 教师工作位','B02':'原模型 · 30 座阅览 · 22 级楼梯','B03':'原模型 · 平顶 · 医疗红十字','B04':'共享活动 / 咨询 / 儿童角','B05':'寄取件 / 分拣 / 后侧收发','B06':'便民接待 / 值班 / 社区调解'}
 text(x,y-2.4,summaries[b['id']],'small')
 ey=b['entry'][1];text(x,ey-.65 if b['door']=='s' else ey+.8,'▼ 入口' if b['door']=='s' else '入口 ▲','small')
rect(-35.125,-1.5,18,8,'#c6c8a9','#96a182');text(-26.125,2.6,'小学小操场');text(-26.125,.6,'18 × 8 m','small')
rect(-8.4,-1.7,5.5,4.5,'#c8c5a1');text(-5.65,.1,'阅读廊架','small');text(7,0,'共享树荫庭院','small');text(28,1.2,'诊所等候小庭','small')
text(2,-5.5,'4 m 公共步行带 · 东西连通');text(0,-28.1,'南侧公共步道 / 邮局后勤收发','small')
text(-26,26.3,'北侧花园步道','small');text(28,26.3,'北侧花园步道','small');text(0,-30.6,'↓ 南入口 · 接大树广场','small')
a,b=pt(36.25,12.4);c,d=pt(39.5,12.4);s.append(f'<path d="M {a} {b} L {c} {d}" stroke="#577b65" stroke-width="3"/>');text(28,6.3,'东侧辅助门 →','small')
for x,y in [(-35,23),(-22,23),(-5,23),(10,23),(24,23),(35,23),(-7.3,4),(10.3,4),(23,5.8),(33.5,5.8)]:circle(x,y,.95,'#9ab087')
s+=['<text x="70" y="874" class="label">落位：北排为小学、图书馆、诊所；南排为社区中心、邮局、警务站。</text><text x="70" y="906" class="label">保留图书馆与诊所原尺寸；诊所侧门及入口坡道仅修改本次区块副本。</text><text x="70" y="938" class="label">西接 A 区庭院住宅，东接 C 区河畔住宅，南接 E 区大树广场。</text><text x="70" y="974" class="small">静态设计 V1 / 2026-10-14 / 区块边界接口待整镇装配；人物活动、碰撞与寻路尚未接入</text></svg>']
(R/'布局示意.svg').write_text('\n'.join(s))
