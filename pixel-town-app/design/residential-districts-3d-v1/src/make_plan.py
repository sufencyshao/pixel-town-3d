import json,html
from pathlib import Path
r=Path(__file__).resolve().parents[1];m=json.loads((r/'manifest.json').read_text());s=['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="960" viewBox="0 0 1400 960"><rect width="1400" height="960" fill="#f6f3e8"/><g font-family="PingFang SC,Microsoft YaHei,sans-serif" fill="#3c5144">']
def text(x,y,t,size=16,anchor='start'):s.append(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}">{html.escape(t)}</text>')
text(50,56,'A / C 住宅区 · 已建模型落位',30);text(50,88,'原尺寸装配 · 南向入户 · 共12栋 / 46户居民住宅 + 主角1户',17)
for z,cx,cy in [('A',385,420),('C',1050,420)]:
 k=8;w,h=m['districts'][z]['size']
 def rect(a,fill,stroke='none'):
  x0,y0,x1,y1=a;s.append(f'<rect x="{cx+x0*k}" y="{cy-y1*k}" width="{(x1-x0)*k}" height="{(y1-y0)*k}" fill="{fill}" stroke="{stroke}"/>')
 text(cx,145,z+(' 花园住宅 / 75 × 62.5 m' if z=='A' else ' 河畔住宅 / 53.75 × 62.5 m'),20,'middle');rect([-w/2,-h/2,w/2,h/2],'#d9e0c8','#819478')
 for p in m['paths'][z]:rect(p,'#fbf9f0')
 for b in [b for b in m['buildings'] if b['zone']==z]:
  rect(b['plot'],'#c8d4b8','#94a486');x,y=b['center'];hero=b['model']=='hero';ap=b['model'].startswith('apartment');hw,hh=(11,5.5) if ap else (6,4.5);bx=x-2 if hero else x
  rect([bx-hw,y-hh,bx+hw,y+hh],'#c6d0c3' if ap else '#749284' if hero else '#d9ac91','#7f9585');text(cx+bx*k,cy-y*k+4,b['id'],15,'middle');text(cx+bx*k,cy-y*k+22,f"{b['floors']}层 / {b['units']}户",12,'middle');ex,ey=b['entry'];s.append(f'<circle cx="{cx+ex*k}" cy="{cy-ey*k}" r="4" fill="#5c7650"/>')
  if hero:rect([x+6.1,y-7,x+9.1,y-1],'#9ccbd0')
 if z=='A':text(cx,cy-18*k,'共享花园',14,'middle')
 else:text(cx+13.6*k,cy+5,'共享庭院',14,'middle')
 text(cx,708,'● 入户接口；白色为连续社区步道',13,'middle')
text(50,760,'总图关系（下方按原位置绘制，上方为片区分别放大）',17)
k=4.4;x=100;y=805
for label,lo,hi,color in [('A',-37.5,37.5,'#c8d4b8'),('B 公共服务区 · 保留',45,130,'#e2dfd3'),('C',138.75,192.5,'#c8d4b8')]:
 xx=x+(lo+37.5)*k;s.append(f'<rect x="{xx}" y="{y}" width="{(hi-lo)*k}" height="65" fill="{color}" stroke="#94a486"/>');text(xx+(hi-lo)*k/2,y+39,label,16,'middle')
text(110,903,'A / C 中心相距 165.625 m；C 两列中心为 ±13.625 m，中间步道宽2.25 m。',15)
text(50,940,'2026-10-13 · 静态设计落位；非施工总图，人物、碰撞与寻路待接入。',12)
s.append('</g></svg>');(r/'住宅区落位.svg').write_text(''.join(s))
