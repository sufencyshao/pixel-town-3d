"""Publish verified source asset folders and their editable profiles to the game."""
import json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
APP=ROOT.parent/'pixel-town-app'/'assets'

def build(sync=True):
 characters=[];pets=[]
 for category in ('characters','pets','codexmini'):
  source=ROOT/category
  for folder in sorted(p for p in source.iterdir() if p.is_dir()):
   profile=folder/'profile.json'
   if not profile.exists(): continue
   p=json.loads(profile.read_text())
   manifest=folder/'animation.json'
   if not manifest.exists(): raise ValueError(f'Missing runtime animation manifest: {folder.name}')
   p['assetFolder']=category+'/'+folder.name
   p['profileMd']=(folder/'profile.md').read_text()
   (pets if category=='pets' else characters).append(p)
   if sync:
    # Retain source GIFs and metadata in the source pack. Game only needs PNG
    # atlases and original/avatar PNGs, never duplicates all individual frames.
    dest=APP/category/folder.name;dest.mkdir(parents=True,exist_ok=True)
    for file in folder.iterdir():
     if file.is_file() and file.suffix in ('.png','.json','.md'):
      shutil.copy2(file,dest/file.name)
    clips=json.loads(manifest.read_text())['animations']
    for clip in clips.values():
     path=Path(clip['atlas']);target=dest/path;target.parent.mkdir(parents=True,exist_ok=True)
     shutil.copy2(folder/path,target)
 roster=dict(version=1,characters=characters,pets=pets)
 (ROOT/'roster.json').write_text(json.dumps(roster,ensure_ascii=False,indent=2)+'\n')
 if sync:
  APP.mkdir(exist_ok=True)
  shutil.copy2(ROOT/'roster.json',APP/'roster.json')
 print(f'Published {len(characters)} residents (including codexmini), {len(pets)} animals')
 return roster

if __name__=='__main__':build()
