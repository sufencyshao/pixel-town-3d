import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from build_daily_actions import residents,prepare_human
from head_turn import CUT_Y
# Collar boundary sampled against normalized original sprites, not generated poses.
# x1/x2: edges of the fixed neck root; join: the upper fixed neck row.
# shoulder: first shirt/collar row to preserve outside the neck opening.
rows=[
(118,136,109,108),(119,138,109,109),(121,135,113,113),(118,137,137,138),(116,138,106,102),
(119,136,119,119),(116,139,115,111),(120,138,120,117),(119,137,120,114),(117,137,121,118),
(120,139,136,136),(121,136,104,102),(119,135,139,139),(119,139,119,115),(117,138,140,132),
(118,137,109,101),(121,136,106,102),(118,137,120,115),(119,137,122,121),(119,137,108,102),
(115,140,117,113),(118,139,124,118),(117,139,129,120),(118,140,127,121),(118,138,126,119),
(117,138,126,114),(117,138,125,115),(113,142,124,115),(119,137,126,109),(119,139,123,119),
(115,140,117,113),(118,138,124,118),(118,138,126,119),(119,137,127,122),(118,138,128,122),
(119,140,130,124),(117,137,125,119),(118,138,121,116),(118,138,125,118),(118,138,130,125)]
result={}
for p,(xl,xr,join,shoulder) in zip(residents('characters'),rows):
 role=int(p.name[:2]);front,_=prepare_human(p)
 # Wider shoulders still preserve the slope on each side of the neck opening.
 boundary=[[0,shoulder],[xl-10,shoulder],[xl,join],[xr,join],[xr+10,shoulder],[255,shoulder]]
 result[str(role)]={'role':p.name,'bodyBoundary':boundary,'neckRoot':[xl,xr,join],
 'targetNeckEnd':[round((xl+xr)/2),CUT_Y[role-1]],'skinMinR':145 if role==36 else 100 if role in (9,22,28,31) else 135,
 'review':'original collar and shoulders manually located; inspect final seam crops'}
(ROOT/'tools/head_joint_calibration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
