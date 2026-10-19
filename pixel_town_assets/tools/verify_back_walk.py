#!/usr/bin/env python3
"""Validate repaired keys, legacy recovery, unchanged artwork and provenance."""
import json
import numpy as np
from PIL import Image
from complete_back_walk import ROOT, folders, sha, registered_step, PHASES, SEQUENCE, KEY_MS

def main():
    errors = []
    rows = []
    baseline = json.loads((ROOT / 'validation/back-walk-baseline.json').read_text())
    changed = []
    for name, old_sha in baseline.items():
        path = ROOT / name
        if not path.exists() or sha(path) != old_sha:
            changed.append(name)
            if path.name not in ('frame_11.png', 'frame_12.png') or path.parent.parent.name != 'characters':
                errors.append(f'unexpected source mutation: {name}')
    for folder in folders():
        role = folder.name
        source = Image.open(folder / 'frame_10.png').convert('RGBA')
        orig = np.asarray(source)
        palette = set(map(tuple, orig[orig[:, :, 3] > 0]))
        atlas = Image.open(folder / 'animations/walk_up.png')
        for n in (11, 12):
            old_name = f'characters/{role}/frame_{n}.png'
            if sha(folder / f'legacy_actions/frame_{n}.png') != baseline[old_name]:
                errors.append(f'{role}: legacy backup {n} changed')
        steps = []
        for n, phase in zip((11, 12), PHASES):
            path = folder / f'frame_{n}.png'
            tile = Image.open(path)
            arr = np.asarray(tile)
            steps.append(arr)
            if tile.mode != 'RGBA' or tile.size != (256, 256):
                errors.append(f'{role}/{n}: invalid mode/size')
            if set(np.unique(arr[:, :, 3])) != {0, 255}:
                errors.append(f'{role}/{n}: alpha not binary')
            if set(map(tuple, arr[arr[:, :, 3] > 0])) - palette:
                errors.append(f'{role}/{n}: colors absent from original back pose')
            if any(np.any(edge) for edge in (arr[0, :, 3], arr[-1, :, 3], arr[:, 0, 3], arr[:, -1, 3])):
                errors.append(f'{role}/{n}: canvas clipping')
            expected = registered_step(atlas.crop((phase * 256, 0, (phase + 1) * 256, 256)), folder)
            if not np.array_equal(arr, np.asarray(expected)):
                errors.append(f'{role}/{n}: provenance reconstruction failed')
        if np.array_equal(steps[0], steps[1]) or any(np.array_equal(s, orig) for s in steps):
            errors.append(f'{role}: repeated standing/step frame')
        mf = json.loads((folder / 'animation.json').read_text())
        if mf != json.loads((folder / 'animation-manifest.json').read_text()):
            errors.append(f'{role}: manifests disagree')
        for path, value in mf['sourceSHA256'].items():
            if sha(folder / path) != value:
                errors.append(f'{role}: wrong SHA for {path}')
        if mf['animations']['cheer']['source'] != 'legacy_actions/frame_11.png':
            errors.append(f'{role}: cheer points to walking pose')
        if mf['backWalkCompletion']['sourceAtlasSHA256'] != sha(folder / 'animations/walk_up.png'):
            errors.append(f'{role}: atlas provenance hash mismatch')
        keys = Image.open(folder / 'animations/back_walk_keys.png')
        if keys.mode != 'RGBA' or keys.size != (1024, 256):
            errors.append(f'{role}: invalid keyframe atlas')
        for i, n in enumerate(SEQUENCE):
            expected = Image.open(folder / f'frame_{n:02d}.png').convert('RGBA')
            if keys.crop((i*256, 0, (i+1)*256, 256)).tobytes() != expected.tobytes():
                errors.append(f'{role}: keyframe sequence mismatch')
        with Image.open(folder / 'animations/back_walk_keys.gif') as gif:
            duration = 0
            if gif.n_frames != 4 or gif.info.get('loop') != 0:
                errors.append(f'{role}: GIF frame/loop mismatch')
            for i in range(gif.n_frames):
                gif.seek(i)
                duration += gif.info.get('duration', 0)
                if gif.convert('RGBA').getpixel((0, 0))[3] != 0:
                    errors.append(f'{role}: GIF background not transparent')
            if duration != 4 * KEY_MS:
                errors.append(f'{role}: GIF timing mismatch')
        frames = [np.asarray(Image.open(folder / f'frame_{n:02d}.png')) for n in SEQUENCE]
        diffs = [int(np.count_nonzero(np.any(frames[i] != frames[(i+1)%4], axis=2))) for i in range(4)]
        if diffs[-1] > max(diffs[:-1]):
            errors.append(f'{role}: loop wrap exceeds internal transition')
        rows.append({'role': role, 'alpha': [0, 255], 'frames': [10, 11, 12],
                     'sourcePhases': list(PHASES), 'newOpaqueColors': 0,
                     'changedPixelsPerLoopTransition': diffs, 'gifDurationMs': duration})
    if len(changed) != 40:
        errors.append(f'expected 40 replacements, got {len(changed)}')
    result = {'roles': len(rows), 'replacedFrames': len(changed),
              'errors': errors, 'changedOriginalFiles': changed, 'checks': rows}
    (ROOT / 'validation/back-walk-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('roles', 'replacedFrames', 'errors')}, ensure_ascii=False, indent=2))
    return bool(errors)

if __name__ == '__main__':
    raise SystemExit(main())
