from pathlib import Path
import json,html
r=Path(__file__).resolve().parents[1];m=json.loads((r/'manifest.json').read_text());s=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 1020" width="1280" height="1020"><rect width="1280" height="1020" fill="#f6f3e8"/><g fill="#405749" font-family="PingFang SC,Microsoft YaHei,sans-serif">'];k=12;cx,cy=400,460
def text(x,y,t,size=16,anchor='start'):s.append(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}">{html.escape(t)}</text>')
def rect(a,fill,stroke='none'):
 x0,y0,x1,y1=a;s.append(f'<rect x="{cx+x0*k}" y="{cy-y1*k}" width="{(x1-x0)*k}" height="{(y1-y0)*k}" fill="{fill}" stroke="{stroke}"/>')
def label(x,y,t,size=16):text(cx+x*k,cy-y*k,t,size,'middle')
text(70,57,'I · 到达与守护',30);text(70,88,'53.75 × 55 m / 保留 I01、I02 原位置 / 北 ↑',16)
rect([-26.875,-27.5,26.875,27.5],'#dbe2cc','#819278')
for a in m['vehicleRects']:rect(a,'#afb6af')
rect([18.5,-34.5,26.875,-27.5],'#afb6af')
for a in m['pathRects']:rect(a,'#fdf9ed')
rect([-22.375,3,.625,18],'#a6b7a0','#6e8779');label(-10.875,12,'I01 溪畔旅店',19);label(-10.875,8.5,'两层 / 六间客房',14)
rect([-19,18.4,-2,22.4],'#d7bc91');label(-10.5,20.4,'北侧木廊',13)
rect([-22.625,-21.5,2.375,-8.75],'#e5d0be','#b1846a');label(-10.125,-12.3,'I02 消防站',18);label(-10.125,-16,'值守区 + 双车库',14)
rect([-10.2,-19.5,-2.6,-16.9],'#bb6656');label(-6.4,-18.4,'消防车',11)
rect([11.95,10.25,15.35,19.75],'#799282');label(13.65,15,'候车棚',12)
rect([19.04,9.725,21.56,18.275],'#749080');label(20.3,14,'小巴',12)
label(10.5,-14,'消防前场',16);label(10.5,-17.1,'保持通畅',12);label(-13,-.8,'步行到旅店 / 商业街',13)
# Mark original door and transit access positions.
for x,y in [[-22.375,10.5],[-8.5,-8.75],[2.265,-18.2],[2.265,-12.05]]:s.append(f'<circle cx="{cx+x*k}" cy="{cy-y*k}" r="5" fill="#3b6b57"/>')
text(790,162,'空间安排',23)
for i,t in enumerate(['01  西北 · 溪畔旅店','一层接待、早餐与休息，二层6间客房。','各客房配独立卫浴，走廊连接双跑楼梯。','','02  东北 · 公交候车','小巴停靠、遮雨棚、长椅和站牌。','乘客沿西侧步道进入旅店与商业街。','','03  南侧 · 消防值守','两个东向车库位，一辆静态展示消防车。','出车前场与北侧公交停靠区分设。']):text(790,205+i*31,t,15)
text(790,604,'步道衔接',22)
for i,t in enumerate(['西 → 商业街','北 → 河岸公园','南 → 镇外车辆入口','西侧步道绕过消防前场']):text(790,646+i*34,t,16)
text(790,824,'坐标与交付边界',20)
for i,t in enumerate(['总图中心 (932.5, 830)，4 图纸单位 / 米。','附加7 m南侧道路用于展示入口衔接。','静态场景；车辆运行与人物行为待接入。']):text(790,860+i*28,t,13)
label(22.7,-37,'南 · 镇外入口',15);text(70,992,'2026-10-14 / I区模型布局示意 / 不作为施工图',13)
s.append('</g></svg>');(r/'布局示意.svg').write_text(''.join(s))
