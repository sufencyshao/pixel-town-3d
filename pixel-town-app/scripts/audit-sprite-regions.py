"""Audit every shipped frame for disconnected fragments at a sheet-cell edge.

PNG files stay untouched. The reviewed regions drive rendering masks only.
The central foreground and small gaps inside a person are always retained.
"""
from pathlib import Path
import json, hashlib
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/validation/day-night-v0.6.0'
REVIEWED = {
    'characters/16_librarian_female': {'frame_06.png': [0, 0, 143, 256]},
    'characters/01_hero_male': {f'frame_{n:02}.png': [0, 23, 256, 256] for n in (5, 6, 7, 8)},
    'characters/14_teacher_female': {f'frame_{n:02}.png': [0, 25, 256, 256] for n in (5, 6, 7)},
    'characters/09_gardener_male': {'frame_16.png': [0, 0, 208, 256]},
}

def spans(occupied):
    indices = np.flatnonzero(occupied)
    if not len(indices):
        return []
    groups = np.split(indices, np.flatnonzero(np.diff(indices) >= 13) + 1)
    return [(int(g[0]), int(g[-1]) + 1) for g in groups]

def region(image):
    a = np.asarray(image)[:, :, 3]
    columns = a.astype(bool).sum(axis=0)
    groups = spans(columns > 0)
    if not groups:
        return None
    primary = max(groups, key=lambda g: int(columns[g[0]:g[1]].sum()))
    area = int(columns[primary[0]:primary[1]].sum())
    extras = [g for g in groups if g != primary and columns[g[0]:g[1]].sum() < area * .40]
    left, right = 0, image.width
    for g in extras:
        if g[1] <= primary[0]:
            left = max(left, (g[1] + primary[0]) // 2)
        elif g[0] >= primary[1]:
            right = min(right, (primary[1] + g[0]) // 2)
    # Thin remnants of the previous grid row also occur above some base heads.
    rows = (a[:, left:right] > 0).sum(axis=1)
    row_groups = spans(rows > 0)
    top, bottom = 0, image.height
    if row_groups:
        main = max(row_groups, key=lambda g: int(rows[g[0]:g[1]].sum()))
        for g in row_groups:
            if g != main and g[1] <= main[0] and g[1] <= 38 and rows[g[0]:g[1]].sum() < rows[main[0]:main[1]].sum() * .15:
                top = max(top, (g[1] + main[0]) // 2)
    if [left, top, right, bottom] == [0, 0, image.width, image.height]:
        return None
    return [left, top, right, bottom]

def build():
    OUT.mkdir(parents=True, exist_ok=True)
    roster = json.loads((ROOT / 'assets/roster.json').read_text())
    regions, findings, checks = {}, [], dict(entities=0, frames=0, baseFrames=0, animationFrames=0)
    cards = []
    for entity in roster['characters'] + roster['pets']:
        folder = entity['assetFolder']; path = ROOT / 'assets' / folder
        animation = json.loads((path / 'animation.json').read_text())
        checks['entities'] += 1; record = dict(frames={}, clips={}, frameOffsets={}, clipOffsets={}, hashes={})
        files = [(f.name, 1, None) for f in sorted(path.glob('frame_*.png'))]
        files += [(c['atlas'], c['frames'], name) for name, c in animation['animations'].items()]
        for relative, count, clip in files:
            sheet = Image.open(path / relative).convert('RGBA')
            fw, fh = (animation['frameWidth'], animation['frameHeight']) if clip else sheet.size
            bounds = []
            for n in range(count):
                tile = sheet.crop((n * fw, 0, (n + 1) * fw, fh))
                checks['frames'] += 1; checks['animationFrames' if clip else 'baseFrames'] += 1
                box = region(tile); bounds.append(box)
                # These exceptions were inspected against actual source pixels.
                reviewed = REVIEWED.get(folder, {}).get(relative)
                if reviewed:
                    old = box or [0, 0, fw, fh]
                    box = [max(old[0],reviewed[0]),max(old[1],reviewed[1]),min(old[2],reviewed[2]),min(old[3],reviewed[3])];bounds[-1] = box
                if box:
                    a = np.asarray(tile)[:, :, 3]
                    removed = int((a > 0).sum() - (a[box[1]:box[3], box[0]:box[2]] > 0).sum())
                    findings.append(dict(folder=folder, name=entity['name'], file=relative, frame=n, bounds=box, removedPixels=removed))
                    if n == 0 or not clip:
                        cards.append((f"{folder.split('/')[-1]} / {clip or relative}", tile, box))
            if any(bounds):
                record['hashes'][relative] = hashlib.sha256((path / relative).read_bytes()).hexdigest()
                if clip:
                    record['clips'][clip] = bounds
                    box = bounds[0]
                    if box and (box[0] or box[2] != fw):
                        tile = sheet.crop((0, 0, fw, fh)); alpha = np.asarray(tile)[:, :, 3].copy()
                        alpha[:, :box[0]] = 0; alpha[:, box[2]:] = 0
                        xs = np.flatnonzero((alpha > 0).any(axis=0))
                        record['clipOffsets'][clip] = int(round(fw / 2 - (xs[0] + xs[-1]) / 2))
                else:
                    key = str(int(relative[6:8])); record['frames'][key] = bounds[0]
                    box = bounds[0]
                    if box[0] or box[2] != fw:
                        tile = sheet; alpha = np.asarray(tile)[:, :, 3].copy()
                        alpha[:, :box[0]] = 0; alpha[:, box[2]:] = 0
                        xs = np.flatnonzero((alpha > 0).any(axis=0))
                        record['frameOffsets'][key] = int(round(fw / 2 - (xs[0] + xs[-1]) / 2))
        if record['frames'] or record['clips']:
            regions[folder] = record
    output = dict(version=1, technique='reviewed edge-fragment rendering regions', entries=regions)
    (ROOT / 'assets/sprite-regions.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    report = dict(checks=checks, affectedEntities=len(regions), affectedFrames=len(findings), findings=findings)
    (OUT / 'sprite-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    for page in range((len(cards) + 19) // 20):
        montage = Image.new('RGB', (5 * 256, 4 * 282), '#e3ebe0'); draw = ImageDraw.Draw(montage)
        for i, (label, tile, box) in enumerate(cards[page * 20:(page + 1) * 20]):
            x, y = i % 5 * 256, i // 5 * 282
            draw.text((x + 4, y + 3), label, fill='black'); montage.paste(tile, (x, y + 26), tile)
            draw.rectangle((x + box[0], y + 26, x + box[2] - 1, y + 281), outline='#ed5860', width=1)
        montage.save(OUT / f'sprite-audit-{page + 1:02}.png')
    print(json.dumps(dict(checks=checks, affectedEntities=len(regions), affectedFrames=len(findings), reviewPages=(len(cards) + 19) // 20, characters=list(regions)), ensure_ascii=False))

if __name__ == '__main__':
    build()
