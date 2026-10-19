from pathlib import Path
import json
R=Path(__file__).resolve().parent.parent;m=json.loads((R/'manifest.json').read_text())
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="920" viewBox="0 0 1100 920"><rect width="1100" height="920" fill="#f4f0e5"/><style>text{font-family:PingFang SC,Microsoft YaHei,sans-serif;fill:#405748}.title{font-size:32px}.small{font-size:15px}.name{font-size:23px;font-weight:600}.sub{font-size:16px}</style><text x="70" y=" sixty"/>'.replace('<text x="70" y=" sixty"/>','')]
svg+=['<text x="70" y="60" class="title">D 区 · 手作工作区</text><text x="70" y="91" class="small">75 × 55 m ｜四栋单层工作场所｜单位：米｜上北下南</text>']
def rect(x,y,w,d,color,stroke='none',radius=0):
 svg.append(f'<rect x="{(x+37.5)*12+90}" y="{(27.5-y-d)*12+135}" width="{w*12}" height="{d*12}" rx="{radius}" fill="{color}" stroke="{stroke}"/>')
def text(x,y,s,cls='sub'):
 svg.append(f'<text x="{(x+37.5)*12+90}" y="{(27.5-y)*12+135}" text-anchor="middle" class="{cls}">{s}</text>')
rect(-37.5,-27.5,75,55,'#d9dfc8','#91a287')
rect(-37.5,-4.5,75,4,'#eee8d9');rect(-3,-27.5,3,55,'#eee8d9');rect(-37.5,-27.5,4.3,55,'#c7c7bd');rect(-37.5,20,72.5,4.5,'#c7c7bd')
for b,color in zip(m['buildings'],['#d5b199','#a2b7a6','#e8d9b7','#c3c4ae']):
 x,y=b['center'];w,d=b['size'];rect(x-w/2,y-d/2,w,d,color,'#687b69',4)
 text(x,y+2.2,b['id']+' '+b['name'],'name');text(x,y-.5,f'{w:g} × {d:g} m')
 text(x,y-2.7,' / '.join(b['people']),'small')
 door=y-d/2 if b['door']=='s' else y+d/2
 rect(x-1.7,min(door,-2.5),3.4,abs(door+2.5),'#eee8d9')
 text(x,door+(.8 if b['door']=='s' else -1.4),'入口','small')
rect(-35.4,8.5,2.9,3,'#c7c7bd');rect(22.6,17.5,4.8,5,'#c7c7bd')
text(0,21.3,'北侧后勤路 · 收货与补给','small');text(4,-2.0,'4 m 手作展示步行带','small')
for x,y in [(-30,25.7),(-8,25.7),(8,25.7),(29,25.7),(-29,-25),(-9,-25),(8,-25),(29,-25)]:
 svg.append(f'<circle cx="{(x+37.5)*12+90}" cy="{(27.5-y)*12+135}" r="12" fill="#9eaf86"/>')
text(-18.75,-24.3,'雕塑花园与绿带','small');text(17,-24.3,'安静绿带','small')
svg+=['<text x="70" y="840" class="sub">东接 E 大树广场 · 南接 G 田园与温室 · 北侧保留住宅缓冲绿带</text><text x="70" y="871" class="small">屋顶及四栋室内可独立显示。后勤与步行脊线交会处待整镇装配统一处理。</text><text x="70" y="899" class="small">独立场景设计 V1 / 2026-10-14 / 人物行为与寻路尚未接入</text></svg>']
(R/'布局示意.svg').write_text('\n'.join(svg))
