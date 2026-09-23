# -*- coding: utf-8 -*-
"""PyOJ 全量回归监控 + 微信推送

用法：
    python tools/run_all_tests.py            # 只跑测试，打印汇总
    python tools/run_all_tests.py --push     # 跑测试；全部通过才推送微信

推送通道用 PushPlus：token / 网址 写在 tools/push_config.json
（或环境变量 PUSHPLUS_TOKEN）。收件人备注写在 push_config.json 的 to 字段。
"""
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

SUITES = [
    "test_e2e.py", "test_social.py", "test_branch.py", "test_round4.py",
    "test_round5.py", "test_round7.py", "test_round8.py", "test_round9.py",
    "test_round10.py", "test_round11.py", "test_round12.py",
    "test_round13.py", "test_round14.py", "test_round15.py", "test_round16.py", "test_round17.py",
]
PY = os.path.join(ROOT, "ven", "Scripts", "python.exe")
if not os.path.exists(PY):
    PY = sys.executable

NUM = re.compile(r"通过\s*(\d+)\s*项")
# 测试脚本本身总是 exit 0，必须从输出里解析失败数，否则会把失败套件当成通过去推送
BAD = re.compile(r"失败\s*(\d+)\s*项")
MARK = re.compile(r"^\s*✗", re.M)


def run_one(name: str):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([PY, name], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=env)
    out = (p.stdout or "") + (p.stderr or "")
    m = NUM.findall(out)
    cnt = int(m[-1]) if m else 0
    # 判定：先看「失败 N 项」，没有就数 ✗ 标记，都没有才退回 exit code
    bad = BAD.findall(out)
    n_bad = int(bad[-1]) if bad else len(MARK.findall(out))
    ok = (n_bad == 0) and (p.returncode == 0 or bad)
    tail = [l for l in out.strip().splitlines() if l.strip()][-1:] or [""]
    return name, cnt, ok, tail[0]


def main() -> int:
    do_push = "--push" in sys.argv
    suites, total, failed = [], 0, []
    print("=" * 60)
    print("PyOJ 全量回归监控")
    print("=" * 60)
    for name in SUITES:
        n, cnt, ok, tail = run_one(name)
        suites.append((n, cnt, ok))
        total += cnt
        if not ok:
            failed.append(n)
        print(f"  {'✅' if ok else '❌'} {n:<16} {cnt:>4} 项   {tail[:44]}")
    print("-" * 60)
    print(f"合计 {total} 项，失败 {len(failed)} 个套件"
          + (f"：{', '.join(failed)}" if failed else ""))

    if do_push:
        if failed:
            print("\n有套件未通过，按约定不推送。")
            return 1
        try:
            import pushplus
        except Exception as e:
            print("推送模块加载失败：", e)
            return 1
        cfg = pushplus.load_cfg()
        url = cfg.get("url") or "http://127.0.0.1:8001"
        content = pushplus.build_report(
            url, total, suites, note=cfg.get("to", ""))
        res = pushplus.send("🌾 PyOJ 网站已完善，全部测试通过", content)
        print("\n推送结果：", res)
        return 0 if res.get("code") == 200 else 1

    if failed:
        return 1
    print("\n全部通过 ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
