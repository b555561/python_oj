"""PyOJ 耘码 · 一键备份

把项目打成带时间戳的 zip，两种模式：

    python tools/backup.py                 完整备份（含数据库 + 会话密钥）—— 本地/网盘存档用
    python tools/backup.py --public        纯净备份（不含数据库/密钥/快照）—— 发别人、上传 GitHub 用
    python tools/backup.py --to "D:\\备份"   指定输出目录

备份完成后会自动校验 zip 完整性（读一遍所有条目算 CRC），坏包会当场报错。
"""
import os
import sqlite3
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# 任何模式都要排除的（体积大 / 可重新生成 / 缓存）
ALWAYS_SKIP_DIRS = {
    "ven", "venv", ".venv", "__pycache__", ".git", "node_modules",
    "backup_旧版", ".pytest_cache", ".vscode", ".idea",
}
ALWAYS_SKIP_FILES = {"Thumbs.db", ".DS_Store"}

# 纯净模式额外排除：运行时数据 + 敏感信息 + 本地快照
PUBLIC_SKIP_FILES = {
    "database.db", ".secret_key", "config.json", "push_config.json",
    "Procfile", "render.yaml", "Dockerfile", ".dockerignore",
}
PUBLIC_SKIP_SUFFIX = {".db", ".sqlite", ".sqlite3", ".pyc", ".pyo"}


def skip(path: Path, public: bool) -> bool:
    """判断某个路径是否跳过"""
    rel = path.relative_to(BASE)
    parts = rel.parts

    # 目录黑名单（只看第一段就够，这些都是顶层目录）
    if parts[0] in ALWAYS_SKIP_DIRS:
        return True
    if len(parts) > 1 and parts[-2] == "__pycache__":
        return True

    name = path.name
    if name in ALWAYS_SKIP_FILES:
        return True

    # 本地预览快照：项目「根目录」下 _ 开头的 html，单个 2MB，随时一条命令重新生成
    # 重新生成： python tools/make_static_snapshot.py /farm _farm.html --login --no-img
    #
    # ⚠ 注意必须限定「根目录」！templates/ 下的 _nav.html / _mascot.html / _hezi.html
    #   等 Jinja 宏模板同样以 _ 开头，误杀会让页面直接 500（首页 extends base.html
    #   → base.html 又 from "_nav.html" import）。这个坑是实测解压启动时发现的。
    if len(parts) == 1 and name.startswith("_") and name.endswith(".html"):
        return True

    if public:
        if name in PUBLIC_SKIP_FILES:
            return True
        if path.suffix in PUBLIC_SKIP_SUFFIX:
            return True
    return False


def db_consistent_copy(tmp_dir: Path):
    """服务正在运行时直接复制 database.db 可能读到半写状态。

    用 SQLite 官方的 backup API 导出一份一致快照，拿它进压缩包。
    （按官方样例：dest 用连接 A，src 用连接 B，避免与业务写操作互相阻塞）
    失败则退回原文件，绝不因此中断备份。
    """
    src = BASE / "database.db"
    if not src.exists():
        return None
    out = tmp_dir / "database.db"
    try:
        src_conn = sqlite3.connect(str(src))
        dst_conn = sqlite3.connect(str(out))
        with dst_conn:
            src_conn.backup(dst_conn)      # pages=1 全量，默认一次拷完
        dst_conn.close()
        src_conn.close()
        if out.exists() and out.stat().st_size > 0:
            return out
    except Exception as e:
        print(f"   ⚠ 数据库一致性快照失败（{e}），改用直接复制")
    return None


def build(out_dir: Path, public: bool) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    kind = "纯净版" if public else "完整版"
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"PyOJ备份_{kind}_{stamp}.zip"

    db_copy = None
    if not public:
        tmp_dir = Path(tempfile.mkdtemp(prefix="pyoj_bak_"))
        db_copy = db_consistent_copy(tmp_dir)

    files = []
    for root, dirs, names in os.walk(BASE):
        root_p = Path(root)
        # 就地裁剪 dirs，避免 os.walk 钻进 venv（省几秒）
        dirs[:] = [d for d in dirs if not skip(root_p / d, public)]
        for n in names:
            p = root_p / n
            if skip(p, public):
                continue
            files.append(p)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in files:
            # 数据库用一致性快照替身，其余原样
            arc = p.relative_to(BASE).as_posix()
            z.write(db_copy if (db_copy and p.name == "database.db") else p, arc)

    # 完整性校验：真正读一遍，CRC 不对会抛 BadZipFile / 校验和错误
    with zipfile.ZipFile(zip_path, "r") as z:
        bad = z.testzip()
        n = len(z.namelist())
    if bad is not None:
        raise RuntimeError(f"备份包损坏，首个坏文件：{bad}")

    size_mb = zip_path.stat().st_size / 1024 / 1024
    print(f"✅ 备份完成（{kind}）")
    print(f"   文件：{zip_path}")
    print(f"   大小：{size_mb:.2f} MB   |   收录 {n} 个文件")
    print(f"   完整性校验：通过")
    return zip_path


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    public = "--public" in sys.argv
    out_dir = None
    if "--to" in sys.argv:
        i = sys.argv.index("--to")
        if i + 1 < len(sys.argv):
            out_dir = Path(sys.argv[i + 1])
    if args and out_dir is None:
        out_dir = Path(args[0])
    if out_dir is None:
        out_dir = Path(r"D:\PyOJ备份")
    build(out_dir, public)


if __name__ == "__main__":
    main()
