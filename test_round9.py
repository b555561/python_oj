"""第九轮：Banner 图片化改造测试

- 大赛 / 指南 banner 使用生成的 PNG 背景图
- 每张 banner 只保留一个行动按钮（立即参赛 / 开始阅读）
- 标题艺术字保留
- 指南错字已修正
"""
import os
import re
import sys
from datetime import date

import requests

BASE = "http://127.0.0.1:" + os.environ.get("OJ_PORT", "8001")
OK = FAIL = 0


def check(name, cond, extra=""):
    global OK, FAIL
    if cond:
        OK += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name}  {extra}")


def main():
    sys.path.insert(0, ".")
    s = requests.Session()
    s.post(BASE + "/login", data={"username": "demo", "password": "demo123456"},
           timeout=15, allow_redirects=False)
    home = s.get(BASE + "/", timeout=15).text
    css = s.get(BASE + "/static/css/style.css", timeout=15).text

    print("\n=== 1. Banner 使用新生成的 PNG 图片 ===")
    check("大赛 banner 引用 PNG 图", 'banner_contest.png' in home)
    check("指南 banner 引用 PNG 图", 'banner_guide.png' in home)
    check("大赛图片可访问",
          s.get(BASE + "/static/images/banners/banner_contest.png", timeout=15).status_code == 200)
    check("指南图片可访问",
          s.get(BASE + "/static/images/banners/banner_guide.png", timeout=15).status_code == 200)
    check("bc-art 是 img 元素", re.search(r'<img[^>]+class="bc-art"', home) is not None)
    check("bc-art 使用 object-fit: cover", "object-fit: cover" in css.split(".bc-art {")[1].split("}")[0])

    print("\n=== 2. 标题艺术字保留 ===")
    check("大赛标题仍在", "耕耘<em>种菜</em>大赛" in home)
    check("指南标题仍在", "网站<em>使用</em>指南" in home)
    check("标题 em 艺术字样式保留", ".bc-title em" in css)
    check("大赛标题金色高亮",
          bool(re.search(r"\.bc-contest\s+\.bc-title em\s*\{[^}]*color:\s*#C97E12", css)))
    check("指南标题绿色高亮",
          bool(re.search(r"\.bc-guide\s+\.bc-title em\s*\{[^}]*color:\s*#2E7D32", css)))

    print("\n=== 3. 每张 banner 只保留一个行动按钮 ===")
    # 分别截取两张 banner 的内容
    parts = re.split(r'banner-card bc-', home)[1:]
    for p, label, want in [(parts[0] if len(parts) > 0 else "", "大赛", "立即参赛"),
                           (parts[1] if len(parts) > 1 else "", "指南", "开始阅读")]:
        gos = re.findall(r'class="bc-go"[^>]*>(.*?)</span>', p)
        chips = re.findall(r'class="bc-chip"', p)
        check(f"{label} banner 有且只有 1 个行动按钮", len(gos) == 1, f"找到 {len(gos)} 个")
        check(f"{label} banner 按钮文案是「{want}】", want in (gos[0] if gos else ""), str(gos))
        check(f"{label} banner 没有多余的 chip 标签", len(chips) == 0, f"找到 {len(chips)} 个")

    print("\n=== 4. 指南错字已修正 ===")
    check("指南 kicker 是「新手必看」", "新手必看" in home)
    check("没有「新手必图」错字", "新手必图" not in home)

    print("\n=== 5. 左侧遮罩保证文字可读 ===")
    check("bc-veil 样式存在", ".bc-veil" in css)
    check("大赛遮罩从左侧强渐变", "rgba(255,250,234,.98)" in css.split(".bc-contest .bc-veil")[1].split("}")[0])
    check("指南遮罩从左侧强渐变", "rgba(245,251,243,.98)" in css.split(".bc-guide .bc-veil")[1].split("}")[0])
    check("文案层 z-index 高于遮罩", int(re.search(r"\.bc-poster\s*\{[^}]*z-index:\s*(\d+)", css).group(1)) >
          int(re.search(r"\.bc-veil\s*\{[^}]*z-index:\s*(\d+)", css).group(1)))

    print("\n=== 6. 原有核心功能仍正常 ===")
    check("登录接口正常", s.post(BASE + "/api/checkin", json={}, timeout=15).json().get("code") in (0, 1))
    check("首页可访问", s.get(BASE + "/", timeout=15).status_code == 200)
    check("大赛页面可访问", s.get(BASE + "/contest", timeout=15).status_code == 200)
    check("指南页面可访问", s.get(BASE + "/guide", timeout=15).status_code == 200)
    check("签到弹窗仍在", 'id="signinMask"' in home)

    print("\n" + "=" * 46)
    print(f"  通过 {OK} 项，失败 {FAIL} 项")
    print("=" * 46)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
