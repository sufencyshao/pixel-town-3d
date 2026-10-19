from pathlib import Path
import json,html
ROOT=Path(__file__).resolve().parent.parent
repo=ROOT.parents[2]
r=json.loads((repo/'pixel_town_assets/roster.json').read_text());people=r['characters'];regular=sum(p['kind']=='human' for p in people);companions=sum(p['kind']=='codexmini' for p in people)
blocks=[{'id':'C01','floors':3,'units':6,'model':'apartment-3','center':[13,-20]},{'id':'C02','floors':4,'units':8,'model':'apartment-4','center':[13,20]},{'id':'C03','floors':4,'units':8,'model':'apartment-4','center':[-13,-20]},{'id':'C04','floors':4,'units':8,'model':'apartment-4','center':[-13,0]},{'id':'C05','floors':5,'units':10,'model':'apartment-5','center':[-13,20]}]
villas=[{'id':'A%02d'%(i+1),'units':1,'floors':2,'model':'courtyard','center':[x,y]} for i,(x,y) in enumerate([(x,y) for y in [20,0,-20] for x in [-24.5,24.5]])]
assert sum(b['units'] for b in blocks)==40
units=[]
for a in villas:units.append({'unitId':a['id'],'type':'courtyard','residentId':None})
for b in blocks:
 for f in range(1,b['floors']+1):
  for n in [1,2]:units.append({'unitId':b['id']+'-%d0%d'%(f,n),'type':'apartment','residentId':None})
data={'date':'2026-10-13','status':'design-review','source':'pixel_town_assets/roster.json; runtime assets/characters and assets/codexmini profile counts checked','regularResidents':regular,'optionalCompanions':companions,'capacityAssumption':'One independent dwelling per character; capacity planning, not current save occupancy. No resident assignments changed.','courtyardVillas':villas,'apartmentBlocks':blocks,'residentUnits':46,'heroUnits':1,'spareIfAll45Stay':46-regular-companions,'unitRegistry':units,'heroUnit':{'unitId':'A07','model':'hero','floors':2,'center':[0,-16],'vegetableBeds':3,'frontGardenAreas':2,'frontGardenStyle':'informal mixed planting','poolMetres':[3,6]},'siteZones':{'A':[75,62.5],'C':[53.75,62.5]},'coordinates':'Local metres, origin at zone centre, positive Y north. This is a placement proposal, not an approved full-town placement.'}
# Plot collision and zone containment checks, keeping intended pedestrian gaps between plots.
for key,items,W,D,size in [('A',villas+[{'id':'A07','center':[0,-16]}],75,62.5,None),('C',blocks,53.75,62.5,(25,17))]:
 boxes=[]
 for a in items:
  w,d=size or ((24,24) if a['id']=='A07' else (20,18));x,y=a['center'];assert abs(x)+w/2<=W/2;assert abs(y)+d/2<=D/2;boxes.append((a['id'],x-w/2,y-d/2,x+w/2,y+d/2))
 for i,a in enumerate(boxes):
  for b in boxes[i+1:]:assert min(a[3],b[3])<=max(a[1],b[1]) or min(a[4],b[4])<=max(a[2],b[2]),(a,b)
data['plotCheck']='PASS: each plot within its zone; no plot overlaps'
(ROOT/'housing-capacity.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="730" viewBox="0 0 1200 730"><rect width="1200" height="730" fill="#f5f2e8"/><style>text{font-family:PingFang SC,Microsoft YaHei,sans-serif;fill:#405646} .small{font-size:13px}.label{font-size:15px;font-weight:500}</style>']
def text(x,y,t,size=16,anchor='start'):svg.append(f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}">{html.escape(t)}</text>')
def rect(x,y,w,h,color,stroke=None,rx=3):svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{color}"'+(f' stroke="{stroke}"' if stroke else '')+'/>')
text(45,54,'溪畔住居 · 住宅区容量与落位建议',28);text(45,84,'6 栋双层独户别墅 + 5 栋河畔公寓 + 1 栋主角泳池别墅',15)
scale=5.4
for name,ox,oy,W,D,items in [('A 花园住宅区',45,154,75,62.5,villas),('C 河畔住宅区',610,154,53.75,62.5,blocks)]:
 text(ox,oy-20,name,21);rect(ox,oy,W*scale,D*scale,'#e0e6d2','#b3bfa5')
 def pos(x,y):return ox+(x+W/2)*scale,oy+(D/2-y)*scale
 # internal paths in spare strip between private plots
 if name.startswith('A'):
  for x in [-13.3,13.3]:
   px,py=pos(x,D/2);rect(px-.7*scale,py,1.4*scale,D*scale,'#d4cdb9')
 else:
  px,py=pos(0,D/2);rect(px-.5*scale,py,1.0*scale,D*scale,'#d4cdb9')
 for a in items:
  x,y=pos(*a['center']);w,d=(20,18) if name.startswith('A') else (25,17)
  rect(x-w/2*scale,y-d/2*scale,w*scale,d*scale,'#eaf0dc','#b4c19f')
  bw,bd=(12,9) if name.startswith('A') else (22,11)
  rect(x-bw/2*scale,y-bd/2*scale,bw*scale,bd*scale,'#c8aa8b' if name.startswith('A') else '#a8bcae','#748c75')
  text(x,y-2,a['id']+' · '+str(a['floors'])+' 层',12,'middle');text(x,y+16,str(a['units'])+' 户',11,'middle')
 if name.startswith('A'):
  x,y=pos(0,-16);rect(x-12*scale,y-12*scale,24*scale,24*scale,'#e9edda','#aabb99');rect(x-8*scale,y-4.5*scale,12*scale,9*scale,'#9eb5a3');rect(x+6.5*scale,y-3*scale,3*scale,6*scale,'#85c3cc','#5995a1');text(x-2*scale,y,'A07 主角',12,'middle');text(x,y+48,'2 层 / 1 户 / 小泳池',11,'middle')
  hx,hy=pos(0,-16)
  for dx in [-4,-1,2]:rect(hx+(dx-1)*scale,hy-(8.5+1.7)*scale,2*scale,3.4*scale,'#829968','#668057',1)
  for dx in [-6.15,2.15]:
   gx,gy=hx+dx*scale,hy+9.2*scale
   svg.append(f'<ellipse cx="{gx}" cy="{gy}" rx="{2.6*scale}" ry="{1.7*scale}" fill="#a5b98f"/>')
   for fx,fy,color in [(-1.4,-.4,'#d4909d'),(.3,.6,'#e9d084'),(1.5,-.5,'#f6f1de'),(-.4,-.7,'#a59abd')]:svg.append(f'<circle cx="{gx+fx*scale}" cy="{gy+fy*scale}" r="3" fill="{color}"/>')
  x,y=pos(0,16);rect(x-10*scale,y-12*scale,20*scale,24*scale,'#cedabb');text(x,y,'共享花园',14,'middle')
 else:
  x,y=pos(13,0);rect(x-11.5*scale,y-7.5*scale,23*scale,15*scale,'#c5d5b8');text(x,y,'河景共享庭院',13,'middle')
  xx=ox+W*scale+14;rect(xx,oy,14,D*scale,'#d6d1be');rect(xx+24,oy,62,D*scale,'#acd0cf');text(xx+55,oy+D*scale/2,'河',20,'middle');text(xx+55,oy+D*scale/2+28,'流',20,'middle')
 text(ox,oy+D*scale+25,f'区块 {W:g} × {D:g} m · 示意北上',13)
text(45,565,'容量核对',20)
text(45,596,f'现有角色库：{regular} 位常规居民 + {companions} 位伙伴；若都独立入住，需要 45 户。',15)
text(45,623,'庭院 6 户 + 公寓 2 × (3 + 4 + 4 + 4 + 5) = 46 户，余 1 户；主角另设 1 户。',15)
text(45,654,'本轮调整：庭院住宅由每栋 4 户改为独户别墅；河畔公寓由 3 栋改为 5 栋，采用三种层数。',14)
text(45,681,'采用原总图 A、C 区块范围检查地块容纳；户主未绑定。入口朝向、日照和完整路网仍需总图阶段联审。',13)
svg.append('</svg>');(ROOT/'住宅区调整示意.svg').write_text(''.join(svg));print('Capacity and nonoverlapping plot plan PASS')
