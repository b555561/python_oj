# -*- coding: utf-8 -*-
"""第 20 轮专项测试：菜园 → 农场（自由建造的 3D 小农场）

验收点：
  1. /farm 顶部是农场：左边配件侧边栏 + 右边大块 3D 地皮（等距 CSS 3D，无第三方库）
  2. 配件种类齐全：草皮 / 农作物 / 蔬菜 / 水果 / 动物 / 栅栏 / 房屋 / 小溪 / 树木 …
  3. 能量买配件：扣能量 → 进背包 → 摆到地皮 → 能搬 → 能拆（拆了退回背包）
  4. **没有固定建造任务、没有强制升级路线**：
     - 任意配件都能直接买（不要求先买别的）
     - 任意空格都能摆（不分区、不按顺序）
     - 页面文案里没有"任务 / 必须 / 达到 X 级 / 完成…才能"这类强制引导
  5. 原有菜地玩法（翻地 / 播种 / 收获 / 菜篮）不受影响
"""
import io
import os
import re
import time
import requests

BASE = os.environ.get("PYOJ_BASE", "http://127.0.0.1:8001")
OK = BAD = 0


def check(name, cond, extra=""):
    global OK, BAD
    if cond:
        OK += 1
        print("  ✓ " + name)
    else:
        BAD += 1
        print("  ✗ " + name + ("  << " + str(extra) if extra else ""))


def read(p):
    return io.open(p, encoding="utf-8").read()


sess = requests.Session()
uname = "r20t" + str(int(time.time()) % 100000)
sess.post(BASE + "/register",
          data={"username": uname, "password": "test123456", "nickname": "r20t"},
          allow_redirects=False, timeout=15)
sess.get(BASE + "/", timeout=15)
farm = sess.get(BASE + "/farm", timeout=15).text

src_farm = read("templates/farm.html")
src_yard = read("core/farmyard.py")
css = read("static/css/farmyard.css")
js = read("static/js/farmyard.js")

print("\n=== 1. 页面结构：侧边栏 + 大块地皮 ===")
check("农场页能打开", "yard-stage" in farm)
check("左侧是配件侧边栏", "yard-side" in farm and "农场配件铺" in farm)
check("右侧是地皮主体", "yard-main" in farm and "yard-view" in farm)
check("侧边栏在左、地皮在右（DOM 顺序）",
      0 <= farm.find("yard-side") < farm.find("yard-main"))
check("有分类切换", "yardCats" in farm)
check("有配件列表容器", "yardItems" in farm)
check("有工具条（拆除 / 缩放 / 转视角 / 清空）",
      all(k in farm for k in ("yardErase", "yardZin", "yardZout", "yardRot", "yardClear")))
check("有底部统计条", "yardFoot" in farm)

print("\n=== 2. 排版：地皮占大部分，配件收在侧边 ===")
_side = css.split(".yard-side {")[1].split("}")[0]
_main = css.split(".yard-main {")[1].split("}")[0]
check("侧边栏固定窄宽度", re.search(r"flex:\s*0\s+0\s+2\d\dpx", _side) is not None, _side)
check("地皮区域自适应撑满", "flex: 1 1 auto" in _main, _main)
check("地皮视口高度足够（>=500px）", re.search(r"height:\s*[5-9]\d\dpx", css) is not None)
check("窄屏时侧边栏放到下面", "@media (max-width: 900px)" in css)

print("\n=== 3. 3D：等距 CSS 3D，没有第三方库 ===")
check("舞台用 rotateX + rotateZ 构成立体视角",
      "rotateX(var(--rx))" in css and "rotateZ(var(--rz))" in css)
check("开启 preserve-3d", "transform-style: preserve-3d" in css)
check("配件是立方体（有顶面 + 四个侧面）",
      all(k in css for k in (".fc-top", ".fc-front", ".fc-back", ".fc-left", ".fc-right")))
check("高度由 --h 控制", "--h" in css and "translateZ" in css)
check("图标反向旋转，永远正面朝屏幕",
      "rotateZ(calc(-1 * var(--rz)))" in css and "rotateX(calc(-1 * var(--rx)))" in css)
for lib in ("three.js", "babylon", "gsap", "lottie", "anime.js", "cdnjs", "unpkg", "jsdelivr"):
    check("未引入 " + lib, lib not in (src_farm + js + css).lower())

print("\n=== 4. 配件种类齐全 ===")
for cat in ("ground", "crop", "veg", "fruit", "animal", "build", "decor"):
    check("有分类 " + cat, 'cat="%s"' % cat in src_yard)
for name in ("草皮", "小溪", "池塘", "小麦", "玉米", "白菜", "番茄", "胡萝卜",
             "苹果树", "桃树", "小鸡", "奶牛", "绵羊", "木栅栏", "小木屋", "谷仓",
             "风车", "水井", "橡树", "松树"):
    check("配件含「%s」" % name, name in src_yard)
check("配件总数 >= 45 种", len(re.findall(r'\bdict\(key="', src_yard)) >= 45,
      len(re.findall(r'\bdict\(key="', src_yard)))

print("\n=== 5. 能量买配件 → 摆放 → 搬动 → 拆除 ===")
from core import db, farmyard  # noqa: E402

u = db.query_one("SELECT id, energy FROM users WHERE username=?", (uname,))
uid = u["id"]
db.add_energy(uid, 500)                       # 给测试账号充能量
before = db.energy_of(uid)

r = sess.post(BASE + "/api/yard/buy", json={"key": "cow", "n": 1}).json()
check("买奶牛成功", r["code"] == 0, r)
check("买完扣了能量", db.energy_of(uid) == before - 22, [before, db.energy_of(uid)])
check("奶牛进背包", farmyard.owned(uid).get("cow", 0) >= 1, farmyard.owned(uid))

r = sess.post(BASE + "/api/yard/place", json={"x": 3, "y": 4, "key": "cow"}).json()
check("摆到 (3,4) 成功", r["code"] == 0, r)
check("地皮上多了奶牛",
      db.query_one("SELECT item_key FROM farm_decor WHERE user_id=? AND x=3 AND y=4",
                   (uid,))["item_key"] == "cow")
check("背包里的奶牛用掉一个", farmyard.owned(uid).get("cow", 0) == 0, farmyard.owned(uid))

r = sess.post(BASE + "/api/yard/place", json={"x": 3, "y": 4, "key": "oak"}).json()
check("同一格不能重复摆", r["code"] != 0, r)

r = sess.post(BASE + "/api/yard/move", json={"fx": 3, "fy": 4, "tx": 7, "ty": 8}).json()
check("搬动成功", r["code"] == 0, r)
check("奶牛到了 (7,8)",
      db.query_one("SELECT item_key FROM farm_decor WHERE user_id=? AND x=7 AND y=8",
                   (uid,))["item_key"] == "cow")

r = sess.post(BASE + "/api/yard/remove", json={"x": 7, "y": 8}).json()
check("拆除成功", r["code"] == 0, r)
check("拆完地皮空了",
      db.query_one("SELECT 1 FROM farm_decor WHERE user_id=? AND x=7 AND y=8", (uid,)) is None)
check("拆除把配件退回背包", farmyard.owned(uid).get("cow", 0) == 1, farmyard.owned(uid))

r = sess.post(BASE + "/api/yard/buy", json={"key": "nonexistent"}).json()
check("买不存在的配件会报错", r["code"] != 0, r)
low = db.energy_of(uid)
db.add_energy(uid, -low)                      # 把能量清零
r = sess.post(BASE + "/api/yard/buy", json={"key": "horse"}).json()
check("能量不够买不了", r["code"] != 0, r)

print("\n=== 6. 自由度：没有任务、没有强制路线 ===")
db.add_energy(uid, 800)
# 新号一进来就能直接买最贵的风车，不需要先造别的
r = sess.post(BASE + "/api/yard/buy", json={"key": "windmill"}).json()
check("最贵的风车可以直接买（无前置）", r["code"] == 0, r)
# 任意角落都能直接摆
r = sess.post(BASE + "/api/yard/place", json={"x": 0, "y": 0, "key": "windmill"}).json()
check("角落 (0,0) 想摆就摆", r["code"] == 0, r)
sess.post(BASE + "/api/yard/buy", json={"key": "windmill"}).json()   # 再买一个摆另一角
r = sess.post(BASE + "/api/yard/place", json={"x": 13, "y": 13, "key": "windmill"}).json()
check("另一角 (13,13) 也能摆", r["code"] == 0 and db.query_one(
    "SELECT 1 FROM farm_decor WHERE user_id=? AND x=13 AND y=13", (uid,)) is not None)
sess.post(BASE + "/api/yard/buy", json={"key": "windmill"}).json()   # 多余的一个，验证清空退还
r = sess.post(BASE + "/api/yard/place", json={"x": 99, "y": 99, "key": "windmill"}).json()
check("超出地皮会被拦住", r["code"] != 0, r)

_yard_html = farm.split('<div class="yard">')[1].split('<div class="grid grid-2"')[0]
# 注意：文案里正面写着"没有任务/没有关卡"，所以只数出现次数，别把否定句当成强制引导
for bad in ("主线任务", "每日任务", "建造任务", "必须先", "才能解锁", "阶段目标"):
    check("农场区没有「%s」这类强制引导" % bad, bad not in _yard_html)
check("农场区没有多余的任务字眼", _yard_html.count("任务") <= 1, _yard_html.count("任务"))
check("农场区没有多余的关卡字眼", _yard_html.count("关卡") <= 1, _yard_html.count("关卡"))
check("文案明确写了没有任务没有关卡",
      "没有任务" in _yard_html and "没有关卡" in _yard_html)
check("侧边栏说明写着拆了会退回背包", "回到背包" in _yard_html or "退回背包" in _yard_html)
check("配件价格只跟能量挂钩（不读等级 / 经验）",
      "level_of" not in src_yard and "exp" not in src_yard)

wm_before = farmyard.owned(uid).get("windmill", 0)
wm_on_board = len([b for b in farmyard.board(uid) if b["key"] == "windmill"])
r = sess.post(BASE + "/api/yard/clear", json={}).json()
check("一键清空成功", r["code"] == 0, r)
check("清空后地皮上没有东西", farmyard.board(uid) == [], farmyard.board(uid))
check("清空后摆着的配件全部回背包",
      farmyard.owned(uid).get("windmill", 0) == wm_before + wm_on_board,
      [wm_before, wm_on_board, farmyard.owned(uid)])

print("\n=== 7. 原有菜地玩法没被破坏 ===")
check("作物图鉴还在", "作物图鉴" in farm)
check("我的地还在", "我的地" in farm and "garden" in farm)
check("菜篮还在", "我的菜篮" in farm)
check("一键收获按钮还在", "harvestAll()" in farm)
check("翻地接口仍可用",
      sess.post(BASE + "/api/farm/plow", json={"pid": 1}).json().get("code") in (0, 1))
check("页面标题已改农场", "苗小序的农场" in farm)
check("导航入口改叫农场", read("templates/base.html").count("'农场'") >= 1)

print("\n" + "=" * 56)
print("第 20 轮：通过 %d 项，失败 %d 项" % (OK, BAD))
print("=" * 56)
