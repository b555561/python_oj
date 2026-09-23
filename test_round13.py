# -*- coding: utf-8 -*-
"""端到端测试（第十三轮）：按页面区分苗小序动画
   菜园 farm    → 循环 耕地 → 浇水 → 施肥
   厨房 kitchen → 循环 切菜 → 做菜
   商店 shop    → 循环 原地转圈 + 招手
   果蔬摊 market→ 循环 原地转圈 + 挥手
   其余页面      → 不加动作类，不重复动作
   全部用 CSS @keyframes，不引入外部动画库
"""
import re
import requests

BASE = "http://127.0.0.1:8001"
s = requests.Session()
OK = FAIL = 0


def check(name, cond, extra=""):
    global OK, FAIL
    if cond:
        OK += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name} {extra}")


print("=== 0. 登录与环境 ===")
s.post(BASE + "/login", data={"username": "demo", "password": "demo123456"},
       allow_redirects=False)
home = s.get(BASE + "/", timeout=15).text
css = s.get(BASE + "/static/css/style.css", timeout=15).text
nj = s.get(BASE + "/static/js/nan.js", timeout=15).text
check("首页可访问", "PyOJ" in home)

print("\n=== 1. 悬浮球道具层 ===")
check("道具层 nf-props 存在", "nf-props" in home)
for p, e in (("p-hoe", "⛏️"), ("p-water", "🪣"), ("p-fert", "🧪"),
             ("p-knife", "🔪"), ("p-cook", "🍳"), ("p-wave", "👋"),
             ("p-clod", "🟤"), ("p-drop", "💧"), ("p-grain", "✨")):
    check(f"道具 {p}（{e}）存在", f'nf-prop {p}' in home)
check("动作文字气泡 nf-act", 'id="nfAct"' in home)

print("\n=== 2. nan.js 按路径切换动作 ===")
check("有页面动作模式函数 pageActMode", "function pageActMode" in nj)
for path, mode in (("/farm", "farm"), ("/kitchen", "kitchen"),
                   ("/shop", "shop"), ("/market", "market")):
    check(f"{path} → {mode} 动作",
          re.search(r"indexOf\('" + path + r"'\)\s*===\s*0\)\s*return\s*'" + mode + "'", nj)
          is not None)
check("其余页面返回空（不重复动作）", "return ''" in nj)
check("菜园动作文案 耕地/浇水/施肥",
      "['耕地', '浇水', '施肥']" in nj.replace('"', "'"))
check("厨房动作文案 切菜/做菜",
      "['切菜', '做菜']" in nj.replace('"', "'"))
check("商店动作文案 招手", "'招手'" in nj.replace('"', "'"))
check("果蔬摊动作文案 挥手", "'挥手'" in nj.replace('"', "'"))
check("菜园每步 2.2s", "step: 2200" in nj)
check("厨房每步 1.8s", "step: 1800" in nj)
check("商店/果蔬摊一轮 3.4s", nj.count("step: 3400") == 2)
check("多动作页面按阶段轮换 ph-*",
      "'ph-0', 'ph-1', 'ph-2'" in nj.replace('"', "'"))
check("切换页面时清理旧动作类", "ACT_CLASSES.forEach" in nj)
check("离开动作页时移除 data-act", "removeAttribute('data-act')" in nj)

print("\n=== 3. CSS 动作类与关键帧 ===")
for c in (".nan-fab.act-farm", ".nan-fab.act-kitchen",
          ".nan-fab.act-shop", ".nan-fab.act-market"):
    check(f"动作类 {c}", c in css)

# 菜园：耕地 → 浇水 → 施肥（三阶段）
check("菜园阶段0 耕地（锄头）", ".nan-fab.act-farm.ph-0 .nf-prop.p-hoe" in css)
check("菜园阶段1 浇水（水桶）", ".nan-fab.act-farm.ph-1 .nf-prop.p-water" in css)
check("菜园阶段2 施肥（肥料）", ".nan-fab.act-farm.ph-2 .nf-prop.p-fert" in css)
check("菜园耕地身体动作", ".nan-fab.act-farm.ph-0 .nan" in css)
check("菜园浇水身体动作", ".nan-fab.act-farm.ph-1 .nan" in css)
check("菜园施肥身体动作", ".nan-fab.act-farm.ph-2 .nan" in css)
check("耕地扬起土块", ".nan-fab.act-farm.ph-0 .nf-prop.p-clod" in css)
check("浇水洒出水滴", ".nan-fab.act-farm.ph-1 .nf-prop.p-drop" in css)
check("施肥撒出颗粒", ".nan-fab.act-farm.ph-2 .nf-prop.p-grain" in css)

# 厨房：切菜 → 做菜
check("厨房阶段0 切菜（菜刀）", ".nan-fab.act-kitchen.ph-0 .nf-prop.p-knife" in css)
check("厨房阶段1 做菜（锅）", ".nan-fab.act-kitchen.ph-1 .nf-prop.p-cook" in css)
check("厨房切菜身体动作", ".nan-fab.act-kitchen.ph-0 .nan" in css)
check("厨房做菜身体动作", ".nan-fab.act-kitchen.ph-1 .nan" in css)

# 商店 / 果蔬摊：转圈 + 招手
check("商店转圈 + 招手",
      ".nan-fab.act-shop .nan" in css and ".nan-fab.act-shop .nf-prop.p-wave" in css)
check("果蔬摊转圈 + 挥手",
      ".nan-fab.act-market .nan" in css and ".nan-fab.act-market .nf-prop.p-wave" in css)

for kf in ("nanHoe", "nfHoe", "nfClod", "nanWater", "nfWater", "nfDrop",
           "nanFert", "nfFert", "nfGrain", "nanChop", "nfKnife",
           "nanStir", "nfPan", "nanSpin", "nfWave"):
    check(f"关键帧 @keyframes {kf}", f"@keyframes {kf}" in css)

print("\n=== 4. 循环播放（infinite） ===")
def _loop(pat):
    """统计带 infinite 的动画声明条数（按行匹配，避免跨行）。"""
    return len([ln for ln in css.split("\n")
                if re.search(pat, ln) and "infinite" in ln])


check("菜园动作无限循环", _loop(r"\.nan-fab\.act-farm\.ph-\d") >= 6)
check("厨房动作无限循环", _loop(r"\.nan-fab\.act-kitchen\.ph-\d") >= 4)
check("商店/果蔬摊动作无限循环", _loop(r"\.nan-fab\.act-(shop|market)") >= 2)

print("\n=== 5. 纯 CSS 实现，无外部动画库 ===")
pages = ["/", "/farm", "/kitchen", "/shop", "/market"]
libs = ("animate.css", "lottie", "gsap", "anime.min.js", "velocity", "aos.css")
bad = []
for p in pages:
    t = s.get(BASE + p, timeout=15).text
    for l in libs:
        if l in t.lower():
            bad.append(p + ":" + l)
check("未引入任何外部动画库", not bad, bad)
check("无外链 CDN 脚本（除本站静态资源）",
      not re.search(r'<script[^>]+src="https?://', home))
check("关键帧均写在本地 style.css",
      css.count("@keyframes") >= 15, css.count("@keyframes"))

print("\n=== 6. 性能友好：只动 transform / opacity ===")
kf_blocks = re.findall(r"@keyframes (?:nan|nf)\w+\s*\{(.*?)\n\}", css, re.S)
check("提取到动作关键帧", len(kf_blocks) >= 12, len(kf_blocks))
heavy = [b for b in kf_blocks
         if re.search(r"(?<!-)\b(width|height|top|left|margin|padding)\s*:", b)]
check("关键帧不触发重排（无 width/height/top/left 动画）", not heavy,
      [h[:60] for h in heavy])

print("\n=== 7. 尊重「减少动态效果」 ===")
# CSS 里有多处 reduced-motion 块（签到/欢迎/引导/舞台），取全部拼接后再判断
_rm = "".join(css.split("@media (prefers-reduced-motion: reduce)")[1:])
check("prefers-reduced-motion 关闭身体动作",
      "act-shop .nan { animation: none" in _rm and "act-farm .nan" in _rm)
check("prefers-reduced-motion 隐藏道具动画",
      ".nan-fab .nf-prop { animation: none !important" in css)

print("\n=== 8. 原有功能未受影响 ===")
check("拖拽能力保留（Pointer 事件）", "pointerdown" in nj)
check("语音输入保留", "SpeechRecognition" in nj or "webkitSpeechRecognition" in nj)
f = s.get(BASE + "/farm", timeout=15).text
k = s.get(BASE + "/kitchen", timeout=15).text
sh = s.get(BASE + "/shop", timeout=15).text
mk = s.get(BASE + "/market", timeout=15).text
check("菜园页内容完整（我的地）", "我的地" in f)
check("厨房页内容完整（菜谱）", "菜谱" in k)
check("种子商店页内容完整（稀有种子）", "稀有种子" in sh)
check("果蔬摊页内容完整（今日行情/价目）",
      ("价目" in mk or "行情" in mk))
check("四个板块页均返回 200", all(x for x in (f, k, sh, mk)))
check("版权栏仍在", "©2026 PyOJ耘码项目 All Rights Reserved." in f)

print(f"\n{'='*46}\n结果：通过 {OK} 项，失败 {FAIL} 项\n{'='*46}")
