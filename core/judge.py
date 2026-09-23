"""判题引擎：把用户代码丢进独立子进程执行，带超时与安全限制。

安全说明（重要）：
  这是一个"教学级轻量沙箱"，适用于本地/内网学习环境。
  它通过 1) 独立子进程 2) 执行超时 3) 移除危险内置函数 4) 禁用 import
  四层限制来防止误操作与死循环。
  如果要部署到公网，请改用 Docker / 专用判题服务，不要直接暴露本模块。
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
RUNNER = Path(__file__).resolve().parent / "_runner.py"

# 优先用项目 venv 的解释器，找不到就用当前解释器
VENV_PY = BASE_DIR / "ven" / "Scripts" / "python.exe"
PY_EXE = str(VENV_PY) if VENV_PY.exists() else sys.executable

TIME_LIMIT = 5  # 秒


def _compare(got: Any, expected: Any) -> bool:
    """结果比较：浮点用容差，其余用 ==。"""
    if isinstance(expected, float) or isinstance(got, float):
        try:
            return abs(float(got) - float(expected)) < 1e-6
        except Exception:
            return False
    if isinstance(expected, list) and isinstance(got, (list, tuple)):
        return list(got) == list(expected)
    if isinstance(expected, dict) and isinstance(got, dict):
        return got == expected
    return got == expected


def run_code(code: str, func_name: str, tests: List[Dict[str, Any]],
             time_limit: int = TIME_LIMIT) -> Dict[str, Any]:
    """执行用户代码并返回判题结果。

    tests 每项形如 {"args": [..], "expected": ..}
    返回 {"status": "accepted"/"wrong"/"error"/"timeout",
          "passed": n, "total": m,
          "results": [{"ok":bool,"args":..,"expected":..,"got":..,"error":..}],
          "stdout": "..."}
    """
    payload = {"code": code, "func": func_name, "tests": tests}

    fd, tmp_in = tempfile.mkstemp(suffix=".json", prefix="oj_")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)

    tmp_out = tmp_in + ".out.json"
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    try:
        proc = subprocess.run(
            [PY_EXE, str(RUNNER), tmp_in, tmp_out],
            capture_output=True, text=True, timeout=time_limit,
            encoding="utf-8", errors="replace", env=env,
            cwd=str(tempfile.gettempdir()),
        )
        if os.path.exists(tmp_out):
            with open(tmp_out, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "status": "error", "passed": 0, "total": len(tests), "results": [],
            "stdout": "",
            "message": (proc.stderr or "")[-1500:] or "判题进程异常退出",
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout", "passed": 0, "total": len(tests), "results": [],
            "stdout": "",
            "message": f"代码执行超时（超过 {time_limit} 秒），请检查是否存在死循环。",
        }
    except Exception as e:  # noqa: BLE001
        return {
            "status": "error", "passed": 0, "total": len(tests), "results": [],
            "stdout": "", "message": f"判题引擎异常：{e}",
        }
    finally:
        for p in (tmp_in, tmp_out):
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
