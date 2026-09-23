"""学习圈 —— 用户分享刷题经验、笔记与提问的社区。"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from . import db

CATEGORIES = ["经验分享", "刷题笔记", "求助提问", "资料推荐", "田园食光"]
CATEGORY_ICON = {
    "经验分享": "💡",
    "刷题笔记": "📝",
    "求助提问": "🙋",
    "资料推荐": "📚",
    "田园食光": "🍽️",
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def posts(category: str = "", q: str = "", limit: int = 30,
          viewer: int = 0) -> List[Dict[str, Any]]:
    sql = ("SELECT p.*, u.nickname, u.exp, "
           "(SELECT COUNT(*) FROM post_likes l WHERE l.post_id=p.id) AS likes, "
           "(SELECT COUNT(*) FROM post_comments c WHERE c.post_id=p.id) AS comments "
           "FROM posts p JOIN users u ON u.id=p.user_id WHERE 1=1")
    args: List[Any] = []
    if category:
        sql += " AND p.category=?"
        args.append(category)
    if q:
        sql += " AND (p.title LIKE ? OR p.content LIKE ?)"
        args += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY p.id DESC LIMIT ?"
    args.append(limit)
    rows = db.query(sql, args)
    liked = set()
    if viewer:
        liked = {r["post_id"] for r in db.query(
            "SELECT post_id FROM post_likes WHERE user_id=?", (viewer,))}
    for r in rows:
        r["lv"] = db.level_of(r["exp"])["level"]
        r["icon"] = CATEGORY_ICON.get(r["category"], "📌")
        r["liked"] = r["id"] in liked
        r["mine"] = viewer and r["user_id"] == viewer
        r["brief"] = (r["content"][:80] + "…") if len(r["content"]) > 80 else r["content"]
        r["time"] = r["created_at"][5:16]
    return rows


def post_detail(pid: int, viewer: int = 0) -> Optional[Dict[str, Any]]:
    row = db.query_one(
        "SELECT p.*, u.nickname, u.exp, "
        "(SELECT COUNT(*) FROM post_likes l WHERE l.post_id=p.id) AS likes "
        "FROM posts p JOIN users u ON u.id=p.user_id WHERE p.id=?", (pid,))
    if not row:
        return None
    row["lv"] = db.level_of(row["exp"])["level"]
    row["icon"] = CATEGORY_ICON.get(row["category"], "📌")
    row["liked"] = bool(viewer and db.query_one(
        "SELECT id FROM post_likes WHERE post_id=? AND user_id=?", (pid, viewer)))
    row["mine"] = viewer and row["user_id"] == viewer
    row["comments"] = comments_of(pid)
    return row


def comments_of(pid: int) -> List[Dict[str, Any]]:
    rows = db.query(
        "SELECT c.*, u.nickname, u.exp FROM post_comments c "
        "JOIN users u ON u.id=c.user_id WHERE c.post_id=? ORDER BY c.id", (pid,))
    for r in rows:
        r["lv"] = db.level_of(r["exp"])["level"]
        r["time"] = r["created_at"][5:16]
    return rows


def _today_count(table: str, user_id: int) -> int:
    r = db.query_one(
        f"SELECT COUNT(*) AS c FROM {table} WHERE user_id=? AND created_at >= ?",
        (user_id, _today() + " 00:00:00"))
    return r["c"] if r else 0


def create_post(user_id: int, title: str, content: str, category: str) -> Dict[str, Any]:
    title = (title or "").strip()
    content = (content or "").strip()
    if len(title) < 2 or len(title) > 40:
        return {"ok": False, "msg": "标题需为 2~40 个字"}
    if len(content) < 5 or len(content) > 3000:
        return {"ok": False, "msg": "正文需为 5~3000 个字"}
    if category not in CATEGORIES:
        category = CATEGORIES[0]
    pid = db.execute(
        "INSERT INTO posts(user_id, title, content, category, created_at) "
        "VALUES (?,?,?,?,?)", (user_id, title, content, category, _now()))
    bonus = 0
    if _today_count("posts", user_id) <= 3:      # 每天前 3 帖给能量
        bonus = db.ENERGY_POST
        db.add_energy(user_id, bonus)
    return {"ok": True, "msg": "发布成功", "id": pid, "bonus": bonus,
            "energy": db.energy_of(user_id)}


def delete_post(pid: int, user_id: int) -> bool:
    row = db.query_one("SELECT user_id FROM posts WHERE id=?", (pid,))
    if not row or row["user_id"] != user_id:
        return False
    db.execute("DELETE FROM post_likes WHERE post_id=?", (pid,))
    db.execute("DELETE FROM post_comments WHERE post_id=?", (pid,))
    db.execute("DELETE FROM posts WHERE id=?", (pid,))
    return True


def toggle_like(pid: int, user_id: int) -> Dict[str, Any]:
    if not db.query_one("SELECT id FROM posts WHERE id=?", (pid,)):
        return {"ok": False, "msg": "帖子不存在"}
    row = db.query_one("SELECT id FROM post_likes WHERE post_id=? AND user_id=?",
                       (pid, user_id))
    if row:
        db.execute("DELETE FROM post_likes WHERE id=?", (row["id"],))
        liked = False
    else:
        db.execute("INSERT INTO post_likes(post_id, user_id, created_at) VALUES (?,?,?)",
                   (pid, user_id, _now()))
        liked = True
        owner = db.query_one("SELECT user_id FROM posts WHERE id=?", (pid,))
        if owner and owner["user_id"] != user_id:
            db.add_energy(owner["user_id"], 1)      # 被点赞的人得 1 点能量
    n = db.query_one("SELECT COUNT(*) AS c FROM post_likes WHERE post_id=?", (pid,))["c"]
    return {"ok": True, "liked": liked, "likes": n}


def add_comment(pid: int, user_id: int, content: str) -> Dict[str, Any]:
    content = (content or "").strip()
    if not db.query_one("SELECT id FROM posts WHERE id=?", (pid,)):
        return {"ok": False, "msg": "帖子不存在"}
    if len(content) < 1 or len(content) > 500:
        return {"ok": False, "msg": "评论需为 1~500 个字"}
    db.execute("INSERT INTO post_comments(post_id, user_id, content, created_at) "
               "VALUES (?,?,?,?)", (pid, user_id, content, _now()))
    bonus = 0
    if _today_count("post_comments", user_id) <= 5:
        bonus = db.ENERGY_COMMENT
        db.add_energy(user_id, bonus)
    return {"ok": True, "msg": "评论成功", "bonus": bonus,
            "energy": db.energy_of(user_id)}


def delete_comment(cid: int, user_id: int) -> bool:
    row = db.query_one("SELECT user_id FROM post_comments WHERE id=?", (cid,))
    if not row or row["user_id"] != user_id:
        return False
    db.execute("DELETE FROM post_comments WHERE id=?", (cid,))
    return True


def stats() -> Dict[str, int]:
    p = db.query_one("SELECT COUNT(*) AS c FROM posts")["c"]
    c = db.query_one("SELECT COUNT(*) AS c FROM post_comments")["c"]
    return {"posts": p, "comments": c}
