#!/usr/bin/env python3
"""Extract original residents' missing back-walk keys from their existing atlas.

No generated or redrawn artwork: reuse zero-based phases 2/10, with a fixed
nearest-neighbour registration to frame_10. Never trim/recenter steps separately.
The original 16-frame walk_up atlas and GIF remain byte-for-byte unchanged.
"""
from pathlib import Path
import hashlib
import json
import shutil
import numpy as np
from PIL import Image, ImageDraw
from animate_existing import clean_source, normalize, palette_frames, save_atlas, NECK

ROOT = Path(__file__).resolve().parents[1]
PHASES = (2, 10)
SEQUENCE = (10, 11, 10, 12)
KEY_MS = 160

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def folders():
    return sorted(p for p in (ROOT / 'characters').iterdir()
                  if p.is_dir() and p.name[:2].isdigit() and 1 <= int(p.name[:2]) <= 20)

def human_approval(folder):
    record = ROOT / 'validation/back-walk-approval.json'
    if record.exists():
        approval = json.loads(record.read_text())
        approved = approval.get('roles', {}).get(folder.name, {})
        hashes = approved.get('assetSHA256', {})
        if hashes and all((folder / name).exists() and sha(folder / name) == value
                          for name, value in hashes.items()):
            return 'approved by user on ' + approval['date']
    return 'pending visual review; see validation/back-walk-completion.md'

def registered_step(tile, folder):
    # Undo the atlas's common 210px normalization using one transform for both
    # phases. Standing key is preserved; hair, clothes and accessories use only
    # existing RGBA samples. Alpha is copied, never interpolated/composited.
    original_box = clean_source(folder / 'frame_10.png').getbbox()
    left, top, width, height = normalize(folder / 'frame_10.png', 'walk_up')[1]
    # normalize() pastes at the floored x coordinate, not its half-pixel box x.
    left = (256 - width) // 2
    x0, y0, x1, y1 = original_box
    yy, xx = np.mgrid[:256, :256]
    sx = np.floor(left + (xx - x0 + .5) * width / (x1 - x0)).astype(int)
    sy = np.floor(top + (yy - y0 + .5) * height / (y1 - y0)).astype(int)
    valid = (sx >= 0) & (sx < 256) & (sy >= 0) & (sy < 256)
    src = np.asarray(tile)
    arr = np.zeros((256, 256, 4), dtype=np.uint8)
    arr[valid] = src[sy[valid], sx[valid]]
    # Keep the original head/hat strip as-is. Existing atlas cleanup loses the
    # disconnected top outline of white chef hats; the standing key retains it.
    # This is rectangle reuse, not a redraw or a new head template.
    head_end = round(y0 + (y1 - y0) * NECK[int(folder.name[:2]) - 1] - 6)
    original = np.asarray(Image.open(folder / 'frame_10.png').convert('RGBA'))
    arr[:head_end] = original[:head_end]
    arr[arr[:, :, 3] == 0] = 0
    return Image.fromarray(arr)

def complete_folder(folder):
    atlas_path = folder / 'animations/walk_up.png'
    atlas = Image.open(atlas_path)
    if atlas.mode != 'RGBA' or atlas.size != (4096, 256):
        raise ValueError(f'{folder.name}: unsupported existing walk_up atlas')
    if set(np.unique(np.asarray(atlas)[:, :, 3])) != {0, 255}:
        raise ValueError(f'{folder.name}: atlas must have binary alpha')
    legacy = folder / 'legacy_actions'
    legacy.mkdir(exist_ok=True)
    # Refuse partial/ambiguous backups; repeated runs never overwrite originals.
    existing = [(legacy / f'frame_{n}.png').exists() for n in (11, 12)]
    if any(existing) and not all(existing):
        raise ValueError(f'{folder.name}: incomplete legacy backup')
    if not any(existing):
        for n in (11, 12):
            shutil.copy2(folder / f'frame_{n}.png', legacy / f'frame_{n}.png')
    for number, phase in zip((11, 12), PHASES):
        tile = atlas.crop((phase * 256, 0, (phase + 1) * 256, 256))
        registered_step(tile, folder).save(folder / f'frame_{number}.png')
    keys = [Image.open(folder / f'frame_{n:02d}.png').convert('RGBA') for n in SEQUENCE]
    save_atlas(keys, folder / 'animations/back_walk_keys.png')
    gifs = palette_frames(keys)
    gifs[0].save(folder / 'animations/back_walk_keys.gif', save_all=True,
                 append_images=gifs[1:], duration=KEY_MS, loop=0,
                 transparency=0, disposal=2, optimize=False)
    for name in ('animation.json', 'animation-manifest.json'):
        path = folder / name
        mf = json.loads(path.read_text())
        mf['animations']['cheer']['source'] = 'legacy_actions/frame_11.png'
        mf['sourceSHA256'].pop('frame_11.png', None)
        for n in (11, 12):
            key = f'legacy_actions/frame_{n}.png'
            mf['sourceSHA256'][key] = sha(folder / key)
            key = f'frame_{n}.png'
            mf['sourceSHA256'][key] = sha(folder / key)
        mf['animations']['walk_up'].update({
            'keyframes': [f'frame_{n:02d}.png' for n in (10, 11, 12)],
            'keyframeAtlas': 'animations/back_walk_keys.png',
            'keyframeGif': 'animations/back_walk_keys.gif',
            'keyframeSequence': list(SEQUENCE), 'keyframeMs': KEY_MS,
        })
        mf['backWalkCompletion'] = {
            'version': 1, 'scope': 'original characters 01..20',
            'method': 'existing walk_up atlas extraction; fixed nearest-neighbour registration; original head strip retained',
            'zeroBasedSourcePhases': list(PHASES),
            'sourceAtlasSHA256': sha(atlas_path),
            'legacyBackup': 'legacy_actions',
            'standingFramePreserved': True,
            'continuousWalkUpPreserved': True,
            'originalHeadStripPreserved': True,
            'humanApproval': human_approval(folder),
        }
        path.write_text(json.dumps(mf, ensure_ascii=False, indent=2) + '\n')

def main():
    selected = folders()
    if len(selected) != 20:
        raise ValueError(f'Expected the handoff\'s 20 roles, got {len(selected)}')
    dest = ROOT / 'validation'
    baseline = dest / 'back-walk-baseline.json'
    if not baseline.exists():
        files = [p for folder in selected for p in folder.glob('frame_*.png')]
        files += [p for folder in selected for p in (folder / 'animations').iterdir() if p.is_file()]
        files += list((ROOT / 'raw_v2').glob('*.png'))
        files += [ROOT / 'process_spritesheet.py']
        baseline.write_text(json.dumps({p.relative_to(ROOT).as_posix(): sha(p) for p in files}, indent=2) + '\n')
    for folder in selected:
        complete_folder(folder)
        print(folder.name + ': frame_11/12 extracted; legacy actions retained')
    for page in range(4):
        board = Image.new('RGB', (4 * 256, 5 * 290), '#e1e6df')
        draw = ImageDraw.Draw(board)
        for row, folder in enumerate(selected[page * 5:page * 5 + 5]):
            for col, n in enumerate((10, 11, 10, 12)):
                tile = Image.open(folder / f'frame_{n:02d}.png')
                board.paste(tile, (col * 256, row * 290), tile)
                draw.text((col * 256 + 4, row * 290 + 259), f'{folder.name} / {n:02d}', fill='#20382a')
        board.save(dest / f'back-walk-keys-page-{page+1}.png')

if __name__ == '__main__':
    main()
