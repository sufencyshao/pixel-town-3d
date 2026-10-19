from pathlib import Path
import shutil,json,base64,math
R=Path(__file__).resolve().parent.parent;S=R.parent/'whole-town-animals-3d-v6';T=R/'town';T.mkdir(exist_ok=True)
for folder in ['src','reference','assets/people','animal-library/assets']:(T/folder).mkdir(parents=True,exist_ok=True)
for p in (S/'src').glob('*.js'):shutil.copy2(p,T/'src'/p.name)
for name in ['manifest.json','environment-data.json','Town-complete.glb','整镇分区总图.svg']:shutil.copy2(S/name,T/name)
shutil.copy2(S/'reference/navigation.json',T/'reference/navigation.json')
for p in (S/'animal-library/assets').rglob('*'):
 if p.is_file() and p.suffix in ['.glb','.json']:
  q=T/'animal-library/assets'/p.relative_to(S/'animal-library/assets');q.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(p,q)
shutil.copy2(S/'animal-library/ATTRIBUTION.md',T/'animal-library/ATTRIBUTION.md')
shutil.copytree(S/'animal-library/vendor',T/'animal-library/vendor',dirs_exist_ok=True)
src=(S/'template.html').read_text();panel='''<section><h2>45位人物 · 场景试放</h2><p class="note">按职业分布在公共步道上，观察人物与建筑的尺度。动作试演不代表自主生活、实际工作或入住。</p><select id="resident-select" style="width:100%;padding:9px" aria-label="选择3D人物"></select><div class="grid"><button id="resident-focus">靠近查看人物</button><a class="link" href="../小镇人物-C方向-离线预览.html">返回人物制作室</a></div><div class="grid" id="resident-actions"></div><p id="resident-state">正在载入人物</p></section>'''
src=src.replace('<aside>','<aside>'+panel,1).replace('小镇动物生活','小镇人物与动物').replace('href="Town-with-animals.blend"','href="Town-with-residents.blend"').replace('<script>window.TOWN_META=', '<script>window.RESIDENT_META=__RESIDENT_META__;window.RESIDENT_PLACEMENTS=__PLACEMENTS__;window.RESIDENT_ASSETS={};window.TOWN_META=')
(T/'template.html').write_text(src)
p=T/'src/viewer.js';s=p.read_text().replace("import {AnimalWorld}","import {ResidentWorld} from './resident-world.js';\nimport {AnimalWorld}")
s=s.replace('let animalWorld;','let animalWorld,residentWorld;')
s=s.replace("animalWorld?.setVisibility(zone,solo,cut);dirty=true;","animalWorld?.setVisibility(zone,solo,cut);residentWorld?.setVisibility(zone,solo,cut);dirty=true;")
s=s.replace('window.townViewer.animals=animalWorld;',"window.townViewer.animals=animalWorld;residentWorld=await ResidentWorld.create({scene,camera,controls,host,animalWorld,focusDistrict:z=>district(z)});window.townViewer.residents=residentWorld;")
s=s.replace('animalWorld?.update(dt);','animalWorld?.update(dt);residentWorld?.update(dt);')
p.write_text(s)
# Source public pedestrian samples already have a42cm clearance; reserve distinct cells.
nav=json.loads((T/'reference/navigation.json').read_text())['humanNavigation'];meta=json.loads((R/'identity/identities.json').read_text())['characters'];zones=json.loads((T/'manifest.json').read_text())['zones'];used=[];placements=[]
cells=[(i,nav['origin'][0]+(i%nav['cols'])*nav['spacing'],nav['origin'][1]+(i//nav['cols'])*nav['spacing']) for i in nav['cells']]
roles={'B':['教师','图书','医','护士','警','邮','学生'],'D':['木匠','修理','画','音乐'],'G':['农','园艺'],'I':['消防','司机','旅店']}
counts={z:0 for z in zones}
for c in meta:
 if c['id']=='01_hero_male':continue
 z='E' if c['kind']=='codexmini' or c['id']=='02_hero_female' else next((z for z,words in roles.items() if any(w in c['role'] for w in words)),'H');cx,cy=zones[z]['center'];j=counts[z];counts[z]+=1;target=(cx+(j%4-1.5)*3,-cy+14+(j//4)*2)
 valid=[row for row in cells if abs(row[1]-cx)<zones[z]['size'][0]/2-2 and abs(row[2]+cy)<zones[z]['size'][1]/2-2 and all(math.hypot(row[1]-p[0],row[2]-p[1])>1.8 for p in used)]
 i,x,y=min(valid,key=lambda row:math.hypot(row[1]-target[0],row[2]-target[1]));used.append((x,y));placements.append({'id':c['id'],'zone':z,'cell':i,'position':[x,nav['heights'][str(i)],y]})
(T/'resident-placements.json').write_text(json.dumps(placements,ensure_ascii=False,indent=2))
print('Town sources copied without modifyingV6',len(placements))
