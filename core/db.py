"""数据库层：建表、迁移、通用查询助手。"""
import sqlite3
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database.db"


# ============ 等级体系 ============
# (等级, 所需累计经验, 称号)
LEVELS = [
    (1, 0, "垦荒新手"),
    (2, 100, "育苗学徒"),
    (3, 300, "菜畦农工"),
    (4, 600, "耘田能手"),
    (5, 1000, "田垄匠师"),
    (6, 1500, "良田农师"),
    (7, 2100, "沃土宗师"),
    (8, 2800, "麦浪守望"),
    (9, 3600, "金穗巨匠"),
    (10, 4500, "沃野神农"),
]

# 经验获取规则
XP_FIRST_AC = 30      # 首次通过
XP_REPEAT_AC = 5      # 重复通过
XP_CHECKIN = 10       # 每日打卡
XP_QUIZ_PASS = 50     # 测验通过

# 能量（菜园）规则 —— 打卡刷题攒能量，用来耕地浇水种菜
ENERGY_CHECKIN = 10     # 每日打卡
ENERGY_FIRST_AC = 8     # 首次通过一道题
ENERGY_REPEAT_AC = 2    # 重复通过
ENERGY_QUIZ_PASS = 30   # 测验 / 认证通过
ENERGY_POST = 5         # 学习圈发帖（每天最多 3 次）
ENERGY_COMMENT = 2      # 学习圈评论（每天最多 5 次）
ENERGY_PLOW = 5         # 耕地消耗
ENERGY_WATER = 8        # 浇水消耗
ENERGY_DISH = 12        # 把菜肴发布到学习圈的基础奖励（菜谱越高级给得越多）

# 金币兑换能量的汇率：COIN_RATE 枚金币 → 1 点能量
COIN_RATE = 2

# ============ 认证体系 ============
# key -> (名称, 所需等级, 所需AC数, 题量, 及格题数, 难度范围)
CERTS = {
    "basic": {
        "name": "青苗认证",
        "level": 3, "ac": 15, "count": 15, "pass": 12,
        "diffs": ("easy", "medium"),
        "desc": "翻土、播种、浇水的基本功：变量、流程控制、字符串与列表，先把地整明白。",
    },
    "advanced": {
        "name": "耕耘认证",
        "level": 5, "ac": 40, "count": 20, "pass": 16,
        "diffs": ("easy", "medium", "hard"),
        "desc": "函数、字典集合、递归与经典算法：会轮作、会养地，一季接一季稳稳产出。",
    },
    "master": {
        "name": "丰收认证",
        "level": 8, "ac": 80, "count": 25, "pass": 21,
        "diffs": ("medium", "hard"),
        "desc": "扎实的数据结构与算法功底：旱涝保收，再硬的板结地也能开垦出结果。",
    },
}

DIFF_LABEL = {"easy": "入门", "medium": "进阶", "hard": "挑战"}
DIFF_ORDER = {"easy": 0, "medium": 1, "hard": 2}


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT UNIQUE NOT NULL,
    pwd_hash   TEXT NOT NULL,
    salt       TEXT NOT NULL,
    nickname   TEXT NOT NULL,
    exp        INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS problems (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    slug     TEXT UNIQUE NOT NULL,
    title    TEXT NOT NULL,
    body     TEXT NOT NULL,
    difficulty TEXT NOT NULL DEFAULT 'easy',
    category TEXT NOT NULL DEFAULT '基础语法',
    starter  TEXT NOT NULL,
    func     TEXT NOT NULL,
    tests    TEXT NOT NULL,
    hint     TEXT NOT NULL DEFAULT '',
    solution TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS submissions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    code       TEXT NOT NULL,
    status     TEXT NOT NULL,
    passed     INTEGER NOT NULL DEFAULT 0,
    total      INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sub_user ON submissions(user_id, problem_id);

CREATE TABLE IF NOT EXISTS wrongs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    problem_id  INTEGER NOT NULL,
    times       INTEGER NOT NULL DEFAULT 1,
    mastered    INTEGER NOT NULL DEFAULT 0,
    last_code   TEXT NOT NULL DEFAULT '',
    last_at     TEXT NOT NULL,
    UNIQUE(user_id, problem_id)
);

CREATE TABLE IF NOT EXISTS favorites (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(user_id, problem_id)
);

CREATE TABLE IF NOT EXISTS checkins (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    day        TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(user_id, day)
);

CREATE TABLE IF NOT EXISTS quizzes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    title       TEXT NOT NULL,
    mode        TEXT NOT NULL DEFAULT 'practice',
    cert_key    TEXT,
    total       INTEGER NOT NULL DEFAULT 0,
    correct     INTEGER NOT NULL DEFAULT 0,
    duration    INTEGER NOT NULL DEFAULT 0,
    passed      INTEGER NOT NULL DEFAULT 0,
    started_at  TEXT NOT NULL,
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS quiz_items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id    INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    sort       INTEGER NOT NULL DEFAULT 0,
    code       TEXT NOT NULL DEFAULT '',
    status     TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS certs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL,
    cert_key  TEXT NOT NULL,
    name      TEXT NOT NULL,
    score     INTEGER NOT NULL,
    cert_no   TEXT UNIQUE NOT NULL,
    issued_at TEXT NOT NULL
);

-- 邀请码：每个用户一条固定邀请码，可重复用于邀请好友
CREATE TABLE IF NOT EXISTS invites (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER UNIQUE NOT NULL,
    code       TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);

-- 好友关系：双向存两条记录，方便查询
CREATE TABLE IF NOT EXISTS friends (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    friend_id  INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(user_id, friend_id)
);
CREATE INDEX IF NOT EXISTS idx_friend_user ON friends(user_id);

-- 学习小队：组队一起打卡
CREATE TABLE IF NOT EXISTS teams (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    slogan     TEXT NOT NULL DEFAULT '',
    code       TEXT UNIQUE NOT NULL,
    owner_id   INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS team_members (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    team_id   INTEGER NOT NULL,
    user_id   INTEGER NOT NULL,
    joined_at TEXT NOT NULL,
    UNIQUE(team_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_team_member ON team_members(team_id);

-- 消息提醒（催打卡、好友加入等）
CREATE TABLE IF NOT EXISTS notices (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    from_id    INTEGER NOT NULL,
    kind       TEXT NOT NULL DEFAULT 'nudge',
    text       TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    is_read    INTEGER NOT NULL DEFAULT 0
);
-- 学习圈：帖子
CREATE TABLE IF NOT EXISTS posts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL,
    category   TEXT NOT NULL DEFAULT '经验分享',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_post_time ON posts(id);

CREATE TABLE IF NOT EXISTS post_likes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id    INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE(post_id, user_id)
);

CREATE TABLE IF NOT EXISTS post_comments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id    INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    content    TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_comment_post ON post_comments(post_id);

-- 苗小序的菜园：地块（每人 6 块，按等级逐步解锁）
CREATE TABLE IF NOT EXISTS plots (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    slot       INTEGER NOT NULL,
    state      TEXT NOT NULL DEFAULT 'empty',  -- empty | plowed | growing
    crop       TEXT NOT NULL DEFAULT '',
    planted_at TEXT,
    watered    INTEGER NOT NULL DEFAULT 0,
    UNIQUE(user_id, slot)
);

-- 菜篮：收获统计
CREATE TABLE IF NOT EXISTS harvests (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    crop    TEXT NOT NULL,
    count   INTEGER NOT NULL DEFAULT 0,
    UNIQUE(user_id, crop)
);
CREATE INDEX IF NOT EXISTS idx_notice_user ON notices(user_id, is_read);

-- 耘野果蔬摊：售卖流水（卖菜换金币）
CREATE TABLE IF NOT EXISTS sales (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    crop       TEXT NOT NULL,
    count      INTEGER NOT NULL,
    unit       INTEGER NOT NULL,
    income     INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sale_user ON sales(user_id);

-- 厨房：做出来的菜肴作品
CREATE TABLE IF NOT EXISTS dishes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    dish_key   TEXT NOT NULL,
    name       TEXT NOT NULL,
    emoji      TEXT NOT NULL,
    score      INTEGER NOT NULL DEFAULT 0,
    energy     INTEGER NOT NULL DEFAULT 0,
    post_id    INTEGER NOT NULL DEFAULT 0,   -- 已发布到学习圈则记下帖子 id
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_dish_user ON dishes(user_id);

-- 种子商店：道具库存（稀有种子 / 肥料）
CREATE TABLE IF NOT EXISTS items (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    item_key   TEXT NOT NULL,
    count      INTEGER NOT NULL DEFAULT 0,
    UNIQUE(user_id, item_key)
);
CREATE INDEX IF NOT EXISTS idx_item_user ON items(user_id);

-- 菜园收获流水（大赛统计耕耘分用）
CREATE TABLE IF NOT EXISTS farm_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    crop       TEXT NOT NULL,
    energy     INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_farmlog_user ON farm_log(user_id, created_at);

-- 耕耘种菜大赛：每赛季一条报名记录，claimed 标记是否已领奖
CREATE TABLE IF NOT EXISTS contest_entries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    season     TEXT NOT NULL,
    joined_at  TEXT NOT NULL,
    claimed    INTEGER NOT NULL DEFAULT 0,
    award      TEXT NOT NULL DEFAULT '',
    UNIQUE(user_id, season)
);
CREATE INDEX IF NOT EXISTS idx_contest_season ON contest_entries(season);
"""


def _columns(table: str) -> List[str]:
    conn = get_conn()
    try:
        return [r["name"] for r in conn.execute(f"PRAGMA table_info({table})")]
    except Exception:
        return []
    finally:
        conn.close()


# 关键列清单：旧版数据库若缺少这些列，说明结构不兼容，需要重建该表
_REQUIRED_COLS = {
    "users": ["pwd_hash", "salt", "nickname", "exp", "created_at"],
    "problems": ["slug", "body", "difficulty", "category", "starter",
                 "func", "tests", "hint", "solution"],
    "submissions": ["passed", "total", "created_at"],
    "wrongs": ["times", "mastered", "last_code", "last_at"],
    "favorites": ["created_at"],
    "checkins": ["day", "created_at"],
    "quizzes": ["mode", "cert_key", "correct", "duration", "passed",
                "started_at", "finished_at"],
    "quiz_items": ["sort", "code", "status"],
    "certs": ["cert_key", "score", "cert_no", "issued_at"],
}


def _ensure_column(table: str, col: str, decl: str) -> None:
    """旧库缺列时补上（ALTER TABLE），不会丢失已有数据。"""
    cols = _columns(table)
    if cols and col not in cols:
        execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")


def init_db() -> None:
    """建表；若检测到旧版不兼容的表结构则自动重建该表。"""
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()

    stale = []
    for table, cols in _REQUIRED_COLS.items():
        existing = _columns(table)
        if existing and not set(cols).issubset(set(existing)):
            stale.append(table)
    if stale:
        executescript("\n".join(f"DROP TABLE IF EXISTS {t};" for t in stale))
        conn = get_conn()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
        finally:
            conn.close()

    # 增量迁移：只补列，不动数据
    _ensure_column("users", "invite_code", "TEXT")
    _ensure_column("users", "energy", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column("users", "coins", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column("plots", "buff", "TEXT")
    # 新手引导：老用户默认 1（已完成、不再弹），新注册由 main.py 显式置 0
    _ensure_column("users", "onboarded", "INTEGER NOT NULL DEFAULT 1")


# ============ 通用助手 ============
def query(sql: str, args=()) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        cur = conn.execute(sql, args)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def query_one(sql: str, args=()) -> Optional[Dict[str, Any]]:
    rows = query(sql, args)
    return rows[0] if rows else None


def execute(sql: str, args=()) -> int:
    """执行写操作，返回 lastrowid。"""
    conn = get_conn()
    try:
        cur = conn.execute(sql, args)
        conn.commit()
        return cur.lastrowid or 0
    finally:
        conn.close()


def executescript(sql: str) -> None:
    conn = get_conn()
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


# ============ 等级 ============
def level_of(exp: int) -> Dict[str, Any]:
    """根据经验值算出等级、称号、以及升到下一级的进度。"""
    cur_lv, cur_name, cur_base = 1, LEVELS[0][2], 0
    for lv, base, name in LEVELS:
        if exp >= base:
            cur_lv, cur_name, cur_base = lv, name, base
    nxt_base = None
    for lv, base, name in LEVELS:
        if base > exp:
            nxt_base = base
            break
    if nxt_base is None:
        return {"level": cur_lv, "name": cur_name, "exp": exp,
                "need": 0, "progress": 100, "maxed": True}
    span = nxt_base - cur_base
    done = exp - cur_base
    return {"level": cur_lv, "name": cur_name, "exp": exp,
            "need": nxt_base, "progress": int(done * 100 / span) if span else 100,
            "maxed": False}


def add_exp(user_id: int, delta: int) -> None:
    execute("UPDATE users SET exp = exp + ? WHERE id = ?", (delta, user_id))


def add_energy(user_id: int, delta: int) -> int:
    """增减能量（不会扣成负数）。返回操作后的余额。"""
    row = query_one("SELECT energy FROM users WHERE id=?", (user_id,))
    cur = row["energy"] if row and row["energy"] is not None else 0
    new = max(0, cur + delta)
    execute("UPDATE users SET energy=? WHERE id=?", (new, user_id))
    return new


def energy_of(user_id: int) -> int:
    row = query_one("SELECT energy FROM users WHERE id=?", (user_id,))
    return (row["energy"] or 0) if row else 0


def add_coins(user_id: int, delta: int) -> int:
    """增减金币（不会扣成负数）。返回操作后的余额。"""
    row = query_one("SELECT coins FROM users WHERE id=?", (user_id,))
    cur = row["coins"] if row and row["coins"] is not None else 0
    new = max(0, cur + delta)
    execute("UPDATE users SET coins=? WHERE id=?", (new, user_id))
    return new


def coins_of(user_id: int) -> int:
    row = query_one("SELECT coins FROM users WHERE id=?", (user_id,))
    return (row["coins"] or 0) if row else 0


def finish_onboard(user_id: int) -> None:
    """标记新手引导已完成（之后不再弹出）。"""
    execute("UPDATE users SET onboarded=1 WHERE id=?", (user_id,))


def load_problem(row: Dict[str, Any]) -> Dict[str, Any]:
    """把 problems 行的 tests JSON 解析出来。"""
    d = dict(row)
    try:
        d["tests"] = json.loads(d["tests"])
    except Exception:
        d["tests"] = []
    return d
