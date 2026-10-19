"""Independent 8-neighbour component audit, including every animation phase."""
import json, hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/validation/day-night-v0.6.0'

def components(mask):
    nodes, previous = [], []
    def find(i):
        while nodes[i][0] != i:
            nodes[i][0] = nodes[nodes[i][0]][0]; i = nodes[i][0]
        return i
    for y, row in enumerate(mask):
        edges = np.flatnonzero(np.diff(np.r_[False, row, False].astype(np.int8)))
        current = []
        for left, right in zip(edges[::2], edges[1::2]):
            i = len(nodes); nodes.append([i, int(right-left), int(left), y, int(right), y+1]); current.append((int(left), int(right), i))
            for pl, pr, pi in previous:
                if pr < left or pl > right:
                    continue
                a, b = find(i), find(pi)
                if a != b:
                    nodes[b][0] = a
        previous = current
    merged = {}
    for i, (_, size, left, top, right, bottom) in enumerate(nodes):
        p = find(i)
        if p not in merged: merged[p] = [0, left, top, right, bottom]
        item = merged[p]; item[0] += size; item[1] = min(item[1], left); item[2] = min(item[2], top); item[3] = max(item[3], right); item[4] = max(item[4], bottom)
    return sorted(merged.values(), reverse=True)

def main():
    roster = json.loads((ROOT / 'assets/roster.json').read_text())
    regions = json.loads((ROOT / 'assets/sprite-regions.json').read_text())['entries']
    findings, cache, cards = [], {}, []; phases = 0
    for entity in roster['characters'] + roster['pets']:
        folder = entity['assetFolder']; path = ROOT / 'assets' / folder
        animation = json.loads((path / 'animation.json').read_text()); rects = regions.get(folder, {})
        files = [(f.name, 1, None) for f in sorted(path.glob('frame_*.png'))]
        files += [(c['atlas'], c['frames'], name) for name, c in animation['animations'].items()]
        for relative, count, clip in files:
            sheet = Image.open(path / relative).convert('RGBA'); fw, fh = (animation['frameWidth'], animation['frameHeight']) if clip else sheet.size
            for n in range(count):
                phases += 1; tile = sheet.crop((n*fw, 0, (n+1)*fw, fh)); mask = np.asarray(tile)[:, :, 3] > 0
                box = rects.get('clips', {}).get(clip, [None]*count)[n] if clip else rects.get('frames', {}).get(str(int(relative[6:8])))
                if box:
                    mask = mask.copy(); mask[:box[1]] = False; mask[box[3]:] = False; mask[:, :box[0]] = False; mask[:, box[2]:] = False
                digest = hashlib.sha256(mask.tobytes()).digest()
                if digest not in cache: cache[digest] = components(mask)
                groups = cache[digest]
                if not groups: continue
                area, left, top, right, bottom = groups[0]
                suspects = []
                for size, l, t, r, b in groups[1:]:
                    gap = max(left-r, l-right, top-b, t-bottom, 0)
                    if size >= 4 and size < area*.35 and gap >= 12 and (l < fw*.25 or r > fw*.75 or b < fh*.25):
                        suspects.append(dict(area=size, bounds=[l,t,r,b], gap=gap))
                if suspects:
                    findings.append(dict(folder=folder,file=relative,frame=n,components=suspects))
                    cards.append((folder.split('/')[-1]+'/'+(clip or relative)+f' [{n}]',tile,suspects))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'component-audit.json').write_text(json.dumps(dict(frames=phases, uniqueMasks=len(cache), suspiciousFrames=len(findings), findings=findings),ensure_ascii=False,indent=2)+'\n')
    for page in range((len(cards)+19)//20):
        image=Image.new('RGB',(1280,1128),'#d2dcd0');d=ImageDraw.Draw(image)
        for i,(label,tile,suspects) in enumerate(cards[page*20:(page+1)*20]):
            x=i%5*256;y=i//5*282;d.text((x+3,y+3),label,fill='black');image.paste(tile,(x,y+26),tile)
            for s in suspects:
                l,t,r,b=s['bounds'];d.rectangle((x+l,y+26+t,x+r,y+26+b),outline='red',width=2)
        image.save(OUT/f'component-audit-{page+1:02}.png')
    print(json.dumps(dict(frames=phases,uniqueMasks=len(cache),suspiciousFrames=len(findings),reviewPages=(len(cards)+19)//20)))

if __name__ == '__main__': main()
