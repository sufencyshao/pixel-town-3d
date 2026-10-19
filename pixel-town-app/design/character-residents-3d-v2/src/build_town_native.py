"""Create a separate editable town with45 residents and the existing20 animals."""
import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parent.parent;T=R/'town';S=R.parent/'whole-town-animals-3d-v6'
bpy.ops.wm.open_mainfile(filepath=str(S/'Town-with-animals.blend'))
old=[o for o in bpy.data.objects if o.get('actor_id')=='Ache_caretaker']
position=next(o.location.copy() for o in old if o.name.endswith('WORLD'))
for o in old:bpy.data.objects.remove(o,do_unlink=True)
for a in list(bpy.data.actions):
 if a.name.startswith('Ache_caretaker__'):bpy.data.actions.remove(a)
placements={r['id']:r for r in json.loads((T/'resident-placements.json').read_text())}
characters=json.loads((R/'assets/manifest.json').read_text())['characters'];collection=bpy.data.collections.new('C自然比例45人物');bpy.context.scene.collection.children.link(collection)
for c in characters:
 with bpy.data.libraries.load(str(R/c['blend']),link=False) as (data,target):target.objects=list(data.objects);target.actions=list(data.actions)
 actions=list(target.actions);objects=list(target.objects)
 for a in actions:
  if a:a.name=c['id']+'__'+a.name;a.use_fake_user=True
 wrapper=bpy.data.objects.new(c['id']+'__WORLD',None);collection.objects.link(wrapper);wrapper['actor_id']=c['id'];wrapper['kind']='resident';wrapper['visible_name']=c['name']
 if c['id']=='01_hero_male':wrapper.location=position
 else:
  x,y,z=placements[c['id']]['position'];wrapper.location=(x,-z,y)
 for o in objects:
  collection.objects.link(o);o['actor_id']=c['id'];o['kind']='resident';o.name=c['id']+'__'+o.name
  if not o.parent:o.parent=wrapper
 print('TOWN_RESIDENT',c['id'],len(actions),flush=True)
bpy.context.scene.frame_set(0);bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
p=T/'Town-with-residents.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p),compress=True);bpy.ops.wm.open_mainfile(filepath=str(p))
resident_ids={o.get('actor_id') for o in bpy.data.objects if o.get('kind')=='resident'};rigs=[o for o in bpy.data.objects if o.type=='ARMATURE'];n=[a for a in bpy.data.actions if any(a.name.startswith(c['id']+'__') for c in characters)]
report={'residentCount':len(resident_ids),'residentActions':len(n),'rigs':len(rigs),'bones':sum(len(o.data.bones) for o in rigs),'file':str(p.relative_to(R)),'passed':len(resident_ids)==45 and len(n)==1350 and len(rigs)==65,'scope':'Editable initial placement and animation library; simulation is provided byHTML, not embedded inBlender.'}
(R/'qa/town-native-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));assert report['passed'],report
