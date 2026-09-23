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
import requests

BASE = "http://127.0.0.1:8001"
HEAD_TPL = ('<!-- 离线快照：由 tools/make_static_snapshot.py 生成，'
            'CSS/JS 已内联，可直接双击用浏览器打开 -->')


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


def inline_img(html, sess):
    def repl(m):
        src = m.group(1)
        if src.startswith("data:") or src.startswith("http"):
            return m.group(0)
        url = BASE + src
        try:
            r = sess.get(url, timeout=10)
            if r.status_code != 200:
                return m.group(0)
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
    html = abs_img(html) if light else inline_img(html, s)
    # 内联后残留的站内绝对链接改成可点击的完整地址（方便在快照里继续点）
    html = html.replace('href="/', 'href="%s/' % BASE)
    if "<head>" in html:
        html = html.replace("<head>", "<head>\n" + HEAD_TPL, 1)

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    kind = "轻量快照（图片走本地服务）" if light else "自包含快照（图片已内联）"
    print("已生成%s: %s  （%d 字节，CSS/JS 均内联）" % (kind, out, len(html)))
    print("外部样式表残留:", html.count("rel=\"stylesheet\""),
          "| 外部脚本残留:", html.count("<script src="))


if __name__ == "__main__":
    main()
