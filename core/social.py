"""社交模块：邀请码、好友、学习小队、打卡提醒。

好友关系在 friends 表里双向存两条记录（A→B、B→A），
这样「我的好友」「好友动态」都能用单条查询搞定。
"""
import secrets
import string
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from . import db

# 邀请码/小队码只用这些字符，避免 0/O、1/I 看错
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _code(n: int) -> str:
    return "".join(secrets.choice(_ALPHABET) for _ in range(n))


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==================== 邀请码 ====================
def ensure_invite_code(user_id: int) -> str:
    """返回该用户的专属邀请码，没有就生成一个。"""
    row = db.query_one("SELECT code FROM invites WHERE user_id=?", (user_id,))
    if row:
        return row["code"]
    for _ in range(20):
        code = _code(8)
        if not db.query_one("SELECT id FROM invites WHERE code=?", (code,)):
            db.execute("INSERT INTO invites(user_id, code, created_at) VALUES (?,?,?)",
                       (user_id, code, _now()))
            db.execute("UPDATE users SET invite_code=? WHERE id=?", (code, user_id))
            return code
    raise RuntimeError("生成邀请码失败")


def user_by_code(code: str) -> Optional[Dict[str, Any]]:
    code = (code or "").strip().upper()
    if not code:
        return None
    return db.query_one(
        "SELECT u.* FROM invites i JOIN users u ON u.id = i.user_id WHERE i.code=?",
        (code,))


def code_of(user_id: int) -> str:
    row = db.query_one("SELECT code FROM invites WHERE user_id=?", (user_id,))
    return row["code"] if row else ensure_invite_code(user_id)


# ==================== 好友 ====================
def add_friend(a: int, b: int) -> bool:
    """建立双向好友关系。返回 True 表示新建立，False 表示已经是好友。"""
    if a == b:
        return False
    if not db.query_one("SELECT id FROM users WHERE id=?", (b,)):
        return False
    existed = db.query_one("SELECT id FROM friends WHERE user_id=? AND friend_id=?", (a, b))
    if existed:
        return False
    now = _now()
    db.execute("INSERT INTO friends(user_id, friend_id, created_at) VALUES (?,?,?)", (a, b, now))
    db.execute("INSERT INTO friends(user_id, friend_id, created_at) VALUES (?,?,?)", (b, a, now))
    return True


def remove_friend(a: int, b: int) -> None:
    db.execute("DELETE FROM friends WHERE user_id=? AND friend_id=?", (a, b))
    db.execute("DELETE FROM friends WHERE user_id=? AND friend_id=?", (b, a))


def is_friend(a: int, b: int) -> bool:
    return bool(db.query_one("SELECT id FROM friends WHERE user_id=? AND friend_id=?", (a, b)))


def friend_ids(user_id: int) -> List[int]:
    return [r["friend_id"] for r in
            db.query("SELECT friend_id FROM friends WHERE user_id=?", (user_id,))]


def friends_of(user_id: int) -> List[Dict[str, Any]]:
    """好友列表，附带等级、连续打卡、今日是否打卡、AC 数。"""
    today = str(date.today())
    rows = db.query(
        "SELECT u.id, u.nickname, u.username, u.exp FROM friends f "
        "JOIN users u ON u.id = f.friend_id WHERE f.user_id=? ORDER BY f.id DESC",
        (user_id,))
    out = []
    for r in rows:
        lv = db.level_of(r["exp"])
        ac = len(db.query(
            "SELECT DISTINCT problem_id FROM submissions WHERE user_id=? AND status='accepted'",
            (r["id"],)))
        out.append({
            "id": r["id"],
            "nickname": r["nickname"],
            "username": r["username"],
            "level": lv["level"],
            "level_name": lv["name"],
            "exp": r["exp"],
            "ac": ac,
            "streak": _streak(r["id"]),
            "today": bool(db.query_one("SELECT id FROM checkins WHERE user_id=? AND day=?",
                                       (r["id"], today))),
        })
    # 今天打卡的排前面，其次连续天数多的
    out.sort(key=lambda x: (not x["today"], -x["streak"], -x["exp"]))
    return out


def _streak(user_id: int) -> int:
    days = {r["day"] for r in db.query("SELECT day FROM checkins WHERE user_id=?", (user_id,))}
    if not days:
        return 0
    today = date.today()
    cur = today if str(today) in days else today - timedelta(days=1)
    if str(cur) not in days:
        return 0
    n = 0
    while str(cur) in days:
        n += 1
        cur -= timedelta(days=1)
    return n


def feed(user_id: int, limit: int = 12) -> List[Dict[str, Any]]:
    """好友动态：最近通过/提交的题目。"""
    ids = friend_ids(user_id)
    if not ids:
        return []
    ph = ",".join("?" * len(ids))
    return db.query(
        f"SELECT s.status, s.created_at, p.id AS pid, p.title, p.difficulty, "
        f"u.nickname, u.id AS uid FROM submissions s "
        f"JOIN problems p ON p.id = s.problem_id JOIN users u ON u.id = s.user_id "
        f"WHERE s.user_id IN ({ph}) ORDER BY s.id DESC LIMIT ?",
        ids + [limit])


def week_board(user_id: int) -> List[Dict[str, Any]]:
    """好友本周打卡排行（含自己）。"""
    ids = friend_ids(user_id) + [user_id]
    if not ids:
        return []
    since = str(date.today() - timedelta(days=date.today().weekday()))
    ph = ",".join("?" * len(ids))
    rows = db.query(
        f"SELECT u.id, u.nickname, u.exp, COUNT(c.id) AS cnt FROM users u "
        f"LEFT JOIN checkins c ON c.user_id = u.id AND c.day >= ? "
        f"WHERE u.id IN ({ph}) GROUP BY u.id ORDER BY cnt DESC, u.exp DESC",
        [since] + ids)
    for i, r in enumerate(rows):
        r["rank"] = i + 1
        r["me"] = r["id"] == user_id
        r["streak"] = _streak(r["id"])
        r["level"] = db.level_of(r["exp"])["level"]
    return rows


def checked_today(user_id: int) -> bool:
    today = str(date.today())
    return bool(db.query_one("SELECT id FROM checkins WHERE user_id=? AND day=?",
                             (user_id, today)))


def nudge_count_today(user_id: int) -> int:
    """今天已经催过多少人（防止刷屏）。"""
    today = str(date.today())
    r = db.query_one(
        "SELECT COUNT(*) AS c FROM notices WHERE from_id=? AND kind='nudge' "
        "AND created_at >= ?", (user_id, today + " 00:00:00"))
    return r["c"] if r else 0


def send_notice(to_id: int, from_id: int, text: str, kind: str = "nudge") -> int:
    return db.execute(
        "INSERT INTO notices(user_id, from_id, kind, text, created_at, is_read) "
        "VALUES (?,?,?,?,?,0)", (to_id, from_id, kind, text, _now()))


def unread_count(user_id: int) -> int:
    r = db.query_one("SELECT COUNT(*) AS c FROM notices WHERE user_id=? AND is_read=0",
                     (user_id,))
    return r["c"] if r else 0


def notices_of(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    return db.query(
        "SELECT n.*, u.nickname AS from_name FROM notices n "
        "JOIN users u ON u.id = n.from_id WHERE n.user_id=? "
        "ORDER BY n.id DESC LIMIT ?", (user_id, limit))


def mark_read(user_id: int) -> None:
    db.execute("UPDATE notices SET is_read=1 WHERE user_id=? AND is_read=0", (user_id,))


# ==================== 学习小队 ====================
def create_team(owner_id: int, name: str, slogan: str = "") -> Dict[str, Any]:
    for _ in range(20):
        code = _code(6)
        if not db.query_one("SELECT id FROM teams WHERE code=?", (code,)):
            break
    else:
        raise RuntimeError("生成小队码失败")
    tid = db.execute(
        "INSERT INTO teams(name, slogan, code, owner_id, created_at) VALUES (?,?,?,?,?)",
        (name.strip(), (slogan or "").strip(), code, owner_id, _now()))
    db.execute("INSERT INTO team_members(team_id, user_id, joined_at) VALUES (?,?,?)",
               (tid, owner_id, _now()))
    return team_by_id(tid)


def team_by_id(tid: int) -> Optional[Dict[str, Any]]:
    return db.query_one("SELECT * FROM teams WHERE id=?", (tid,))


def team_by_code(code: str) -> Optional[Dict[str, Any]]:
    code = (code or "").strip().upper()
    if not code:
        return None
    return db.query_one("SELECT * FROM teams WHERE code=?", (code,))


def join_team(user_id: int, team_id: int) -> bool:
    if db.query_one("SELECT id FROM team_members WHERE team_id=? AND user_id=?",
                    (team_id, user_id)):
        return False
    db.execute("INSERT INTO team_members(team_id, user_id, joined_at) VALUES (?,?,?)",
               (team_id, user_id, _now()))
    return True


def leave_team(user_id: int, team_id: int) -> None:
    db.execute("DELETE FROM team_members WHERE team_id=? AND user_id=?", (team_id, user_id))


def teams_of(user_id: int) -> List[Dict[str, Any]]:
    rows = db.query(
        "SELECT t.*, (SELECT COUNT(*) FROM team_members m WHERE m.team_id=t.id) AS members "
        "FROM teams t JOIN team_members m2 ON m2.team_id = t.id "
        "WHERE m2.user_id=? ORDER BY t.id DESC", (user_id,))
    return rows


def team_members(team_id: int) -> List[Dict[str, Any]]:
    """小队成员 + 今日打卡状态 + 连续天数。"""
    today = str(date.today())
    rows = db.query(
        "SELECT u.id, u.nickname, u.exp, m.joined_at FROM team_members m "
        "JOIN users u ON u.id = m.user_id WHERE m.team_id=? ORDER BY m.id",
        (team_id,))
    out = []
    for r in rows:
        lv = db.level_of(r["exp"])
        out.append({
            "id": r["id"],
            "nickname": r["nickname"],
            "level": lv["level"],
            "level_name": lv["name"],
            "exp": r["exp"],
            "streak": _streak(r["id"]),
            "today": bool(db.query_one("SELECT id FROM checkins WHERE user_id=? AND day=?",
                                       (r["id"], today))),
            "joined_at": r["joined_at"],
        })
    out.sort(key=lambda x: (not x["today"], -x["streak"]))
    return out


def team_checkin_rate(team_id: int) -> int:
    """小队今日打卡率（百分比）。"""
    ms = team_members(team_id)
    if not ms:
        return 0
    return round(sum(1 for m in ms if m["today"]) * 100 / len(ms))
