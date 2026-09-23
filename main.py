"""Python 刷题平台 —— FastAPI 主程序。

功能：注册登录 / 题库 / 在线判题 / 错题本 / 收藏 / 每日打卡 /
      限时测验 / 等级经验 / 认证考试与证书 / 排行榜 / AI 助教(DeepSeek)
"""
import json
import random
import secrets
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from core import db, auth, judge, ai, stats, social, farm, circle, market, kitchen
from core import shop, contest, blessing
from core.seed import seed_problems, CATEGORIES

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Python 刷题平台")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 启动即建表 + 灌题
db.init_db()
seed_problems()


# ==================== 通用助手 ====================
def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_user(request: Request):
    return auth.get_current_user(request)


def api_user(request: Request):
    """API 用：未登录直接返回 401 JSON。"""
    u = auth.get_current_user(request)
    if not u:
        raise HTTPException(status_code=401, detail="请先登录")
    return u


def signin_payload(request: Request, u: dict) -> Optional[dict]:
    """登录后的「每日签到弹窗」数据。

    每天只弹一次：当天弹过会写 cookie `pop_signin`，第二天再弹。
    已签到时展示祝贺语，未签到时展示邀请语，两种情况都带祝福语。
    """
    try:
        today = str(date.today())
        # 当天弹过、或刚注册（要弹新用户欢迎）时都不再弹签到窗
        if request.cookies.get("pop_signin") == today:
            return None
        if request.cookies.get("welcome_new") == "1":
            return None
        days = stats.checkin_days(u["id"])
        checked = today in set(days)
        info = blessing.daily(u, stats.streak(u["id"]), len(days), checked)
        info["xp"] = db.XP_CHECKIN
        info["energy"] = db.ENERGY_CHECKIN
        return info
    except Exception:
        return None


def render(request: Request, name: str, ctx: Optional[dict] = None) -> HTMLResponse:
    """渲染模板，自动注入当前用户与等级信息。"""
    u = get_user(request)
    base = {"request": request, "user": u, "ai_on": ai.is_enabled(),
            "ai_demo": ai.is_demo(),
            "categories": CATEGORIES, "diff_label": db.DIFF_LABEL,
            "unread": social.unread_count(u["id"]) if u else 0,
            "energy": db.energy_of(u["id"]) if u else 0,
            "coins": db.coins_of(u["id"]) if u else 0,
            "ready_crops": farm.ready_count(u["id"]) if u else 0}
    try:
        base["season"] = contest.current()      # 顶部海报 Banner 要用当季主题
    except Exception:
        base["season"] = {"crop_emoji": "🌾", "crop_name": "水稻", "days_left": 7,
                          "title": "耕耘季", "key": ""}
    if u:
        base["lv"] = db.level_of(u["exp"])
    base["signin"] = signin_payload(request, u) if u else None
    base["welcome_new"] = bool(u) and request.cookies.get("welcome_new") == "1"
    base["intro"] = blessing.NEW_USER_INTRO
    base["need_onboard"] = bool(u) and int(u.get("onboarded") or 0) == 0
    if ctx:
        base.update(ctx)
    # Starlette >= 1.6 要求 TemplateResponse(request, name, context)；
    # 0.29~0.4x 则是 TemplateResponse(name, context)。两种都兼容。
    # 只有「签名不匹配」的 TypeError 才回退，模板内部的报错要照常抛出。
    try:
        return templates.TemplateResponse(request, name, base)
    except TypeError as e:
        msg = str(e)
        if "argument" in msg or "positional" in msg or "required" in msg:
            return templates.TemplateResponse(name, base)
        raise


def json_ok(data: dict = None, msg: str = "ok"):
    return JSONResponse({"code": 0, "msg": msg, "data": data or {}})


def json_fail(msg: str, code: int = 1):
    return JSONResponse({"code": code, "msg": msg, "data": {}})


def problem_by_id(pid: int):
    row = db.query_one("SELECT * FROM problems WHERE id=?", (pid,))
    return db.load_problem(row) if row else None


# ==================== 首页 / 登录 / 注册 ====================
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    u = get_user(request)
    if not u:
        return render(request, "landing.html")
    s = stats.summary(u["id"])
    return render(request, "home.html", {
        "s": s,
        "progress": stats.category_progress(u["id"]),
        "recent": stats.recent_activity(u["id"]),
        "checkin_days": [d for d in stats.checkin_days(u["id"])],
        "garden": farm.garden(u["id"]),
        "unlocked": farm.slots_of(u["id"]),
        "total_slots": farm.TOTAL_SLOTS,
        "basket": farm.basket(u["id"]),
        "items": shop.catalog(u["id"]),
        "inv": shop.inventory(u["id"]),
        "season": contest.current(),
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if get_user(request):
        return RedirectResponse("/", status_code=302)
    return render(request, "login.html")


@app.post("/login")
async def login_submit(request: Request, username: str = Form(...),
                       password: str = Form(...)):
    row = db.query_one("SELECT * FROM users WHERE username=?", (username.strip(),))
    if not row or not auth.verify_password(password, row["pwd_hash"], row["salt"]):
        return render(request, "login.html", {"error": "用户名或密码不正确"})
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie("session", auth.create_session_token(row["id"]),
                    max_age=auth.SESSION_TTL, httponly=True, samesite="lax")
    return resp


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, invite: str = ""):
    if get_user(request):
        return RedirectResponse("/", status_code=302)
    inviter = social.user_by_code(invite) if invite else None
    return render(request, "register.html", {"invite": invite, "inviter": inviter})


@app.post("/register")
async def register_submit(request: Request, username: str = Form(...),
                          password: str = Form(...), nickname: str = Form(""),
                          invite: str = Form("")):
    username = username.strip()
    nickname = (nickname or "").strip() or username
    if len(username) < 3 or len(username) > 20:
        return render(request, "register.html", {"error": "用户名需为 3~20 个字符",
                                                 "invite": invite})
    if len(password) < 6:
        return render(request, "register.html", {"error": "密码至少 6 位", "invite": invite})
    if db.query_one("SELECT id FROM users WHERE username=?", (username,)):
        return render(request, "register.html", {"error": "该用户名已被注册",
                                                 "invite": invite})
    h, salt = auth.hash_password(password)
    uid = db.execute(
        "INSERT INTO users(username, pwd_hash, salt, nickname, exp, created_at) "
        "VALUES (?,?,?,?,0,?)", (username, h, salt, nickname, now_str()))
    # 新用户：开启「首次登录分步新手引导」（老用户默认已完成）
    db.execute("UPDATE users SET onboarded=0 WHERE id=?", (uid,))

    # 通过邀请链接注册：自动互加好友，并给双方发一条提醒
    inviter = social.user_by_code(invite) if invite else None
    if inviter and inviter["id"] != uid:
        social.add_friend(uid, inviter["id"])
        social.send_notice(uid, inviter["id"],
                           f"你和 {inviter['nickname']} 已成为好友，一起刷题打卡吧！", "friend")
        social.send_notice(inviter["id"], uid,
                           f"{nickname} 通过你的邀请链接注册啦，快去打个招呼～", "friend")

    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie("session", auth.create_session_token(uid),
                    max_age=auth.SESSION_TTL, httponly=True, samesite="lax")
    # 仅「首次注册」后弹一次新用户欢迎；登录不会带这个 cookie
    resp.set_cookie("welcome_new", "1", max_age=180, httponly=False, samesite="lax")
    return resp


@app.post("/logout")
async def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("session")
    return resp


# ==================== 题库 ====================
@app.get("/problems", response_class=HTMLResponse)
async def problems(request: Request, q: str = "", category: str = "",
                   difficulty: str = "", status: str = ""):
    u = get_user(request)
    sql = "SELECT * FROM problems WHERE 1=1"
    args = []
    if q:
        sql += " AND (title LIKE ? OR body LIKE ?)"
        args += [f"%{q}%", f"%{q}%"]
    if category:
        sql += " AND category=?"
        args.append(category)
    if difficulty:
        sql += " AND difficulty=?"
        args.append(difficulty)
    sql += " ORDER BY id"
    rows = [db.load_problem(r) for r in db.query(sql, args)]

    solved = stats.solved_ids(u["id"]) if u else set()
    favs = set()
    wrongs = set()
    if u:
        favs = {r["problem_id"] for r in db.query(
            "SELECT problem_id FROM favorites WHERE user_id=?", (u["id"],))}
        wrongs = {r["problem_id"] for r in db.query(
            "SELECT problem_id FROM wrongs WHERE user_id=? AND mastered=0", (u["id"],))}

    for p in rows:
        p["solved"] = p["id"] in solved
        p["fav"] = p["id"] in favs
        p["wrong"] = p["id"] in wrongs
        p["diff_text"] = db.DIFF_LABEL.get(p["difficulty"], p["difficulty"])

    if status == "solved":
        rows = [p for p in rows if p["solved"]]
    elif status == "unsolved":
        rows = [p for p in rows if not p["solved"]]
    elif status == "wrong":
        rows = [p for p in rows if p["wrong"]]

    return render(request, "problems.html", {
        "rows": rows, "q": q, "category": category,
        "difficulty": difficulty, "status": status,
        "total": len(rows),
    })


@app.get("/problem/{pid}", response_class=HTMLResponse)
async def problem_page(request: Request, pid: int):
    p = problem_by_id(pid)
    if not p:
        raise HTTPException(404, "题目不存在")
    u = get_user(request)
    ctx = {"p": p, "diff_text": db.DIFF_LABEL.get(p["difficulty"], p["difficulty"])}
    if u:
        ctx["fav"] = bool(db.query_one(
            "SELECT id FROM favorites WHERE user_id=? AND problem_id=?", (u["id"], pid)))
        ctx["solved"] = bool(db.query_one(
            "SELECT id FROM submissions WHERE user_id=? AND problem_id=? "
            "AND status='accepted'", (u["id"], pid)))
        ctx["history"] = db.query(
            "SELECT status, passed, total, created_at FROM submissions "
            "WHERE user_id=? AND problem_id=? ORDER BY id DESC LIMIT 5", (u["id"], pid))
        last = db.query_one(
            "SELECT code FROM submissions WHERE user_id=? AND problem_id=? "
            "ORDER BY id DESC LIMIT 1", (u["id"], pid))
        ctx["code"] = last["code"] if last else p["starter"]
    else:
        ctx["fav"] = False
        ctx["solved"] = False
        ctx["history"] = []
        ctx["code"] = p["starter"]
    return render(request, "problem.html", ctx)


class CodeBody(BaseModel):
    """通用请求体：pid + 可选代码。收藏/错题等接口只用到 pid。"""
    pid: int = 0
    code: str = ""


@app.post("/api/run")
async def api_run(body: CodeBody):
    """运行代码（不记录、不加经验）。"""
    p = problem_by_id(body.pid)
    if not p:
        return json_fail("题目不存在")
    res = judge.run_code(body.code, p["func"], p["tests"])
    return json_ok(res)


@app.post("/api/submit")
async def api_submit(request: Request, body: CodeBody):
    """提交判题：记录结果、更新错题本、结算经验。"""
    u = api_user(request)
    p = problem_by_id(body.pid)
    if not p:
        return json_fail("题目不存在")

    res = judge.run_code(body.code, p["func"], p["tests"])
    status = res["status"]
    passed, total = res["passed"], res["total"]

    db.execute(
        "INSERT INTO submissions(user_id, problem_id, code, status, passed, total, created_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (u["id"], p["id"], body.code, status, passed, total, now_str()))

    gained = 0
    e_gain = 0
    action = ""
    if status == "accepted":
        before = db.query_one(
            "SELECT COUNT(*) AS c FROM submissions WHERE user_id=? AND problem_id=? "
            "AND status='accepted'", (u["id"], p["id"]))["c"]
        gained = db.XP_FIRST_AC if before <= 1 else db.XP_REPEAT_AC
        e_gain = db.ENERGY_FIRST_AC if before <= 1 else db.ENERGY_REPEAT_AC
        db.add_exp(u["id"], gained)
        db.add_energy(u["id"], e_gain)
        # 通过后从错题本移除（或标记已掌握）
        db.execute("DELETE FROM wrongs WHERE user_id=? AND problem_id=?", (u["id"], p["id"]))
        action = "accepted"
    else:
        row = db.query_one(
            "SELECT id, times FROM wrongs WHERE user_id=? AND problem_id=?", (u["id"], p["id"]))
        if row:
            db.execute("UPDATE wrongs SET times=times+1, last_code=?, last_at=?, mastered=0 "
                       "WHERE id=?", (body.code, now_str(), row["id"]))
        else:
            db.execute("INSERT INTO wrongs(user_id, problem_id, times, last_code, last_at) "
                       "VALUES (?,?,1,?,?)", (u["id"], p["id"], body.code, now_str()))
        action = "wrong"

    new_user = db.query_one("SELECT * FROM users WHERE id=?", (u["id"],))
    return json_ok({
        "result": res, "action": action, "gained": gained, "e_gain": e_gain,
        "energy": db.energy_of(u["id"]),
        "level": db.level_of(new_user["exp"]),
    })


# ==================== 错题本 ====================
@app.get("/wrongs", response_class=HTMLResponse)
async def wrongs_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    rows = db.query(
        "SELECT w.*, p.title, p.difficulty, p.category, p.slug FROM wrongs w "
        "JOIN problems p ON p.id = w.problem_id "
        "WHERE w.user_id=? AND w.mastered=0 ORDER BY w.last_at DESC", (u["id"],))
    done = db.query(
        "SELECT w.*, p.title, p.difficulty FROM wrongs w JOIN problems p ON p.id=w.problem_id "
        "WHERE w.user_id=? AND w.mastered=1 ORDER BY w.last_at DESC LIMIT 20", (u["id"],))
    for r in rows:
        r["diff_text"] = db.DIFF_LABEL.get(r["difficulty"], r["difficulty"])
    return render(request, "wrongs.html", {"rows": rows, "done": done})


@app.post("/api/wrong/master")
async def wrong_master(request: Request, body: CodeBody):
    u = api_user(request)
    db.execute("UPDATE wrongs SET mastered=1 WHERE user_id=? AND problem_id=?",
               (u["id"], body.pid))
    return json_ok(msg="已标记为掌握")


@app.post("/api/wrong/remove")
async def wrong_remove(request: Request, body: CodeBody):
    u = api_user(request)
    db.execute("DELETE FROM wrongs WHERE user_id=? AND problem_id=?", (u["id"], body.pid))
    return json_ok(msg="已移出错题本")


# ==================== 收藏 ====================
@app.get("/favorites", response_class=HTMLResponse)
async def favorites_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    rows = db.query(
        "SELECT p.*, f.created_at FROM favorites f JOIN problems p ON p.id=f.problem_id "
        "WHERE f.user_id=? ORDER BY f.id DESC", (u["id"],))
    rows = [db.load_problem(r) for r in rows]
    solved = stats.solved_ids(u["id"])
    for r in rows:
        r["solved"] = r["id"] in solved
        r["diff_text"] = db.DIFF_LABEL.get(r["difficulty"], r["difficulty"])
    return render(request, "favorites.html", {"rows": rows})


@app.post("/api/favorite")
async def api_favorite(request: Request, body: CodeBody):
    u = api_user(request)
    row = db.query_one("SELECT id FROM favorites WHERE user_id=? AND problem_id=?",
                       (u["id"], body.pid))
    if row:
        db.execute("DELETE FROM favorites WHERE id=?", (row["id"],))
        return json_ok({"fav": False}, "已取消收藏")
    db.execute("INSERT INTO favorites(user_id, problem_id, created_at) VALUES (?,?,?)",
               (u["id"], body.pid, now_str()))
    return json_ok({"fav": True}, "收藏成功")


# ==================== 每日打卡 ====================
@app.get("/checkin", response_class=HTMLResponse)
async def checkin_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    days = set(stats.checkin_days(u["id"]))
    today = date.today()
    # 生成最近 5 周（35 天）的日历数据，按周对齐（周一开头）
    start = today - timedelta(days=today.weekday() + 28)
    cal = []
    for i in range(35):
        d = start + timedelta(days=i)
        cal.append({"day": str(d), "n": d.day, "done": str(d) in days,
                    "today": d == today, "future": d > today})
    board = db.query(
        "SELECT u.nickname, COUNT(c.id) AS cnt FROM checkins c JOIN users u ON u.id=c.user_id "
        "WHERE c.day >= ? GROUP BY c.user_id ORDER BY cnt DESC LIMIT 10",
        (str(today - timedelta(days=30)),))
    # 好友今日打卡墙
    fids = social.friend_ids(u["id"])
    wall = []
    if fids:
        ph = ",".join("?" * len(fids))
        wall = db.query(
            f"SELECT u.id, u.nickname, u.exp, "
            f"MAX(CASE WHEN c.day=? THEN 1 ELSE 0 END) AS today "
            f"FROM users u LEFT JOIN checkins c ON c.user_id=u.id "
            f"WHERE u.id IN ({ph}) GROUP BY u.id ORDER BY today DESC, u.exp DESC",
            [str(today)] + fids)
        for w in wall:
            w["streak"] = social._streak(w["id"])
    return render(request, "checkin.html", {
        "cal": cal,
        "streak": stats.streak(u["id"]),
        "total": len(days),
        "checked_today": str(today) in days,
        "board": board,
        "wall": wall,
    })


@app.post("/api/checkin")
async def api_checkin(request: Request):
    u = api_user(request)
    today = str(date.today())
    if db.query_one("SELECT id FROM checkins WHERE user_id=? AND day=?", (u["id"], today)):
        return json_fail("今天已经打过卡啦，明天再来～")
    db.execute("INSERT INTO checkins(user_id, day, created_at) VALUES (?,?,?)",
               (u["id"], today, now_str()))
    db.add_exp(u["id"], db.XP_CHECKIN)
    db.add_energy(u["id"], db.ENERGY_CHECKIN)
    nu = db.query_one("SELECT * FROM users WHERE id=?", (u["id"],))
    streak = stats.streak(u["id"])
    b = blessing.daily(u, streak, len(stats.checkin_days(u["id"])), True)
    return json_ok({"streak": streak, "level": db.level_of(nu["exp"]),
                    "gained": db.XP_CHECKIN, "e_gain": db.ENERGY_CHECKIN,
                    "energy": db.energy_of(u["id"]),
                    "bless": b["bless"], "emoji": b["emoji"], "head": b["head"]},
                   f"打卡成功，能量 +{db.ENERGY_CHECKIN}")


@app.get("/api/blessing")
async def api_blessing(request: Request):
    """当前用户的问候语 + 每日祝福语（登录弹窗 / AI 助手都能用）。"""
    u = api_user(request)
    days = stats.checkin_days(u["id"])
    return json_ok(blessing.daily(u, stats.streak(u["id"]), len(days),
                                  str(date.today()) in set(days)))


@app.post("/api/onboard/done")
async def api_onboard_done(request: Request):
    """新手引导走完（或跳过）后调用：写入完成标记，之后不再弹出。"""
    u = get_user(request)
    if not u:
        return json_fail("请先登录", 401)
    db.finish_onboard(u["id"])
    return json_ok({"onboarded": 1}, "引导完成，去开工吧！")


# ==================== 好友 / 邀请 / 学习小队 ====================
@app.get("/friends", response_class=HTMLResponse)
async def friends_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    social.mark_read(u["id"])
    my_code = social.ensure_invite_code(u["id"])
    teams = social.teams_of(u["id"])
    for t in teams:
        t["member_list"] = social.team_members(t["id"])
        t["rate"] = social.team_checkin_rate(t["id"])
    return render(request, "friends.html", {
        "my_code": my_code,
        "friends": social.friends_of(u["id"]),
        "feed": social.feed(u["id"]),
        "board": social.week_board(u["id"]),
        "teams": teams,
        "notices": social.notices_of(u["id"]),
    })


@app.get("/team/{tid}", response_class=HTMLResponse)
async def team_page(request: Request, tid: int):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    t = social.team_by_id(tid)
    if not t:
        raise HTTPException(404, "小队不存在")
    members = social.team_members(tid)
    mine = any(m["id"] == u["id"] for m in members)
    owner = db.query_one("SELECT nickname FROM users WHERE id=?", (t["owner_id"],))
    member_ids = {m["id"] for m in members}
    invitable = [f for f in social.friends_of(u["id"]) if f["id"] not in member_ids]
    return render(request, "team.html", {
        "t": t, "members": members, "mine": mine,
        "rate": social.team_checkin_rate(tid),
        "owner_name": owner["nickname"] if owner else "—",
        "friend_ids": social.friend_ids(u["id"]),
        "invitable": invitable,
    })


class TeamBody(BaseModel):
    name: str = ""
    slogan: str = ""
    code: str = ""


@app.post("/api/invite/mine")
async def api_invite_mine(request: Request):
    u = api_user(request)
    return json_ok({"code": social.ensure_invite_code(u["id"])})


@app.post("/api/friend/add")
async def api_friend_add(request: Request, body: CodeBody):
    u = api_user(request)
    target = social.user_by_code(body.code)
    if not target:
        return json_fail("邀请码无效或不存在")
    if target["id"] == u["id"]:
        return json_fail("这是你自己的邀请码哦～")
    ok = social.add_friend(u["id"], target["id"])
    if not ok:
        return json_fail(f"你和 {target['nickname']} 已经是好友了")
    social.send_notice(target["id"], u["id"],
                       f"{u['nickname']} 添加了你为好友，一起刷题打卡吧！", "friend")
    return json_ok({"nickname": target["nickname"]},
                   f"已添加 {target['nickname']} 为好友")


@app.post("/api/friend/remove")
async def api_friend_remove(request: Request, body: CodeBody):
    u = api_user(request)
    social.remove_friend(u["id"], body.pid)
    return json_ok(msg="已解除好友关系")


@app.post("/api/nudge")
async def api_nudge(request: Request, body: CodeBody):
    """催好友打卡。"""
    u = api_user(request)
    f = db.query_one("SELECT id, nickname FROM users WHERE id=?", (body.pid,))
    if not f:
        return json_fail("用户不存在")
    if not social.is_friend(u["id"], f["id"]):
        return json_fail("对方不是你的好友")
    if social.checked_today(f["id"]):
        return json_fail(f"{f['nickname']} 今天已经打过卡啦")
    if social.nudge_count_today(u["id"]) >= 10:
        return json_fail("今天催得太多了，明天再来吧～")
    social.send_notice(f["id"], u["id"], f"{u['nickname']} 喊你今天记得打卡哦 🔥")
    return json_ok(msg=f"已提醒 {f['nickname']}")


@app.post("/api/notice/read")
async def api_notice_read(request: Request):
    u = api_user(request)
    social.mark_read(u["id"])
    return json_ok(msg="已全部标记为已读")


@app.post("/api/team/create")
async def api_team_create(request: Request, body: TeamBody):
    u = api_user(request)
    name = (body.name or "").strip()
    if len(name) < 2 or len(name) > 20:
        return json_fail("小队名称需为 2~20 个字符")
    t = social.create_team(u["id"], name, body.slogan)
    return json_ok({"id": t["id"], "code": t["code"], "name": t["name"]},
                   f"小队「{t['name']}」创建成功")


@app.post("/api/team/join")
async def api_team_join(request: Request, body: TeamBody):
    u = api_user(request)
    t = social.team_by_code(body.code)
    if not t:
        return json_fail("小队码无效或不存在")
    ok = social.join_team(u["id"], t["id"])
    if not ok:
        return json_fail(f"你已经在小队「{t['name']}」里了")
    owner = db.query_one("SELECT id, nickname FROM users WHERE id=?", (t["owner_id"],))
    if owner and owner["id"] != u["id"]:
        social.send_notice(owner["id"], u["id"],
                           f"{u['nickname']} 加入了你的小队「{t['name']}」", "team")
    return json_ok({"id": t["id"], "name": t["name"]}, f"已加入「{t['name']}」")


@app.post("/api/team/invite")
async def api_team_invite(request: Request, body: CodeBody):
    """邀请好友加入小队：body.pid 为小队 id，body.code 为好友 id（字符串）。"""
    u = api_user(request)
    t = social.team_by_id(body.pid)
    if not t:
        return json_fail("小队不存在")
    try:
        fid = int(body.code)
    except (TypeError, ValueError):
        return json_fail("参数错误")
    f = db.query_one("SELECT id, nickname FROM users WHERE id=?", (fid,))
    if not f:
        return json_fail("好友不存在")
    if not social.is_friend(u["id"], f["id"]):
        return json_fail("对方不是你的好友")
    if db.query_one("SELECT id FROM team_members WHERE team_id=? AND user_id=?", (t["id"], fid)):
        return json_fail(f"{f['nickname']} 已经在小队里了")
    social.send_notice(f["id"], u["id"],
                       f"{u['nickname']} 邀请你加入学习小队「{t['name']}」，"
                       f"小队码：{t['code']}", "team")
    return json_ok(msg=f"已向 {f['nickname']} 发出邀请")


@app.post("/api/team/leave")
async def api_team_leave(request: Request, body: CodeBody):
    u = api_user(request)
    t = social.team_by_id(body.pid)
    if not t:
        return json_fail("小队不存在")
    social.leave_team(u["id"], t["id"])
    return json_ok(msg=f"已退出「{t['name']}」")


# ==================== 限时测验 ====================
@app.get("/quiz", response_class=HTMLResponse)
async def quiz_home(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    history = db.query(
        "SELECT * FROM quizzes WHERE user_id=? AND mode='practice' "
        "ORDER BY id DESC LIMIT 10", (u["id"],))
    return render(request, "quiz_home.html", {"history": history})


class QuizStart(BaseModel):
    count: int = 10
    difficulty: str = ""
    category: str = ""
    minutes: int = 20


@app.post("/api/quiz/start")
async def quiz_start(request: Request, body: QuizStart):
    u = api_user(request)
    sql = "SELECT * FROM problems WHERE 1=1"
    args = []
    if body.difficulty:
        sql += " AND difficulty=?"
        args.append(body.difficulty)
    if body.category:
        sql += " AND category=?"
        args.append(body.category)
    pool = db.query(sql, args)
    if not pool:
        return json_fail("没有符合筛选条件的题目")
    n = max(1, min(int(body.count), len(pool), 30))
    picked = random.sample(pool, n)

    qid = db.execute(
        "INSERT INTO quizzes(user_id, title, mode, total, correct, duration, started_at) "
        "VALUES (?,?,?,?,0,?,?)",
        (u["id"], f"练习测验 · {n} 题", "practice", n, int(body.minutes), now_str()))
    for i, p in enumerate(picked):
        db.execute("INSERT INTO quiz_items(quiz_id, problem_id, sort) VALUES (?,?,?)",
                   (qid, p["id"], i))
    return json_ok({"quiz_id": qid}, "测验已生成")


@app.get("/quiz/{qid}", response_class=HTMLResponse)
async def quiz_page(request: Request, qid: int):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    q = db.query_one("SELECT * FROM quizzes WHERE id=? AND user_id=?", (qid, u["id"]))
    if not q:
        raise HTTPException(404, "测验不存在")
    if q["finished_at"]:
        return RedirectResponse(f"/quiz/{qid}/result", status_code=302)
    items = []
    for r in db.query(
            "SELECT qi.*, p.title, p.body, p.starter, p.difficulty, p.category, p.func "
            "FROM quiz_items qi JOIN problems p ON p.id=qi.problem_id "
            "WHERE qi.quiz_id=? ORDER BY qi.sort", (qid,)):
        r["diff_text"] = db.DIFF_LABEL.get(r["difficulty"], r["difficulty"])
        r["starter"] = r["starter"]
        items.append(r)
    return render(request, "quiz.html", {"q": q, "items": items})


@app.post("/api/quiz/{qid}/submit")
async def quiz_submit(request: Request, qid: int):
    u = api_user(request)
    q = db.query_one("SELECT * FROM quizzes WHERE id=? AND user_id=?", (qid, u["id"]))
    if not q:
        return json_fail("测验不存在")
    if q["finished_at"]:
        return json_fail("这份测验已经交卷了")

    try:
        payload = await request.json()
    except Exception:
        return json_fail("请求格式错误")
    codes = payload.get("codes") or {}
    seconds = int(payload.get("seconds") or 0)

    items = db.query(
        "SELECT qi.*, p.func, p.tests, p.starter FROM quiz_items qi "
        "JOIN problems p ON p.id=qi.problem_id WHERE qi.quiz_id=? ORDER BY qi.sort", (qid,))
    correct = 0
    for it in items:
        code = (codes.get(str(it["id"])) or "").strip() or it["starter"]
        tests = json.loads(it["tests"])
        res = judge.run_code(code, it["func"], tests)
        st = "accepted" if res["status"] == "accepted" else "wrong"
        if st == "accepted":
            correct += 1
        db.execute("UPDATE quiz_items SET code=?, status=? WHERE id=?", (code, st, it["id"]))

    total = len(items)
    passed_flag = 0
    cert_no = None

    if q["mode"] == "cert":
        cfg = db.CERTS.get(q["cert_key"])
        need = cfg["pass"] if cfg else int(total * 0.8)
        passed_flag = 1 if correct >= need else 0
        if passed_flag:
            cert_no = f"PY{datetime.now().strftime('%Y%m%d')}{secrets.token_hex(3).upper()}"
            db.execute(
                "INSERT INTO certs(user_id, cert_key, name, score, cert_no, issued_at) "
                "VALUES (?,?,?,?,?,?)",
                (u["id"], q["cert_key"], cfg["name"], correct, cert_no, now_str()))
            db.add_exp(u["id"], db.XP_QUIZ_PASS)
            db.add_energy(u["id"], db.ENERGY_QUIZ_PASS)
    else:
        passed_flag = 1 if (total and correct * 1.0 / total >= 0.6) else 0
        if passed_flag:
            db.add_exp(u["id"], db.XP_QUIZ_PASS)
            db.add_energy(u["id"], db.ENERGY_QUIZ_PASS)

    db.execute("UPDATE quizzes SET correct=?, duration=?, passed=?, finished_at=? WHERE id=?",
               (correct, seconds // 60, passed_flag, now_str(), qid))
    return json_ok({"quiz_id": qid, "correct": correct, "total": total,
                    "passed": passed_flag, "cert_no": cert_no},
                   "交卷成功")


@app.get("/quiz/{qid}/result", response_class=HTMLResponse)
async def quiz_result(request: Request, qid: int):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    q = db.query_one("SELECT * FROM quizzes WHERE id=? AND user_id=?", (qid, u["id"]))
    if not q:
        raise HTTPException(404, "测验不存在")
    items = db.query(
        "SELECT qi.*, p.title, p.difficulty, p.slug FROM quiz_items qi "
        "JOIN problems p ON p.id=qi.problem_id WHERE qi.quiz_id=? ORDER BY qi.sort", (qid,))
    for r in items:
        r["diff_text"] = db.DIFF_LABEL.get(r["difficulty"], r["difficulty"])
    cert = db.query_one("SELECT * FROM certs WHERE user_id=? AND cert_key=? AND cert_no LIKE ?",
                        (u["id"], q["cert_key"] or "", "%%"))
    return render(request, "quiz_result.html", {"q": q, "items": items,
                                                "score": round(q["correct"] * 100 / q["total"])
                                                if q["total"] else 0})


# ==================== 认证与证书 ====================
@app.get("/cert", response_class=HTMLResponse)
async def cert_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    lv = db.level_of(u["exp"])
    ac = stats.ac_count(u["id"])
    owned = {r["cert_key"]: r for r in db.query(
        "SELECT * FROM certs WHERE user_id=?", (u["id"],))}
    items = []
    for key, cfg in db.CERTS.items():
        items.append({
            "key": key, **cfg,
            "ok_level": lv["level"] >= cfg["level"],
            "ok_ac": ac >= cfg["ac"],
            "owned": owned.get(key),
            "ac_need": cfg["ac"],
            "ac_now": ac,
        })
    # 等级阶梯仅用于前端展示（称号走 db.LEVELS，条件/题数/及格线仍由 CERTS 决定）
    ladder = [{"level": lv_, "exp": base, "name": name} for lv_, base, name in db.LEVELS]
    return render(request, "cert.html",
                  {"items": items, "lv": lv, "ac": ac, "ladder": ladder})


@app.post("/api/cert/start")
async def cert_start(request: Request, body: CodeBody):
    """body.pid 复用为 0，用 body.code 传 cert_key。"""
    u = api_user(request)
    key = (body.code or "").strip()
    cfg = db.CERTS.get(key)
    if not cfg:
        return json_fail("认证类型不存在")
    lv = db.level_of(u["exp"])
    ac = stats.ac_count(u["id"])
    if lv["level"] < cfg["level"]:
        return json_fail(f"需要达到 Lv.{cfg['level']}，当前 Lv.{lv['level']}")
    if ac < cfg["ac"]:
        return json_fail(f"需要通过 {cfg['ac']} 道题，当前 {ac} 道")
    if db.query_one("SELECT id FROM certs WHERE user_id=? AND cert_key=?", (u["id"], key)):
        return json_fail("你已经获得该认证，无需重复考试")

    ph = ",".join("?" * len(cfg["diffs"]))
    pool = db.query(f"SELECT * FROM problems WHERE difficulty IN ({ph})", list(cfg["diffs"]))
    if len(pool) < cfg["count"]:
        return json_fail("题库数量不足，无法组卷")
    picked = random.sample(pool, cfg["count"])

    qid = db.execute(
        "INSERT INTO quizzes(user_id, title, mode, cert_key, total, correct, duration, started_at)"
        " VALUES (?,?,?,?,?,0,?,?)",
        (u["id"], f"{cfg['name']}考试", "cert", key, cfg["count"], 30, now_str()))
    for i, p in enumerate(picked):
        db.execute("INSERT INTO quiz_items(quiz_id, problem_id, sort) VALUES (?,?,?)",
                   (qid, p["id"], i))
    return json_ok({"quiz_id": qid}, "认证考试已开始")


@app.get("/certificate/{cert_no}", response_class=HTMLResponse)
async def certificate(request: Request, cert_no: str):
    row = db.query_one(
        "SELECT c.*, u.nickname, u.username FROM certs c JOIN users u ON u.id=c.user_id "
        "WHERE c.cert_no=?", (cert_no,))
    if not row:
        raise HTTPException(404, "证书不存在")
    return render(request, "certificate.html", {"c": row})


# ==================== 排行榜 ====================
@app.get("/rank", response_class=HTMLResponse)
async def rank_page(request: Request):
    rows = db.query("SELECT id, username, nickname, exp FROM users ORDER BY exp DESC LIMIT 50")
    for i, r in enumerate(rows):
        r["rank"] = i + 1
        r["lv"] = db.level_of(r["exp"])
        r["ac"] = stats.ac_count(r["id"])
        r["streak"] = stats.streak(r["id"])
    me = get_user(request)
    me_rank = 0
    if me:
        for i, r in enumerate(rows):
            if r["id"] == me["id"]:
                me_rank = i + 1
                break
    return render(request, "rank.html", {"rows": rows, "me_rank": me_rank})


# ==================== 个人中心 ====================
@app.get("/me", response_class=HTMLResponse)
async def me_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    return render(request, "me.html", {
        "s": stats.summary(u["id"]),
        "progress": stats.category_progress(u["id"]),
        "recent": stats.recent_activity(u["id"], 15),
        "certs": db.query("SELECT * FROM certs WHERE user_id=? ORDER BY id DESC", (u["id"],)),
        "quizzes": db.query("SELECT * FROM quizzes WHERE user_id=? ORDER BY id DESC LIMIT 10",
                            (u["id"],)),
    })


# ==================== 苗小序的菜园 ====================
@app.get("/farm", response_class=HTMLResponse)
async def farm_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    garden = farm.garden(u["id"])
    ready = sum(1 for p in garden if p["ready"])
    growing = sum(1 for p in garden if p["state"] == "growing")
    return render(request, "farm.html", {
        "garden": garden,
        "shop": farm.shop(u["id"]),
        "basket": farm.basket(u["id"]),
        "energy": db.energy_of(u["id"]),
        "unlocked": farm.slots_of(u["id"]),
        "total_slots": farm.TOTAL_SLOTS,
        "ready": ready,
        "growing": growing,
        "tips": farm_tip(ready, growing, db.energy_of(u["id"])),
        "rare": farm.rare_options(u["id"]),
        "ferts": [f for f in shop.ferts(u["id"]) if f["own"] > 0],
    })


def farm_tip(ready: int, growing: int, energy: int) -> str:
    if ready:
        return f"有 {ready} 块地熟啦！快收获，别让菜烂在地里～"
    if growing:
        return f"地里还有 {growing} 株在长。浇水能让它快 10 分钟哦 💧"
    if energy < 10:
        return "能量有点少，去打卡或做道题攒一攒，我这就扛着锄头下地 🌱"
    return "地都空着呢，先翻块地，再挑个种子种下去吧～"


@app.post("/api/farm/plow")
async def api_farm_plow(request: Request, body: CodeBody):
    u = api_user(request)
    r = farm.plow(u["id"], body.pid)
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


class PlantBody(BaseModel):
    """播种：pid=地块，crop=作物 key，seed=可选稀有种子 key。

    code 是旧版字段名，保留它是为了兼容早期调用（crop 为空时回退到 code）。
    """
    pid: int = 0
    crop: str = ""
    seed: str = ""
    code: str = ""


class ItemBody(BaseModel):
    """道具：key=道具 key，n=数量，pid=地块（施肥时用）。"""
    key: str = ""
    n: int = 1
    pid: int = 0


@app.post("/api/farm/plant")
async def api_farm_plant(request: Request, body: PlantBody):
    """body.pid = 地块编号，body.crop = 作物 key，body.seed = 稀有种子（可选）。"""
    u = api_user(request)
    crop = (body.crop or body.code or "").strip()
    r = farm.plant(u["id"], body.pid, crop, (body.seed or "").strip())
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


@app.post("/api/farm/fertilize")
async def api_farm_fertilize(request: Request, body: ItemBody):
    u = api_user(request)
    r = shop.use(u["id"], (body.key or "").strip(), body.pid)
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


@app.post("/api/farm/water")
async def api_farm_water(request: Request, body: CodeBody):
    u = api_user(request)
    r = farm.water(u["id"], body.pid)
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


@app.post("/api/farm/harvest")
async def api_farm_harvest(request: Request, body: CodeBody):
    u = api_user(request)
    r = farm.harvest(u["id"], body.pid)
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


@app.post("/api/farm/harvest-all")
async def api_farm_harvest_all(request: Request):
    u = api_user(request)
    r = farm.harvest_all(u["id"])
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


# ==================== 种子商店 ====================
@app.get("/shop", response_class=HTMLResponse)
async def shop_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    return render(request, "shop.html", {
        "items": shop.catalog(u["id"]),
        "seeds": shop.seeds(u["id"]),
        "ferts": shop.ferts(u["id"]),
        "inv": shop.inventory(u["id"]),
        "energy": db.energy_of(u["id"]),
        "garden": farm.garden(u["id"]),
        "unlocked": farm.slots_of(u["id"]),
        "growing_plots": [p for p in farm.garden(u["id"]) if p["state"] == "growing"],
    })


@app.post("/api/shop/buy")
async def api_shop_buy(request: Request, body: ItemBody):
    u = api_user(request)
    r = shop.buy(u["id"], (body.key or "").strip(), body.n)
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


@app.post("/api/shop/use")
async def api_shop_use(request: Request, body: ItemBody):
    """施肥：body.key 道具，body.pid 地块编号。"""
    u = api_user(request)
    r = shop.use(u["id"], (body.key or "").strip(), body.pid)
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


# ==================== 耕耘种菜大赛 ====================
@app.get("/contest", response_class=HTMLResponse)
async def contest_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    ov = contest.overview(u["id"])
    ov["energy"] = db.energy_of(u["id"])
    ov["inv"] = shop.inventory(u["id"])
    return render(request, "contest.html", ov)


@app.post("/api/contest/join")
async def api_contest_join(request: Request):
    u = api_user(request)
    r = contest.join(u["id"])
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


@app.post("/api/contest/claim")
async def api_contest_claim(request: Request):
    u = api_user(request)
    r = contest.claim(u["id"])
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


# ==================== 新手教程 ====================
@app.get("/guide", response_class=HTMLResponse)
async def guide_page(request: Request):
    return render(request, "guide.html", {"season": contest.current()})


# ==================== 分支一：耘野果蔬摊 ====================
@app.get("/market", response_class=HTMLResponse)
async def market_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    return render(request, "market.html", {
        "stock": market.stock(u["id"]),
        "prices": [dict(key=k, name=c["name"], emoji=c["emoji"], **market.price_of(k))
                   for k, c in farm.CROPS.items()],
        "sum": market.summary(u["id"]),
        "sales": market.recent_sales(u["id"]),
        "board": market.wealth_board(10),
        "rate": db.COIN_RATE,
        "energy": db.energy_of(u["id"]),
        "basket": farm.basket(u["id"]),
    })


class SellBody(BaseModel):
    crop: str = ""
    count: int = 1
    coins: int = 0


@app.post("/api/market/sell")
async def api_market_sell(request: Request, body: SellBody):
    u = api_user(request)
    r = market.sell(u["id"], (body.crop or "").strip(), body.count)
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


@app.post("/api/market/sell-all")
async def api_market_sell_all(request: Request):
    u = api_user(request)
    r = market.sell_all(u["id"])
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


@app.post("/api/market/exchange")
async def api_market_exchange(request: Request, body: SellBody):
    u = api_user(request)
    r = market.exchange(u["id"], body.coins)
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


# ==================== 分支二：厨房 ====================
@app.get("/kitchen", response_class=HTMLResponse)
async def kitchen_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    return render(request, "kitchen.html", {
        "recipes": kitchen.recipes(u["id"]),
        "dishes": kitchen.my_dishes(u["id"]),
        "stat": kitchen.stats(u["id"]),
        "pantry": kitchen.pantry(u["id"]),
        "basket": farm.basket(u["id"]),
        "energy": db.energy_of(u["id"]),
    })


class CookBody(BaseModel):
    dish: str = ""
    pid: int = 0
    title: str = ""
    note: str = ""


@app.post("/api/kitchen/cook")
async def api_kitchen_cook(request: Request, body: CookBody):
    u = api_user(request)
    r = kitchen.cook(u["id"], (body.dish or "").strip())
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


@app.post("/api/kitchen/publish")
async def api_kitchen_publish(request: Request, body: CookBody):
    u = api_user(request)
    r = kitchen.publish(u["id"], body.pid, body.title, body.note)
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


# ==================== 学习圈 ====================
@app.get("/circle", response_class=HTMLResponse)
async def circle_page(request: Request, category: str = "", q: str = ""):
    u = get_user(request)
    uid = u["id"] if u else 0
    return render(request, "circle.html", {
        "posts": circle.posts(category, q, 30, uid),
        "category": category, "q": q,
        "cats": circle.CATEGORIES,
        "stat": circle.stats(),
    })


@app.get("/post/{pid}", response_class=HTMLResponse)
async def post_page(request: Request, pid: int):
    u = get_user(request)
    uid = u["id"] if u else 0
    p = circle.post_detail(pid, uid)
    if not p:
        raise HTTPException(404, "帖子不存在")
    return render(request, "post.html", {"p": p})


class PostBody(BaseModel):
    title: str = ""
    content: str = ""
    category: str = ""
    message: str = ""
    pid: int = 0


@app.post("/api/circle/post")
async def api_circle_post(request: Request, body: PostBody):
    u = api_user(request)
    r = circle.create_post(u["id"], body.title, body.content, body.category)
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


@app.post("/api/circle/like")
async def api_circle_like(request: Request, body: PostBody):
    u = api_user(request)
    r = circle.toggle_like(body.pid, u["id"])
    return json_ok(r, "已点赞" if r.get("liked") else "已取消赞") if r["ok"] \
        else json_fail(r["msg"])


@app.post("/api/circle/comment")
async def api_circle_comment(request: Request, body: PostBody):
    u = api_user(request)
    r = circle.add_comment(body.pid, u["id"], body.message)
    return json_ok(r, r["msg"]) if r["ok"] else json_fail(r["msg"])


@app.post("/api/circle/delete")
async def api_circle_delete(request: Request, body: PostBody):
    u = api_user(request)
    if not circle.delete_post(body.pid, u["id"]):
        return json_fail("只能删除自己的帖子")
    return json_ok(msg="已删除")


# ==================== AI 助教 ====================
@app.get("/ai", response_class=HTMLResponse)
async def ai_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    return render(request, "ai.html", {"enabled": ai.is_enabled(),
                                       "has_key": bool(ai.get_api_key())})


class ChatBody(BaseModel):
    message: str = ""
    pid: int = 0
    code: str = ""
    action: str = "chat"   # chat | explain | analyze


@app.post("/api/ai/chat")
async def api_ai_chat(request: Request, body: ChatBody):
    api_user(request)
    if not ai.is_enabled():
        return json_fail("尚未配置 DeepSeek API Key，请到「设置」页面填写")
    if body.action == "explain":
        p = problem_by_id(body.pid)
        if not p:
            return json_fail("题目不存在")
        r = ai.explain_problem(p["title"], p["body"], p.get("hint", ""))
    elif body.action == "analyze":
        p = problem_by_id(body.pid)
        if not p:
            return json_fail("题目不存在")
        res = judge.run_code(body.code, p["func"], p["tests"])
        r = ai.analyze_error(p["title"], p["body"], body.code, res["results"], res["message"])
    else:
        if not body.message.strip():
            return json_fail("请输入你的问题")
        r = ai.free_chat(body.message.strip())
    if not r["ok"]:
        return json_fail(r["error"])
    return json_ok({"text": r["text"]})


# ==================== 设置 ====================
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    cfg = ai.load_config()
    return render(request, "settings.html", {"has_key": bool(ai.get_api_key()),
                                             "ai_enabled": cfg.get("ai_enabled", True)})


@app.post("/settings")
async def settings_save(request: Request, api_key: str = Form(""),
                        ai_enabled: str = Form("")):
    u = get_user(request)
    if not u:
        return RedirectResponse("/login", status_code=302)
    patch = {"ai_enabled": ai_enabled == "on"}
    if api_key.strip():
        patch["deepseek_api_key"] = api_key.strip()
    ai.save_config(patch)
    return render(request, "settings.html", {
        "has_key": bool(ai.get_api_key()),
        "ai_enabled": ai.load_config().get("ai_enabled", True),
        "saved": True,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
