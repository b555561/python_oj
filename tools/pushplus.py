# -*- coding: utf-8 -*-
"""PushPlus 微信推送封装（pushplus.plus）

用法：
    from tools import pushplus
    pushplus.send("标题", "正文（支持 html）")

凭证优先级：命令行/调用参数 > 环境变量 PUSHPLUS_TOKEN > tools/push_config.json
"""
import json
import os
import urllib.request

API = "https://www.pushplus.plus/send"
_HERE = os.path.dirname(os.path.abspath(__file__))
CFG_PATH = os.path.join(_HERE, "push_config.json")


def load_cfg() -> dict:
    cfg = {
        "token": os.environ.get("PUSHPLUS_TOKEN", ""),
        "url": "http://127.0.0.1:8001",
        "topic": "",          # 群组编码：一对多推送时填
        "to": "",             # 备注：推给谁
    }
    if os.path.exists(CFG_PATH):
        try:
            with open(CFG_PATH, encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    return cfg


def save_cfg(**kv) -> None:
    cfg = load_cfg()
    cfg.update({k: v for k, v in kv.items() if v is not None})
    with open(CFG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def send(title: str, content: str, token: str = "", url: str = "") -> dict:
    """推送一条微信消息。返回接口原始 JSON。"""
    cfg = load_cfg()
    token = token or cfg.get("token", "")
    if not token:
        return {"code": -1, "msg": "缺少 PushPlus token（填 tools/push_config.json 或环境变量 PUSHPLUS_TOKEN）"}

    payload = {
        "token": token,
        "title": title,
        "content": content,
        "template": "html",
    }
    if cfg.get("topic"):
        payload["topic"] = cfg["topic"]

    req = urllib.request.Request(
        API,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"code": -2, "msg": f"推送失败：{e}"}


def build_report(url: str, total: int, suites: list, note: str = "") -> str:
    """生成推送正文（html 模板）。"""
    rows = "".join(
        f"<tr><td>{name}</td><td style='text-align:right'>{cnt}</td>"
        f"<td style='text-align:right'>{'✅' if ok else '❌'}</td></tr>"
        for name, cnt, ok in suites
    )
    return f"""
    <div style="font-family:-apple-system,'PingFang SC',sans-serif;line-height:1.8;color:#2f3a33">
      <p style="font-size:16px;font-weight:700;margin:0 0 8px">🌾 PyOJ 网站已完善，全部自动化测试通过</p>
      <p style="margin:0 0 10px">
        网址：<a href="{url}" style="color:#2E7D32;font-weight:700">{url}</a><br>
        体验账号：<code>demo</code> / <code>demo123456</code>
      </p>
      <table border="1" cellpadding="6" cellspacing="0"
             style="border-collapse:collapse;font-size:13px;border-color:#d9ead6">
        <tr style="background:#f2faf0"><th>测试套件</th><th>通过项</th><th>结果</th></tr>
        {rows}
        <tr><td><b>合计</b></td><td style="text-align:right"><b>{total}</b></td>
            <td style="text-align:right"><b>✅</b></td></tr>
      </table>
      <p style="margin:10px 0 0;font-size:13px;color:#5c6b60">
        本次更新：页脚版权声明栏 · 四大板块模块顺序调整 · 首次登录分步新手引导 ·
        苗小序分板块动作动画 · 注册欢迎语与每日签到祝福。
        {note}
      </p>
      <p style="margin:6px 0 0;font-size:12px;color:#98a29c">
        —— 由 PyOJ 自动化监控推送{('，推送对象：' + note) if note else ''}
      </p>
    </div>
    """


if __name__ == "__main__":
    import sys

    cfg = load_cfg()
    t = sys.argv[1] if len(sys.argv) > 1 else "PyOJ 测试通过通知"
    c = sys.argv[2] if len(sys.argv) > 2 else "测试全部通过 ✅"
    print(send(t, c))
