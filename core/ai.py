"""AI 助教：对接 DeepSeek（OpenAI 兼容接口）。

配置方式（任选其一，优先级从高到低）：
  1. 项目根目录 config.json:  {"deepseek_api_key": "sk-xxxx", "ai_enabled": true}
  2. 环境变量 DEEPSEEK_API_KEY
  3. 网站「设置」页面里填写（会写入 config.json）

没配置 key 时，AI 相关功能会自动降级为不可用，其余功能不受影响。

另外，为了方便演示与离线体验，内置了一套「预设问答演示模式」：
没有配置 API Key 时，苗小序会用写好的答案库作答，不会联网、不调用任何接口；
一旦填入 Key，就自动切换回 DeepSeek 真实对话（原有问答逻辑完全不变）。
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config.json"

API_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"

MASCOT_NAME = "苗小序"

SYSTEM_PROMPT = (
    "你叫「苗小序」，是这个刷题网站的吉祥物 —— 一株活泼可爱的小绿苗，\n"
    "同时也是一位耐心细致的 Python 编程助教。你还有个搭档叫「禾籽」，\n"
    "是一颗爱讲冷知识的小种子，负责菜园、果蔬摊和厨房那边的科普。\n\n"
    "性格与说话方式：\n"
    "1. 用中文回答，亲切可爱，像学长学姐陪同学一起刷题。\n"
    "2. 喜欢拿农耕、植物生长打比方讲解编程，比如「基础打牢就像给小苗浇水」、\n"
    "   「调试代码就像给庄稼除虫，得有耐心」。\n"
    "3. 偶尔用 🌱🌾✨ 这类表情点缀，但不要每段都堆表情。\n"
    "4. 先鼓励一句，再讲重点，最后给一句「要不要试试这样改？」的引导。\n"
    "5. 学生卡住时不要嘲笑，要像浇水一样一点点引导他自己想明白。\n\n"
    "教学要求：\n"
    "1. 讲解要落到代码层面，必要时给出示例代码片段。\n"
    "2. 不要直接甩出一整份完整答案，要引导思考。\n"
    "3. 回答控制在 500 字以内，条理清晰。"
)


def load_config() -> Dict[str, Any]:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_config(cfg: Dict[str, Any]) -> None:
    old = load_config()
    old.update(cfg)
    CONFIG_FILE.write_text(json.dumps(old, ensure_ascii=False, indent=2), encoding="utf-8")


def get_api_key() -> str:
    cfg = load_config()
    key = cfg.get("deepseek_api_key") or os.environ.get("DEEPSEEK_API_KEY", "")
    return (key or "").strip()


def is_enabled() -> bool:
    """可用 = 配了 Key，或开启了预设问答演示模式。"""
    cfg = load_config()
    if cfg.get("ai_enabled") is False:
        return False
    if get_api_key():
        return True
    return demo_enabled()


def demo_enabled() -> bool:
    """预设问答演示模式默认开启；config.json 里写 ai_demo:false 可关闭。"""
    cfg = load_config()
    return cfg.get("ai_demo", True) is not False


def is_demo() -> bool:
    """当前是否处于演示模式（没配 Key 且不走真实接口）。"""
    return (not bool(get_api_key())) and demo_enabled()


def chat(messages: List[Dict[str, str]], max_tokens: int = 800,
         timeout: int = 60) -> Dict[str, Any]:
    """调用 DeepSeek，返回 {"ok": bool, "text": str, "error": str}"""
    key = get_api_key()
    if not key:
        if demo_enabled():
            return demo_reply(messages)      # 演示模式：本地预设答案，不发任何请求
        return {"ok": False, "text": "", "error": "尚未配置 DeepSeek API Key"}

    try:
        import requests
        resp = requests.post(
            API_URL,
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"},
            json={"model": MODEL, "messages": messages,
                  "max_tokens": max_tokens, "temperature": 0.7,
                  "stream": False},
            timeout=timeout,
        )
        if resp.status_code != 200:
            return {"ok": False, "text": "",
                    "error": f"接口返回 {resp.status_code}：{resp.text[:300]}"}
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
        return {"ok": True, "text": text, "error": ""}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "text": "", "error": f"请求失败：{e}"}


def explain_problem(title: str, body: str, hint: str = "") -> Dict[str, Any]:
    """让 AI 讲解一道题的解题思路（不直接给完整答案）。"""
    prompt = (
        f"题目：{title}\n\n题面：\n{body}\n\n"
        f"{('提示：' + hint) if hint else ''}\n\n"
        "请帮我：1) 用大白话讲清楚这道题要做什么；2) 给出解题思路和关键步骤；"
        "3) 指出新手容易踩的坑。不要直接给完整可提交的代码，用伪代码或片段引导。"
    )
    return chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])


def analyze_error(title: str, body: str, code: str,
                  results: List[Dict[str, Any]], message: str) -> Dict[str, Any]:
    """让 AI 分析用户代码为什么没通过。"""
    fails = [r for r in (results or []) if not r.get("ok")][:3]
    detail = "\n".join(
        f"- 输入 {r.get('args')}：期望 {r.get('expected')}，实际 {r.get('got')}"
        f"{('，报错：' + r['error']) if r.get('error') else ''}"
        for r in fails
    )
    prompt = (
        f"题目：{title}\n题面：{body}\n\n"
        f"我的代码：\n```python\n{code}\n```\n\n"
        f"运行结果：{message}\n"
        f"未通过的用例：\n{detail if detail else '（无）'}\n\n"
        "请指出：1) 错在哪里；2) 为什么会错；3) 给出修改建议（可以是关键代码片段）。"
    )
    return chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])


def free_chat(question: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
    msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in (history or [])[-8:]:
        role = h.get("role")
        content = (h.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            msgs.append({"role": role, "content": content[:2000]})
    msgs.append({"role": "user", "content": question})
    return chat(msgs)


# ==================== 预设问答演示模式 ====================
# 没配 Key 时使用：本地关键词匹配，零网络请求，方便演示与离线体验。
DEMO_FALLBACK = (
    "🌱 我是苗小序，现在跑在「预设问答演示模式」上 —— 不联网、不调用接口，"
    "用的都是我提前写好的答案。\n\n"
    "你可以试试问我这些：列表推导式、while 和 for、函数返回 None、字典遍历、递归、"
    "装饰器、生成器、异常处理、学习路线，还有菜园种菜、果蔬摊、厨房和大赛的玩法。\n\n"
    "想让我真正自由发挥的话，到「设置」页填上 DeepSeek API Key，我就能陪你聊代码啦～"
)

DEMO_QA = [
    {"kw": ["列表推导式", "列表生成"], "title": "列表推导式",
     "text": "把「造一个空列表 → for 循环 → append」三步压缩成一行：\n\n"
             "    squares = [x*x for x in range(10)]\n"
             "    evens = [x for x in nums if x % 2 == 0]\n\n"
             "结构是：[表达式 for 变量 in 可迭代对象 if 条件]，if 可省略。\n"
             "⚠️ 别为了炫技嵌套两层以上，那样可读性会断崖式下跌 —— 换成普通循环反而更好。\n"
             "要不要试试把你现在那段 for + append 改写成推导式？"},
    {"kw": ["while", "for 循环", "for循环"], "title": "while 还是 for",
     "text": "一句话口诀：**次数已知用 for，条件满足才停选 while**。\n\n"
             "    for i in range(5):        # 明确跑 5 次\n"
             "    while guess != answer:    # 不知道要跑几次\n\n"
             "while 最容易踩的坑是忘了更新条件，变成死循环 🌪️ —— "
             "写之前先问自己：循环体里哪个变量在变小/逼近终点？\n"
             "遍历列表、字符串、字典一律用 for，别用 while + 下标，那是 C 语言的习惯。"},
    {"kw": ["返回 none", "返回None", "none", "没有返回值"], "title": "函数为什么返回 None",
     "text": "Python 里**没写 return 的函数默认返回 None**，写了 return 但后面没值也一样。\n\n"
             "最常见的坑：想修改列表却写成了\n"
             "    def add_one(lst): lst = lst + [1]   # 重新绑定，外面没变\n"
             "正确做法是原地修改并返回：\n"
             "    def add_one(lst): lst.append(1); return lst\n\n"
             "还有一类：print(result) 有输出，但 return 没写，调用方拿到的就是 None。\n"
             "记住 print 是给人看的，return 才是给程序用的 🌱"},
    {"kw": ["字典", "dict", "键值对"], "title": "字典怎么用",
     "text": "字典就是「用名字查东西」，比列表按下标查更好读。\n\n"
             "    d.get(key, 默认值)      # 查不到不报错\n"
             "    for k, v in d.items():  # 遍历键值\n"
             "    d[key] = d.get(key, 0) + 1   # 计数套路\n\n"
             "⚠️ 遍历时不要增删键（RuntimeError），要改就先 list(d.keys()) 存一份。\n"
             "统计词频、分组归类，八成都能用这个「get 默认 0 再 +1」的套路解决。"},
    {"kw": ["集合", "set", "去重"], "title": "集合与去重",
     "text": "集合 set 的两大本事：**去重**和**快速判断在不在里面**（比列表快得多）。\n\n"
             "    uniq = list(set(nums))          # 去重（会打乱顺序）\n"
             "    uniq = sorted(set(nums))        # 去重 + 排序\n"
             "    if x in seen: ...               # O(1) 查找\n\n"
             "需要保持原顺序就别用 set，改用 dict.fromkeys(items) 或边遍历边判断 🌾"},
    {"kw": ["递归"], "title": "递归怎么写",
     "text": "递归就两件事：**基线条件**（什么时候停）+ **递归条件**（怎么变小）。\n\n"
             "    def fact(n):\n"
             "        if n <= 1: return 1          # 基线\n"
             "        return n * fact(n - 1)       # 规模变小\n\n"
             "⚠️ 忘了基线条件就是 RecursionError；Python 默认递归深度约 1000，"
             "数据大时改写成循环或用 lru_cache 缓存。\n"
             "先写出「n=1 时答案是什么」，递归就完成一半了 🌱"},
    {"kw": ["函数", "参数", "形参", "实参"], "title": "函数与参数",
     "text": "定义函数时最常见的三个小机关：\n"
             "1️⃣ 默认参数 `def f(a, b=2)` —— 默认值别用可变对象（[] 或 {}），会串味；\n"
             "2️⃣ 关键字调用 `f(a=1, b=3)` —— 不用记顺序；\n"
             "3️⃣ `return` 可以一次返回多个值，本质是元组打包。\n\n"
             "函数写短一点，一个函数只干一件事，调试时你会感谢自己 ✨"},
    {"kw": ["类", "面向对象", "class", "对象"], "title": "类与对象",
     "text": "类是图纸，对象是按图纸造出来的东西。\n\n"
             "    class Plot:\n"
             "        def __init__(self, crop): self.crop = crop\n"
             "        def water(self): self.grow += 10\n\n"
             "`__init__` 负责初始化，`self` 就是「这个对象自己」。\n"
             "菜园里的每一块地，其实就很适合写成一个 Plot 对象 🌱"},
    {"kw": ["异常", "try", "报错", "error", "调试"], "title": "异常处理与调试",
     "text": "报错不要慌，从下往上读最后一行，那里才是真正的病根。\n\n"
             "    try:\n"
             "        可能出错的代码\n"
             "    except ValueError as e:\n"
             "        print('出问题了：', e)\n\n"
             "调试三板斧：① 打印中间变量；② 缩小范围（先跑最小输入）；"
             "③ 对着报错行号往上追一层。\n"
             "调试就像给庄稼除虫，耐心一点总能找到 🐛"},
    {"kw": ["字符串", "切片", "split"], "title": "字符串与切片",
     "text": "字符串是不可变的，所有「修改」其实都是生成新串。\n\n"
             "    s[::-1]           # 反转\n"
             "    s[1:4]            # 左闭右开，取下标 1、2、3\n"
             "    s.split(',')      # 拆成列表\n"
             "    ','.join(list)    # 拼回字符串\n\n"
             "⚠️ 切片越界不报错，但下标访问越界会 IndexError。\n"
             "处理文本题，split + 循环 + join 基本能打八成的题 🌾"},
    {"kw": ["排序", "sort", "sorted"], "title": "排序",
     "text": "`list.sort()` 原地排序，`sorted(list)` 返回新列表（原列表不动）。\n\n"
             "    sorted(items, key=lambda x: x['score'], reverse=True)\n"
             "    sorted(words, key=len)        # 按长度\n\n"
             "想按多个条件排：key 返回一个元组 `(主键, 次键)`。\n"
             "自定义排序规则就交给 lambda 或 operator.itemgetter ✨"},
    {"kw": ["装饰器", "lambda", "生成器", "yield", "迭代器"],
     "title": "进阶小语法",
     "text": "这几个都是「写出来很酷，用对了才香」的家伙：\n"
             "🔸 lambda：一次性小函数，`sorted(key=lambda x: -x)`；\n"
             "🔸 生成器 yield：数据量大时省内存，一次产出一个；\n"
             "🔸 装饰器 @：给函数套一层壳，比如计时、登录校验。\n\n"
             "先读懂别人的代码，再自己写一个，别一上来就嵌套两层装饰器 🌱"},
    {"kw": ["文件", "读写", "open", "编码", "乱码"],
     "title": "文件读写",
     "text": "记住用 with，它会自动帮你关文件：\n\n"
             "    with open('a.txt', encoding='utf-8') as f:\n"
             "        text = f.read()\n\n"
             "⚠️ 中文乱码十有八九是没写 encoding='utf-8'。\n"
             "写文件用 'w'（覆盖）还是 'a'（追加）要看清楚，'w' 会清空原内容 ✨"},
    {"kw": ["学习路线", "怎么学", "入门", "新手"], "title": "Python 学习路线",
     "text": "一条能走通的路线（配着本站题库用更好）：\n"
             "1️⃣ 基础语法：变量、输入输出、分支循环 —— 对应「基础语法」分类；\n"
             "2️⃣ 字符串与列表：切片、遍历、常用方法；\n"
             "3️⃣ 字典与集合：计数、分组、查表；\n"
             "4️⃣ 函数与递归：把重复代码收进来；\n"
             "5️⃣ 算法进阶：排序、查找、简单 DP。\n\n"
             "每天打卡 + 2 道题，比周末突击 10 道有效得多 🌾"},
    {"kw": ["打卡", "能量", "积分"], "title": "打卡与能量",
     "text": "能量（⚡）就是本站的积分：\n"
             "✅ 每日打卡 +10、首次通过 +8、重复通过 +2、测验达标 +30、发帖 +5；\n"
             "💸 翻地 -5、浇水 -8、买种子按作物定价。\n\n"
             "收菜会返还更多能量，所以「打卡 → 种菜 → 收获」是个正向循环。\n"
             "攒多了还能去种子商店换稀有种子和肥料 🌱"},
    {"kw": ["菜园", "种菜", "播种", "收获", "浇水"], "title": "菜园怎么玩",
     "text": "菜园四步：⛏️ 翻地(-5) → 🌱 播种(按作物) → 💧 浇水(-8，每次顶 10 分钟) → 🧺 收获。\n\n"
             "收获之后有两条路：\n"
             "A 拿到「耘野果蔬摊」按行情卖成金币，还能看经管科普；\n"
             "B 进「厨房」做成菜，学食品科学并发到学习圈换能量。\n"
             "等级越高解锁的地越多，最多 6 块同时开工 🌾"},
    {"kw": ["果蔬摊", "金币", "卖菜", "行情"], "title": "果蔬摊与金币",
     "text": "菜篮里的收成可以按当日行情卖成金币 🪙，行情每天波动（0.8~1.3 倍）。\n"
             f"金币能在果蔬摊按 {2} 枚换 1 点能量的比例换回能量，摊位等级还会随累计收入提升。\n\n"
             "每卖出一单都会弹一张管理/金融小科普，比如机会成本、复利、库存周转 —— "
             "摆摊顺便学点经营的道理 📦"},
    {"kw": ["厨房", "做菜", "菜谱", "食品"], "title": "厨房与菜肴",
     "text": "厨房里可以用菜篮的食材做菜，做好会弹一张食品科学小科普 🍳\n"
             "（比如番茄红素是脂溶性的、豆浆会假沸、果胶加糖加酸才能凝成果酱）。\n\n"
             "做好的菜能发布到学习圈「🍽️ 田园食光」分区，换回几十到两百多点能量，"
             "是来能量最快的一条路 ✨"},
    {"kw": ["种菜大赛", "耕耘大赛", "大赛", "比赛", "榜单", "耕耘"], "title": "耕耘种菜大赛",
     "text": "大赛每周一季，每季绑定一个题库分类 + 一种主推作物 🌾\n\n"
             "积分 = 打卡天数 × 20 + 本周通过题目（主题分类额外加分）\n"
             "　　　+ 收获次数与收获能量（主推作物额外加分）\n"
             "　　　+ 菜园里作物的生长进度。\n\n"
             "赛季结束前都能报名，结算时按榜单发能量和稀有种子奖励。\n"
             "想冲榜就照着本季主题分类刷题，顺便多种主推作物 🏆"},
    {"kw": ["种子商店", "稀有种子", "肥料", "道具"], "title": "种子商店",
     "text": "种子商店用能量兑换两类道具：\n"
             "🌈 稀有种子：七彩番茄种（收获 ×2）、黄金稻种（生长 −40%）、沙瓤西瓜种（收获 +50%），播种时选用；\n"
             "💧 肥料：速长肥（+30 分钟）、壮苗肥（+80 分钟）、催熟肥（立刻成熟），在菜园地块上使用。\n\n"
             "大赛拿到的奖励也会进这里 🌱"},
    {"kw": ["你好", "是谁", "介绍", "嗨"], "title": "认识一下",
     "text": "嗨～我是苗小序 🌱 这个刷题网站的吉祥物，也是你的 Python 刷题搭子。\n"
             "我还有个搭档叫禾籽，是一颗爱讲冷知识的小种子，负责菜园、果蔬摊和厨房那边的科普。\n\n"
             "现在我在「预设问答演示模式」里，回答都是提前写好的；"
             "想让我自由发挥，去设置页填上 DeepSeek API Key 就好啦 ✨"},
]


def _demo_answer(question: str) -> str:
    """命中多条时取「关键词最长」的一条，避免「耕耘种菜大赛」被「种菜」抢先匹配。"""
    q = (question or "").lower()
    best, best_len = None, 0
    for item in DEMO_QA:
        for kw in item["kw"]:
            k = kw.lower()
            if k in q and len(k) > best_len:
                best, best_len = item, len(k)
    return best["text"] if best else DEMO_FALLBACK


def _demo_explain(prompt: str) -> str:
    title = ""
    for line in prompt.splitlines():
        if line.startswith("题目："):
            title = line[3:].strip()
            break
    return (f"🌱 来，我陪你拆《{title}》这道题（演示模式答案）：\n\n"
            "1️⃣ 先翻译成人话：题目给了什么输入，想要什么输出？把这句话写下来。\n"
            "2️⃣ 想最笨的办法：能不能用循环一个个处理？先让它跑通，再谈优化。\n"
            "3️⃣ 找边界：空输入、只有一个元素、极值，这三类最容易漏。\n"
            "4️⃣ 写一个 3 行的伪代码骨架：\n"
            "        result = 初值\n"
            "        for 每个输入: result = 更新(result)\n"
            "        return result\n\n"
            "卡住的话告诉我你卡在第几步，我陪你往下想 🌾")


def _demo_debug(prompt: str) -> str:
    title = ""
    for line in prompt.splitlines():
        if line.startswith("题目："):
            title = line[3:].strip()
            break
    return (f"🌱 关于《{title}》这份代码（演示模式答案），按这个顺序排查：\n\n"
            "1️⃣ 看报错最后一行：类型错误查变量类型，索引错误查循环边界。\n"
            "2️⃣ 打印中间值：在关键步骤 print 一下，确认它是不是你以为的样子。\n"
            "3️⃣ 检查返回值：函数有没有 return？是不是用了 print 代替 return？\n"
            "4️⃣ 对拍用例：拿最小输入手动算一遍，再和程序输出比。\n"
            "5️⃣ 边界：空列表、0、负数，这类输入最常翻车。\n\n"
            "调试就像给庄稼除虫，耐心一点总能找到 🐛 要不要先把报错信息发给我看看？")


def demo_reply(messages: List[Dict[str, str]]) -> Dict[str, Any]:
    """演示模式：本地预设答案，不发起任何网络请求。"""
    text = ""
    for m in reversed(messages or []):
        if m.get("role") == "user":
            text = (m.get("content") or "").strip()
            break
    if not text:
        return {"ok": True, "text": DEMO_FALLBACK}
    if "请帮我：1) 用大白话讲清楚" in text:
        return {"ok": True, "text": _demo_explain(text)}
    if "请指出：1) 错在哪里" in text:
        return {"ok": True, "text": _demo_debug(text)}
    return {"ok": True, "text": _demo_answer(text)}
