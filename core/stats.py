"""用户统计：AC 数、打卡连续天数、分类进度等。"""
from typing import Dict, List, Set
from datetime import date, timedelta

from . import db


def solved_ids(user_id: int) -> Set[int]:
    rows = db.query(
        "SELECT DISTINCT problem_id FROM submissions WHERE user_id=? AND status='accepted'",
        (user_id,))
    return {r["problem_id"] for r in rows}


def ac_count(user_id: int) -> int:
    return len(solved_ids(user_id))


def submission_count(user_id: int) -> int:
    r = db.query_one("SELECT COUNT(*) AS c FROM submissions WHERE user_id=?", (user_id,))
    return r["c"] if r else 0


def wrong_count(user_id: int) -> int:
    r = db.query_one(
        "SELECT COUNT(*) AS c FROM wrongs WHERE user_id=? AND mastered=0", (user_id,))
    return r["c"] if r else 0


def favorite_count(user_id: int) -> int:
    r = db.query_one("SELECT COUNT(*) AS c FROM favorites WHERE user_id=?", (user_id,))
    return r["c"] if r else 0


def checkin_days(user_id: int) -> List[str]:
    rows = db.query("SELECT day FROM checkins WHERE user_id=? ORDER BY day", (user_id,))
    return [r["day"] for r in rows]


def streak(user_id: int) -> int:
    """连续打卡天数（算到今天；今天没打卡则从昨天算起）。"""
    days = set(checkin_days(user_id))
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


def checked_today(user_id: int) -> bool:
    return str(date.today()) in set(checkin_days(user_id))


def summary(user_id: int) -> Dict:
    """首页仪表盘用的一次性统计。"""
    solved = solved_ids(user_id)
    total_problems = db.query_one("SELECT COUNT(*) AS c FROM problems")["c"]
    return {
        "ac": len(solved),
        "total_problems": total_problems,
        "submissions": submission_count(user_id),
        "wrongs": wrong_count(user_id),
        "favorites": favorite_count(user_id),
        "streak": streak(user_id),
        "checkin_total": len(checkin_days(user_id)),
        "checked_today": checked_today(user_id),
        "rate": round(len(solved) * 100 / total_problems) if total_problems else 0,
    }


def category_progress(user_id: int) -> List[Dict]:
    """每个分类的进度。"""
    solved = solved_ids(user_id)
    rows = db.query("SELECT category, COUNT(*) AS c FROM problems GROUP BY category")
    out = []
    for r in rows:
        done = db.query(
            "SELECT COUNT(DISTINCT problem_id) AS c FROM submissions s "
            "JOIN problems p ON p.id = s.problem_id "
            "WHERE s.user_id=? AND s.status='accepted' AND p.category=?",
            (user_id, r["category"]))[0]["c"]
        out.append({
            "category": r["category"], "total": r["c"], "solved": done,
            "percent": round(done * 100 / r["c"]) if r["c"] else 0,
        })
    return out


def recent_activity(user_id: int, limit: int = 8) -> List[Dict]:
    return db.query(
        "SELECT s.status, s.created_at, p.id, p.title, p.difficulty "
        "FROM submissions s JOIN problems p ON p.id = s.problem_id "
        "WHERE s.user_id=? ORDER BY s.id DESC LIMIT ?", (user_id, limit))
