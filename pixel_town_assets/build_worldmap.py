"""
小镇总地图 v3 - 规整网格版
- 建筑严格沿道路两侧排列
- 道路带人行道细节
- 20栋住宅
"""
from PIL import Image, ImageDraw, ImageOps
import os, random

BASE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(BASE, "buildings")
D = os.path.join(BASE, "decorations")

W, H = 3000, 2200
canvas = Image.new("RGBA", (W, H), (120, 180, 90, 255))
random.seed(42)
d = ImageDraw.Draw(canvas)

# 草地斑驳
for _ in range(1500):
    x, y = random.randint(0, W-20), random.randint(0, H-20)
    s = random.randint(-12, 12)
    d.rectangle([x, y, x+18, y+18], fill=(120+s, 180+s, 90+s, 255))

# ===== 道路系统 =====
ROAD = (194, 164, 106, 255)        # 主路土黄
SIDEWALK = (210, 200, 180, 255)   # 人行道浅灰
ROAD_W = 70   # 主路宽
SW_W = 18     # 人行道宽

# 横路（y坐标中心）
h_roads = [400, 950, 1600]
# 纵路（x坐标中心）
v_roads = [750, 1500, 2250]

# 画人行道（先画，再画主路）
for ry in h_roads:
    d.rectangle([0, ry-ROAD_W//2-SW_W, W, ry-ROAD_W//2], fill=SIDEWALK)
    d.rectangle([0, ry+ROAD_W//2, W, ry+ROAD_W//2+SW_W], fill=SIDEWALK)
for rx in v_roads:
    d.rectangle([rx-ROAD_W//2-SW_W, 0, rx-ROAD_W//2, H], fill=SIDEWALK)
    d.rectangle([rx+ROAD_W//2, 0, rx+ROAD_W//2+SW_W, H], fill=SIDEWALK)

# 画主路
for ry in h_roads:
    d.rectangle([0, ry-ROAD_W//2, W, ry+ROAD_W//2], fill=ROAD)
for rx in v_roads:
    d.rectangle([rx-ROAD_W//2, 0, rx+ROAD_W//2, H], fill=ROAD)

# 河流（左下角）
d.polygon([(0, 1700), (500, 1700), (600, 1900), (400, 2200), (0, 2200)], fill=(80, 140, 200, 255))

def load_trim(path, target_h=None):
    im = Image.open(path).convert("RGBA")
    bbox = im.getbbox()
    im = im.crop(bbox)
    if target_h:
        w, h = im.size
        im = im.resize((int(w*target_h/h), target_h), Image.NEAREST)
    return im

def bldg(name, h=220): return load_trim(os.path.join(B, name), h)
def deco(name, h=120): return load_trim(os.path.join(D, name), h)

items = []

# ===== 建筑严格沿道路排列 =====
# 北横路(400)北侧：商店街5间（x沿纵路间隔）
shops = [
    ("02_cafe.png",      900),
    ("03_bakery.png",   1150),
    ("04_bookstore.png",1400),
    ("05_clinic.png",   1700),
    ("06_postoffice.png",1950),
]
for f, x in shops:
    items.append((bldg(f, 220), x, 340))  # 建筑底部在路北边

# 北横路南侧：市政厅(左) + 北住宅4栋
items.append((bldg("01_townhall.png", 300), 400, 500))
items.append((bldg("20_house_lavender.png", 190), 900, 500))
items.append((ImageOps.mirror(bldg("22_house_stone.png", 190)), 1150, 500))
items.append((bldg("25_house_teal.png", 190),    1400, 500))
items.append((ImageOps.mirror(bldg("24_house_cream.png", 190)),1700, 500))

# 中横路(950)北侧：左住宅区第一排(沿纵路1左边) + 商业区
items.append((bldg("09_house_yellow.png", 190), 250, 880))
items.append((bldg("10_house_blue.png", 190),   500, 880))
# 商业区在纵路2右边
items.append((bldg("13_supermarket.png", 240), 1800, 880))
items.append((bldg("14_hospital.png", 260),   2100, 880))
items.append((bldg("16_inn.png", 240),        2400, 880))

# 中横路南侧：左住宅区第二排 + 餐饮街
items.append((bldg("11_house_pink.png", 190),  250, 1050))
items.append((bldg("19_house_mint.png", 190),  500, 1050))
items.append((bldg("15_restaurant.png", 220), 1800, 1050))
items.append((bldg("17_barbershop.png", 200),2100, 1050))
items.append((bldg("18_bar.png", 220),       2400, 1050))

# 南横路(1600)北侧：左住宅区第三排 + 右侧散放住宅
items.append((bldg("21_house_peach.png", 190), 250, 1520))
items.append((bldg("26_house_tan.png", 190),  500, 1520))
items.append((bldg("23_house_twostory.png",200), 1800, 1520))
items.append((ImageOps.mirror(bldg("10_house_blue.png", 190)), 2100, 1520))
items.append((ImageOps.mirror(bldg("11_house_pink.png", 190)),  2400, 1520))
items.append((ImageOps.mirror(bldg("21_house_peach.png", 190)),2650, 1520))

# 南横路南侧：学校(左)/谷仓(中)/教堂(右)
items.append((bldg("07_school.png", 240), 400, 1750))
items.append((bldg("12_barn.png", 240),  1500, 1750))
items.append((bldg("08_church.png", 240),2400, 1750))

# ===== 装饰 =====
# 喷泉在市政厅前广场
items.append((deco("fountain.png", 120), 400, 620))
items.append((deco("flowerbed.png", 90), 250, 620))
items.append((deco("flowerbed.png", 90), 550, 620))

# 树：路边间隔排列
tree = deco("tree.png", 110)
tree_pos = [
    (100, 200), (2900, 200), (100, 700), (2900, 700),
    (100, 1300), (2900, 1300), (100, 2000), (2900, 2000),
    (1000, 650), (1300, 650), (1900, 650),
    (1000, 1300), (1300, 1300), (1900, 1300),
    (900, 1850), (2000, 1850),
]
for tx, ty in tree_pos:
    items.append((tree.copy(), tx, ty))

# 路灯：沿路
lamp = deco("lamp.png", 100)
lamp_pos = [
    (850, 470), (1100, 470), (1350, 470), (1600, 470), (1850, 470),
    (850, 1020), (1100, 1020), (1600, 1020),
    (850, 1570), (1100, 1570), (1600, 1570), (1900, 1570),
]
for lx, ly in lamp_pos:
    items.append((lamp.copy(), lx, ly))

# 长椅
bench = deco("bench.png", 80)
items.append((bench.copy(), 300, 680))
items.append((bench.copy(), 500, 680))
items.append((bench.copy(), 1300, 1900))

# 木桥（河上）
items.append((deco("bridge.png", 160), 350, 1750))

# 花坛
fb = deco("flowerbed.png", 90)
items.append((fb.copy(), 200, 1900))
items.append((fb.copy(), 1700, 1900))
items.append((fb.copy(), 2600, 1900))

# 按y排序
items.sort(key=lambda it: it[2])
for im, x, y in items:
    canvas.paste(im, (x - im.size[0]//2, y - im.size[1]), im)

out = os.path.join(BASE, "dioramas", "00_town_worldmap.png")
canvas.convert("RGB").save(out)
print("saved", out)
