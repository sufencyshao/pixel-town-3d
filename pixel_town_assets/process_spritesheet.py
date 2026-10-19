"""
批量角色处理 pipeline：
  sprite_sheet.png (2048x2048, 4x4 grid, 白底)
    -> 透明化（flood fill 白底+灰影）
    -> 切成 16 块 512x512
    -> trim 透明边
    -> 居中放到标准画布 256x256
    -> 保存到 characters/<role_name>/frame_01.png ... frame_16.png

用法：
  python3 process_spritesheet.py <raw_sheet.png> <role_folder_name>
"""
import sys, os
from collections import deque
from PIL import Image
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CHARS_DIR = os.path.join(HERE, "characters")


def to_transparent(rgba_arr, white_thresh=235, gray_thresh=110, min_shadow_area=5000):
    arr = rgba_arr.copy()
    h, w, _ = arr.shape
    rgb = arr[:, :, :3].astype(int)
    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    maxc = np.maximum(np.maximum(r,g),b)
    minc = np.minimum(np.minimum(r,g),b)
    near_white = (r>=white_thresh)&(g>=white_thresh)&(b>=white_thresh)
    near_gray = (maxc-minc<25)&(maxc>=gray_thresh)&(maxc<white_thresh)
    bg = near_white | near_gray

    visited = np.zeros((h,w), dtype=bool)
    q = deque()
    for x in range(w):
        for y in (0,h-1):
            if bg[y,x] and not visited[y,x]:
                visited[y,x]=True; q.append((y,x))
    for y in range(h):
        for x in (0,w-1):
            if bg[y,x] and not visited[y,x]:
                visited[y,x]=True; q.append((y,x))
    while q:
        y,x = q.popleft()
        for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
            ny,nx = y+dy,x+dx
            if 0<=ny<h and 0<=nx<w and not visited[ny,nx] and bg[ny,nx]:
                visited[ny,nx]=True; q.append((ny,nx))
    trans = visited.copy()
    leftover = near_gray & ~visited
    seen = np.zeros((h,w), dtype=bool)
    for y in range(h):
        for x in range(w):
            if leftover[y,x] and not seen[y,x]:
                block=[]
                q2=deque([(y,x)]); seen[y,x]=True
                while q2:
                    cy,cx=q2.popleft(); block.append((cy,cx))
                    for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        ny,nx=cy+dy,cx+dx
                        if 0<=ny<h and 0<=nx<w and not seen[ny,nx] and leftover[ny,nx]:
                            seen[ny,nx]=True; q2.append((ny,nx))
                if len(block)<min_shadow_area:
                    for by,bx in block: trans[by,bx]=True
    arr[trans,3]=0
    return arr


def trim_and_center(img, canvas=256):
    """trim 透明边，居中放到 canvas x canvas 的透明画布上"""
    bbox = img.getbbox()
    if bbox is None:
        return Image.new("RGBA", (canvas,canvas), (0,0,0,0))
    cropped = img.crop(bbox)
    # 等比缩放到画布内（留 10% 边距）
    max_side = int(canvas * 0.9)
    w, h = cropped.size
    scale = min(max_side/w, max_side/h)
    new_size = (max(1,int(w*scale)), max(1,int(h*scale)))
    cropped = cropped.resize(new_size, Image.NEAREST)
    out = Image.new("RGBA", (canvas,canvas), (0,0,0,0))
    out.paste(cropped, ((canvas-new_size[0])//2, (canvas-new_size[1])//2), cropped)
    return out


def process(raw_path, role_name):
    img = Image.open(raw_path).convert("RGBA")
    arr = np.array(img)
    h, w, _ = arr.shape
    # 强制 4x4 网格
    cell = h // 4
    arr_t = to_transparent(arr)
    out_dir = os.path.join(CHARS_DIR, role_name)
    os.makedirs(out_dir, exist_ok=True)
    idx = 1
    for row in range(4):
        for col in range(4):
            cell_arr = arr_t[row*cell:(row+1)*cell, col*cell:(col+1)*cell]
            cell_img = Image.fromarray(cell_arr)
            final = trim_and_center(cell_img, canvas=256)
            final.save(os.path.join(out_dir, f"frame_{idx:02d}.png"))
            idx += 1
    print(f"[ok] {role_name}: 16 frames -> {out_dir}")


if __name__ == "__main__":
    raw = sys.argv[1]
    role = sys.argv[2]
    process(raw, role)
