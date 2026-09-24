# -*- coding: utf-8 -*-
"""
把线上页面抓成「完全自包含」的静态快照（CSS / JS 内联，img 转 data URI），
这样用 file:// 直接打开也能看到完整样式，不依赖本地服务是否在运行。

用法：
    ./ven/Scripts/python.exe tools/make_static_snapshot.py /cert _cert_offline.html
    ./ven/Scripts/python.exe tools/make_static_snapshot.py /register _reg_offline.html
    # 需要登录态的页面，先 --login 自动注册一个临时账号
    ./ven/Scripts/python.exe tools/make_static_snapshot.py /cert _cert_offline.html --login
"""
import sys
import re
import time
import base64
import mimetypes
import urllib.parse
import requests

BASE = "http://127.0.0.1:8001"
HEAD_TPL = ('<!-- 离线快照：由 tools/make_static_snapshot.py 生成，'
            'CSS/JS 已内联，可直接双击用浏览器打开 -->')

# --slim 模式下大图的替身：一张田园配色的内联 SVG（自带文字说明，不依赖任何外部资源）
_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="240">'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0" stop-color="#eaf6e2"/><stop offset="1" stop-color="#cfe8c4"/>'
        '</linearGradient></defs>'
        '<rect width="1200" height="240" fill="url(#g)"/>'
        '<text x="600" y="126" font-family="sans-serif" font-size="24" '
        'fill="#5c8a4a" text-anchor="middle">'
        '田园横幅图（完整图见本地站点）</text></svg>')
PLACEHOLDER = "data:image/svg+xml;charset=utf-8," + urllib.parse.quote(_SVG)


def inline_css(html, sess):
    def repl(m):
        href = m.group(1)
        url = href if href.startswith("http") else BASE + href
        try:
            css = sess.get(url, timeout=10).text
        except Exception as e:
            return "<!-- css 拉取失败 %s: %s -->" % (url, e)
        return "<style>\n%s\n</style>" % css
    return re.sub(r'<link[^>]+rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)["\'][^>]*>',
                  repl, html)


def inline_js(html, sess):
    def repl(m):
        src = m.group(1)
        if src.startswith("http") or "//" in src.split("/")[0]:
            url = src if src.startswith("http") else BASE + src
        else:
            url = BASE + src
        try:
            js = sess.get(url, timeout=10).text
        except Exception as e:
            return "<!-- js 拉取失败 %s: %s -->" % (url, e)
        return "<script>\n%s\n</script>" % js
    return re.sub(r'<script[^>]+src=["\']([^"\']+)["\'][^>]*>\s*</script>', repl, html)


def inline_img(html, sess, max_bytes=None):
    """图片转 data URI。

    max_bytes 不为 None 时（--slim 模式）：超过该体积的图片不内联，
    换成一张内联 SVG 占位图。目的是让快照「完全自包含」的同时把体积压下来——
    之前全内联会到 2.1MB，预览面板加载超时被当成文件损坏。
    """
    def repl(m):
        src = m.group(1)
        if src.startswith("data:") or src.startswith("http"):
            return m.group(0)
        url = BASE + src
        try:
            r = sess.get(url, timeout=10)
            if r.status_code != 200:
                return m.group(0)
            if max_bytes is not None and len(r.content) > max_bytes:
                return m.group(0).replace(src, PLACEHOLDER)
            ctype = r.headers.get("content-type") or \
                mimetypes.guess_type(url)[0] or "image/png"
            b64 = base64.b64encode(r.content).decode("ascii")
            return m.group(0).replace(src, "data:%s;base64,%s" % (ctype, b64))
        except Exception:
            return m.group(0)
    return re.sub(r'<img[^>]+src=["\']([^"\']+)["\']', repl, html)


def abs_img(html):
    """不内联图片（--no-img）：仅把 src="/..." 补成 http://127.0.0.1:8001/...
       文件体积能小 10 倍，预览面板加载更快；前提是本地服务在运行。"""
    def repl(m):
        src = m.group(1)
        if src.startswith("http") or src.startswith("data:"):
            return m.group(0)
        return m.group(0).replace(src, BASE + src)
    html = re.sub(r'<img[^>]+src=["\']([^"\']+)["\']', repl, html)
    return re.sub(r'url\((["\']?)/static/', r'url(\1' + BASE + '/static/', html)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    login = "--login" in sys.argv
    path = args[0] if args else "/"
    out = args[1] if len(args) > 1 else "_snapshot.html"

    s = requests.Session()
    if login:
        un = "snap" + str(int(time.time()) % 100000)
        s.post(BASE + "/register",
               data={"username": un, "password": "test123456", "nickname": "snap"},
               allow_redirects=False, timeout=10)
        s.get(BASE + "/", timeout=10)

    r = s.get(BASE + path, timeout=15)
    if r.status_code != 200:
        print("抓取失败 HTTP %s（%s 可能需要登录，加 --login）" % (r.status_code, path))
        sys.exit(1)

    html = r.text
    html = inline_css(html, s)
    html = inline_js(html, s)
    light = "--no-img" in sys.argv
    slim = "--slim" in sys.argv
    html = abs_img(html) if light else inline_img(html, s, 120 * 1024 if slim else None)
    # 内联后残留的站内绝对链接改成可点击的完整地址（方便在快照里继续点）
    html = html.replace('href="/', 'href="%s/' % BASE)
    if "<head>" in html:
        html = html.replace("<head>", "<head>\n" + HEAD_TPL, 1)

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    if light:
        kind = "轻量快照（图片走本地服务，服务停了图会缺）"
    elif slim:
        kind = "精简自包含快照（大图用占位图，完全不依赖服务）"
    else:
        kind = "完整自包含快照（全部图片已内联，体积较大）"
    print("已生成%s: %s  （%.0f KB）" % (kind, out, len(html.encode("utf-8")) / 1024))
    print("外部样式表残留:", html.count("rel=\"stylesheet\""),
          "| 外部脚本残留:", html.count("<script src="),
          "| 外部图片残留:", len(re.findall(r'src="(?!data:)(?!http)', html)))


if __name__ == "__main__":
    main()
