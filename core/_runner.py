"""判题子进程：在受限环境中执行用户代码并比对测试用例。

由 core/judge.py 通过 subprocess 调用，不要手动运行。
用法: python _runner.py <输入json> <输出json>
"""
import builtins
import io
import json
import sys
from contextlib import redirect_stdout

# 允许使用的内置函数白名单
SAFE_NAMES = [
    "abs", "all", "any", "bool", "chr", "ord", "dict", "divmod", "enumerate",
    "filter", "float", "int", "isinstance", "len", "list", "map", "max", "min",
    "pow", "print", "range", "repr", "reversed", "round", "set", "sorted",
    "str", "sum", "tuple", "type", "zip", "True", "False", "None",
]
SAFE_BUILTINS = {}
for _n in SAFE_NAMES:
    if hasattr(builtins, _n):
        SAFE_BUILTINS[_n] = getattr(builtins, _n)
SAFE_BUILTINS["True"] = True
SAFE_BUILTINS["False"] = False
SAFE_BUILTINS["None"] = None


def compare(got, expected):
    if isinstance(expected, float) or isinstance(got, float):
        try:
            return abs(float(got) - float(expected)) < 1e-6
        except Exception:
            return False
    if isinstance(expected, list) and isinstance(got, (list, tuple)):
        return list(got) == list(expected)
    return got == expected


def main():
    in_path, out_path = sys.argv[1], sys.argv[2]
    with open(in_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    code = payload["code"]
    func = payload["func"]
    tests = payload.get("tests", [])

    result = {"status": "accepted", "passed": 0, "total": len(tests),
              "results": [], "stdout": "", "message": ""}

    # 语法/编译期错误（含禁用 import 引发的 NameError 等会在运行时暴露）
    try:
        compile(code, "<user_code>", "exec")
    except SyntaxError as e:
        result["status"] = "error"
        result["message"] = f"语法错误：第 {e.lineno} 行 {e.msg}"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
        return

    g = {"__builtins__": SAFE_BUILTINS, "__name__": "__user__"}
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            exec(code, g)  # noqa: S102
    except Exception as e:  # noqa: BLE001
        result["status"] = "error"
        result["message"] = f"{type(e).__name__}: {e}（注意：沙箱内禁止 import 与文件操作）"
        result["stdout"] = buf.getvalue()[:2000]
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
        return

    if func not in g or not callable(g[func]):
        result["status"] = "error"
        result["message"] = f"没有找到函数 `{func}`，请确认你定义了它。"
        result["stdout"] = buf.getvalue()[:2000]
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False)
        return

    wrong = 0
    for t in tests:
        args = t.get("args", [])
        expected = t.get("expected")
        item = {"ok": False, "args": args, "expected": expected, "got": None, "error": ""}
        try:
            with redirect_stdout(buf):
                got = g[func](*args)
            item["got"] = got if isinstance(got, (int, float, str, bool, list, dict, tuple)) else repr(got)
            item["ok"] = compare(got, expected)
        except Exception as e:  # noqa: BLE001
            item["error"] = f"{type(e).__name__}: {e}"
        if not item["ok"]:
            wrong += 1
        result["results"].append(item)

    errs = [r for r in result["results"] if r.get("error")]
    result["passed"] = len(tests) - wrong
    if wrong and errs and len(errs) == len(tests) and tests:
        # 所有用例都抛了同一种异常（如沙箱禁止 import），归类为运行出错更清楚
        result["status"] = "error"
        result["message"] = errs[0]["error"]
    elif wrong:
        result["status"] = "wrong"
        result["message"] = f"有 {wrong} 个测试用例未通过"
    else:
        result["status"] = "accepted"
    result["stdout"] = buf.getvalue()[:2000]

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
