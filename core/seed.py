"""题库种子数据：33 道 Python 练习题。

每道题结构：
  slug       唯一标识
  title      标题
  body       题面（支持换行）
  difficulty easy / medium / hard
  category   分类
  func       需要实现的函数名
  starter    初始代码
  tests      测试用例 [{"args":[...], "expected": ...}]
  hint       提示
  solution   参考答案
"""
from typing import List, Dict, Any

PROBLEMS: List[Dict[str, Any]] = [
    # ================= 基础语法 =================
    {
        "slug": "add-two",
        "title": "两数之和",
        "category": "基础语法", "difficulty": "easy", "func": "add",
        "body": "实现函数 add(a, b)，返回 a 与 b 的和。\n\n示例：add(1, 2) -> 3",
        "starter": "def add(a, b):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [1, 2], "expected": 3},
            {"args": [-5, 5], "expected": 0},
            {"args": [100, 250], "expected": 350},
            {"args": [0, 0], "expected": 0},
        ],
        "hint": "用 return 把结果返回出去，不要 print。",
        "solution": "def add(a, b):\n    return a + b\n",
    },
    {
        "slug": "is-even",
        "title": "判断奇偶",
        "category": "基础语法", "difficulty": "easy", "func": "is_even",
        "body": "实现函数 is_even(n)，当 n 是偶数时返回 True，否则返回 False。\n\n示例：is_even(4) -> True",
        "starter": "def is_even(n):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [4], "expected": True},
            {"args": [7], "expected": False},
            {"args": [0], "expected": True},
            {"args": [-3], "expected": False},
        ],
        "hint": "用取模运算符 % 判断余数是否为 0。",
        "solution": "def is_even(n):\n    return n % 2 == 0\n",
    },
    {
        "slug": "celsius",
        "title": "摄氏温度转华氏",
        "category": "基础语法", "difficulty": "easy", "func": "to_fahrenheit",
        "body": "实现函数 to_fahrenheit(c)，把摄氏温度转为华氏温度。\n公式：F = C × 9 / 5 + 32\n结果保留 1 位小数。\n\n示例：to_fahrenheit(100) -> 212.0",
        "starter": "def to_fahrenheit(c):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [100], "expected": 212.0},
            {"args": [0], "expected": 32.0},
            {"args": [37], "expected": 98.6},
            {"args": [-40], "expected": -40.0},
        ],
        "hint": "用 round(x, 1) 保留一位小数。",
        "solution": "def to_fahrenheit(c):\n    return round(c * 9 / 5 + 32, 1)\n",
    },
    {
        "slug": "my-abs",
        "title": "自定义绝对值",
        "category": "基础语法", "difficulty": "easy", "func": "my_abs",
        "body": "不使用内置 abs()，实现函数 my_abs(x) 返回 x 的绝对值。\n\n示例：my_abs(-8) -> 8",
        "starter": "def my_abs(x):\n    # 不允许使用 abs()\n    pass\n",
        "tests": [
            {"args": [-8], "expected": 8},
            {"args": [8], "expected": 8},
            {"args": [0], "expected": 0},
            {"args": [-3.5], "expected": 3.5},
        ],
        "hint": "负数返回它的相反数，非负数原样返回。",
        "solution": "def my_abs(x):\n    return -x if x < 0 else x\n",
    },
    {
        "slug": "score-grade",
        "title": "成绩等级判定",
        "category": "基础语法", "difficulty": "easy", "func": "grade",
        "body": "实现函数 grade(score)，根据分数返回等级字符串：\n  90 分及以上 -> 'A'\n  80~89      -> 'B'\n  70~79      -> 'C'\n  60~69      -> 'D'\n  60 分以下   -> 'F'\n\n示例：grade(85) -> 'B'",
        "starter": "def grade(score):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [95], "expected": "A"},
            {"args": [85], "expected": "B"},
            {"args": [73], "expected": "C"},
            {"args": [60], "expected": "D"},
            {"args": [45], "expected": "F"},
        ],
        "hint": "用 if / elif / else 从上往下判断，注意边界。",
        "solution": "def grade(score):\n    if score >= 90:\n        return 'A'\n    elif score >= 80:\n        return 'B'\n    elif score >= 70:\n        return 'C'\n    elif score >= 60:\n        return 'D'\n    return 'F'\n",
    },
    {
        "slug": "sum-to-n",
        "title": "1 到 n 的累加和",
        "category": "基础语法", "difficulty": "easy", "func": "sum_to",
        "body": "实现函数 sum_to(n)，返回 1 + 2 + ... + n 的结果。\n不能使用 sum() 和循环公式以外的方式？——允许任意写法。\n\n示例：sum_to(5) -> 15",
        "starter": "def sum_to(n):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [5], "expected": 15},
            {"args": [1], "expected": 1},
            {"args": [100], "expected": 5050},
            {"args": [0], "expected": 0},
        ],
        "hint": "用 for 循环累加，或者直接用等差数列公式 n*(n+1)//2。",
        "solution": "def sum_to(n):\n    return n * (n + 1) // 2\n",
    },

    # ================= 字符串 =================
    {
        "slug": "reverse-string",
        "title": "字符串反转",
        "category": "字符串", "difficulty": "easy", "func": "reverse_string",
        "body": "实现函数 reverse_string(s)，返回 s 反转后的字符串。\n\n示例：reverse_string('hello') -> 'olleh'",
        "starter": "def reverse_string(s):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": ["hello"], "expected": "olleh"},
            {"args": ["Python"], "expected": "nohtyP"},
            {"args": [""], "expected": ""},
            {"args": ["a"], "expected": "a"},
        ],
        "hint": "切片 s[::-1] 一步搞定。",
        "solution": "def reverse_string(s):\n    return s[::-1]\n",
    },
    {
        "slug": "is-palindrome",
        "title": "回文字符串判断",
        "category": "字符串", "difficulty": "easy", "func": "is_palindrome",
        "body": "实现函数 is_palindrome(s)，判断 s 是否为回文（正着读和反着读一样）。\n忽略大小写差异，只考虑字母数字组成的简单字符串。\n\n示例：is_palindrome('level') -> True",
        "starter": "def is_palindrome(s):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": ["level"], "expected": True},
            {"args": ["python"], "expected": False},
            {"args": ["aba"], "expected": True},
            {"args": ["AbBa"], "expected": True},
        ],
        "hint": "先把 s 转成小写，再和它的反转比较。",
        "solution": "def is_palindrome(s):\n    s = s.lower()\n    return s == s[::-1]\n",
    },
    {
        "slug": "count-char",
        "title": "统计字符出现次数",
        "category": "字符串", "difficulty": "easy", "func": "count_char",
        "body": "实现函数 count_char(s, ch)，返回字符 ch 在字符串 s 中出现的次数。\n不能使用 s.count() 方法，请自己遍历。\n\n示例：count_char('banana', 'a') -> 3",
        "starter": "def count_char(s, ch):\n    # 不能使用 s.count()\n    pass\n",
        "tests": [
            {"args": ["banana", "a"], "expected": 3},
            {"args": ["hello", "l"], "expected": 2},
            {"args": ["python", "z"], "expected": 0},
            {"args": ["", "a"], "expected": 0},
        ],
        "hint": "用 for 循环遍历每个字符，相等就计数加一。",
        "solution": "def count_char(s, ch):\n    n = 0\n    for c in s:\n        if c == ch:\n            n += 1\n    return n\n",
    },
    {
        "slug": "count-words",
        "title": "统计单词数量",
        "category": "字符串", "difficulty": "medium", "func": "count_words",
        "body": "实现函数 count_words(s)，返回字符串 s 中单词的个数。\n单词以空白字符分隔，需正确处理多个连续空格与首尾空格。\n\n示例：count_words('  hello   world  ') -> 2",
        "starter": "def count_words(s):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": ["hello world"], "expected": 2},
            {"args": ["  hello   world  "], "expected": 2},
            {"args": [""], "expected": 0},
            {"args": ["   "], "expected": 0},
            {"args": ["one"], "expected": 1},
        ],
        "hint": "s.split() 不带参数时会自动处理多余空格。",
        "solution": "def count_words(s):\n    return len(s.split())\n",
    },
    {
        "slug": "title-case",
        "title": "每个单词首字母大写",
        "category": "字符串", "difficulty": "medium", "func": "title_words",
        "body": "实现函数 title_words(s)，把字符串中每个单词的首字母变为大写，其余字母变为小写，再用单个空格连接。\n\n示例：title_words('hELLO wORLD') -> 'Hello World'",
        "starter": "def title_words(s):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": ["hELLO wORLD"], "expected": "Hello World"},
            {"args": ["python is fun"], "expected": "Python Is Fun"},
            {"args": ["a"], "expected": "A"},
            {"args": ["  two   words "], "expected": "Two Words"},
        ],
        "hint": "先 split()，对每个词做 word[0].upper() + word[1:].lower()，再 join。",
        "solution": "def title_words(s):\n    return ' '.join(w[0].upper() + w[1:].lower() for w in s.split())\n",
    },

    # ================= 列表 =================
    {
        "slug": "my-max",
        "title": "找出列表最大值",
        "category": "列表", "difficulty": "easy", "func": "my_max",
        "body": "不使用内置 max()，实现函数 my_max(lst) 返回列表中的最大值。\n假设列表非空。\n\n示例：my_max([3, 9, 2]) -> 9",
        "starter": "def my_max(lst):\n    # 不能使用 max()\n    pass\n",
        "tests": [
            {"args": [[3, 9, 2]], "expected": 9},
            {"args": [[-1, -5, -2]], "expected": -1},
            {"args": [[7]], "expected": 7},
            {"args": [[1, 3, 3, 2]], "expected": 3},
        ],
        "hint": "先假设第一个元素最大，再逐个比较更新。",
        "solution": "def my_max(lst):\n    m = lst[0]\n    for x in lst[1:]:\n        if x > m:\n            m = x\n    return m\n",
    },
    {
        "slug": "sum-list",
        "title": "列表求和",
        "category": "列表", "difficulty": "easy", "func": "sum_list",
        "body": "实现函数 sum_list(lst)，返回列表中所有数字的和。\n不能使用内置 sum()。\n\n示例：sum_list([1, 2, 3]) -> 6",
        "starter": "def sum_list(lst):\n    # 不能使用 sum()\n    pass\n",
        "tests": [
            {"args": [[1, 2, 3]], "expected": 6},
            {"args": [[]], "expected": 0},
            {"args": [[-1, 1]], "expected": 0},
            {"args": [[2, 4, 6, 8]], "expected": 20},
        ],
        "hint": "用一个变量累加，遍历列表每项加进去。",
        "solution": "def sum_list(lst):\n    total = 0\n    for x in lst:\n        total += x\n    return total\n",
    },
    {
        "slug": "dedup",
        "title": "列表去重（保持顺序）",
        "category": "列表", "difficulty": "medium", "func": "dedup",
        "body": "实现函数 dedup(lst)，去除列表中的重复元素，并保持原有顺序。\n\n示例：dedup([3, 1, 3, 2, 1]) -> [3, 1, 2]",
        "starter": "def dedup(lst):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [[3, 1, 3, 2, 1]], "expected": [3, 1, 2]},
            {"args": [[1, 2, 3]], "expected": [1, 2, 3]},
            {"args": [[]], "expected": []},
            {"args": [["a", "b", "a"]], "expected": ["a", "b"]},
        ],
        "hint": "遍历时用一个集合记录已见过的元素（集合在沙箱中可用）。",
        "solution": "def dedup(lst):\n    seen = set()\n    out = []\n    for x in lst:\n        if x not in seen:\n            seen.add(x)\n            out.append(x)\n    return out\n",
    },
    {
        "slug": "binary-search",
        "title": "二分查找",
        "category": "列表", "difficulty": "medium", "func": "binary_search",
        "body": "实现函数 binary_search(lst, target)，在**已升序排列**的列表 lst 中查找 target。\n找到则返回其下标，找不到返回 -1。\n\n示例：binary_search([1, 3, 5, 7], 5) -> 2",
        "starter": "def binary_search(lst, target):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [[1, 3, 5, 7], 5], "expected": 2},
            {"args": [[1, 3, 5, 7], 1], "expected": 0},
            {"args": [[1, 3, 5, 7], 7], "expected": 3},
            {"args": [[1, 3, 5, 7], 4], "expected": -1},
            {"args": [[], 1], "expected": -1},
        ],
        "hint": "维护左右指针 left/right，每次取中点比较后缩小区间。",
        "solution": "def binary_search(lst, target):\n    left, right = 0, len(lst) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if lst[mid] == target:\n            return mid\n        elif lst[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n",
    },
    {
        "slug": "bubble-sort",
        "title": "冒泡排序",
        "category": "列表", "difficulty": "medium", "func": "bubble_sort",
        "body": "实现函数 bubble_sort(lst)，用冒泡排序把列表升序排列并返回新列表。\n不要修改原列表。不能使用 sorted()。\n\n示例：bubble_sort([3, 1, 4, 2]) -> [1, 2, 3, 4]",
        "starter": "def bubble_sort(lst):\n    # 不能使用 sorted()\n    pass\n",
        "tests": [
            {"args": [[3, 1, 4, 2]], "expected": [1, 2, 3, 4]},
            {"args": [[5, 5, 1]], "expected": [1, 5, 5]},
            {"args": [[]], "expected": []},
            {"args": [[9, 8, 7, 6, 5]], "expected": [5, 6, 7, 8, 9]},
        ],
        "hint": "先复制一份 arr = lst[:]，再两层循环相邻比较交换。",
        "solution": "def bubble_sort(lst):\n    arr = lst[:]\n    n = len(arr)\n    for i in range(n):\n        for j in range(0, n - i - 1):\n            if arr[j] > arr[j + 1]:\n                arr[j], arr[j + 1] = arr[j + 1], arr[j]\n    return arr\n",
    },

    # ================= 字典与集合 =================
    {
        "slug": "word-freq",
        "title": "统计词频",
        "category": "字典与集合", "difficulty": "medium", "func": "word_freq",
        "body": "实现函数 word_freq(words)，统计列表中每个单词出现的次数，返回字典。\n\n示例：word_freq(['a', 'b', 'a']) -> {'a': 2, 'b': 1}",
        "starter": "def word_freq(words):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [["a", "b", "a"]], "expected": {"a": 2, "b": 1}},
            {"args": [[]], "expected": {}},
            {"args": [["x", "x", "x"]], "expected": {"x": 3}},
            {"args": [["one", "two"]], "expected": {"one": 1, "two": 1}},
        ],
        "hint": "用 d.get(w, 0) + 1 累加计数。",
        "solution": "def word_freq(words):\n    d = {}\n    for w in words:\n        d[w] = d.get(w, 0) + 1\n    return d\n",
    },
    {
        "slug": "merge-dict",
        "title": "合并两个字典",
        "category": "字典与集合", "difficulty": "easy", "func": "merge_dict",
        "body": "实现函数 merge_dict(d1, d2)，合并两个字典；若键重复，以 d2 的值为准。\n\n示例：merge_dict({'a': 1}, {'b': 2, 'a': 9}) -> {'a': 9, 'b': 2}",
        "starter": "def merge_dict(d1, d2):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [{"a": 1}, {"b": 2, "a": 9}], "expected": {"a": 9, "b": 2}},
            {"args": [{}, {"k": 1}], "expected": {"k": 1}},
            {"args": [{"x": 1}, {}], "expected": {"x": 1}},
        ],
        "hint": "先复制 d1，再用 d2 更新。",
        "solution": "def merge_dict(d1, d2):\n    out = d1.copy()\n    out.update(d2)\n    return out\n",
    },
    {
        "slug": "intersection",
        "title": "两个列表的交集",
        "category": "字典与集合", "difficulty": "easy", "func": "intersection",
        "body": "实现函数 intersection(a, b)，返回同时存在于两个列表中的元素，结果升序排列。\n\n示例：intersection([1, 2, 3], [2, 3, 4]) -> [2, 3]",
        "starter": "def intersection(a, b):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [[1, 2, 3], [2, 3, 4]], "expected": [2, 3]},
            {"args": [[1, 2], [3, 4]], "expected": []},
            {"args": [[3, 1, 2], [2, 1]], "expected": [1, 2]},
            {"args": [[], [1]], "expected": []},
        ],
        "hint": "转成集合求交集，再排序返回列表。",
        "solution": "def intersection(a, b):\n    return sorted(set(a) & set(b))\n",
    },
    {
        "slug": "sort-by-value",
        "title": "字典按值排序",
        "category": "字典与集合", "difficulty": "medium", "func": "sort_by_value",
        "body": "实现函数 sort_by_value(d)，把字典按值从大到小排序，返回键组成的列表。\n值相同时按键的字母/数字顺序升序排列。\n\n示例：sort_by_value({'a': 3, 'b': 1, 'c': 2}) -> ['a', 'c', 'b']",
        "starter": "def sort_by_value(d):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [{"a": 3, "b": 1, "c": 2}], "expected": ["a", "c", "b"]},
            {"args": [{}], "expected": []},
            {"args": [{"x": 5, "y": 5, "z": 1}], "expected": ["x", "y", "z"]},
        ],
        "hint": "sorted(d, key=lambda k: (-d[k], k))",
        "solution": "def sort_by_value(d):\n    return sorted(d, key=lambda k: (-d[k], k))\n",
    },

    # ================= 函数与递归 =================
    {
        "slug": "factorial",
        "title": "阶乘（递归）",
        "category": "函数与递归", "difficulty": "easy", "func": "factorial",
        "body": "实现函数 factorial(n)，返回 n 的阶乘。要求使用递归实现。\n约定 factorial(0) = 1。\n\n示例：factorial(5) -> 120",
        "starter": "def factorial(n):\n    # 请用递归实现\n    pass\n",
        "tests": [
            {"args": [5], "expected": 120},
            {"args": [0], "expected": 1},
            {"args": [1], "expected": 1},
            {"args": [6], "expected": 720},
        ],
        "hint": "递归出口是 n <= 1 返回 1，否则返回 n * factorial(n-1)。",
        "solution": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n",
    },
    {
        "slug": "fib",
        "title": "斐波那契数列",
        "category": "函数与递归", "difficulty": "medium", "func": "fib",
        "body": "实现函数 fib(n)，返回斐波那契数列的第 n 项。\n约定 fib(0) = 0，fib(1) = 1。\n\n示例：fib(6) -> 8\n（数列：0, 1, 1, 2, 3, 5, 8 ...）",
        "starter": "def fib(n):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [6], "expected": 8},
            {"args": [0], "expected": 0},
            {"args": [1], "expected": 1},
            {"args": [10], "expected": 55},
        ],
        "hint": "用循环迭代实现效率更高：a, b = b, a + b。",
        "solution": "def fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a\n",
    },
    {
        "slug": "gcd",
        "title": "最大公约数",
        "category": "函数与递归", "difficulty": "medium", "func": "gcd",
        "body": "实现函数 gcd(a, b)，用辗转相除法求两个正整数的最大公约数。\n\n示例：gcd(12, 18) -> 6",
        "starter": "def gcd(a, b):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [12, 18], "expected": 6},
            {"args": [7, 13], "expected": 1},
            {"args": [100, 10], "expected": 10},
            {"args": [17, 17], "expected": 17},
        ],
        "hint": "while b: a, b = b, a % b，最后返回 a。",
        "solution": "def gcd(a, b):\n    while b:\n        a, b = b, a % b\n    return a\n",
    },
    {
        "slug": "is-prime",
        "title": "素数判断",
        "category": "函数与递归", "difficulty": "medium", "func": "is_prime",
        "body": "实现函数 is_prime(n)，判断 n 是否为素数（质数），返回 True / False。\n注意：小于 2 的数都不是素数。\n\n示例：is_prime(7) -> True",
        "starter": "def is_prime(n):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [7], "expected": True},
            {"args": [1], "expected": False},
            {"args": [2], "expected": True},
            {"args": [9], "expected": False},
            {"args": [97], "expected": True},
        ],
        "hint": "只需检查到 n 的平方根即可，用 range(2, int(n ** 0.5) + 1)。",
        "solution": "def is_prime(n):\n    if n < 2:\n        return False\n    i = 2\n    while i * i <= n:\n        if n % i == 0:\n            return False\n        i += 1\n    return True\n",
    },

    # ================= 算法进阶 =================
    {
        "slug": "fizzbuzz",
        "title": "FizzBuzz 序列",
        "category": "算法进阶", "difficulty": "easy", "func": "fizzbuzz",
        "body": "实现函数 fizzbuzz(n)，返回长度 n 的列表：\n  下标对应的数能被 3 整除 -> 'Fizz'\n  能被 5 整除 -> 'Buzz'\n  同时能被 15 整除 -> 'FizzBuzz'\n  否则 -> 该数字的字符串形式\n第 i 项（从 1 开始计）对应数字 i。\n\n示例：fizzbuzz(5) -> ['1', '2', 'Fizz', '4', 'Buzz']",
        "starter": "def fizzbuzz(n):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [5], "expected": ["1", "2", "Fizz", "4", "Buzz"]},
            {"args": [15], "expected": ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8",
                                        "Fizz", "Buzz", "11", "Fizz", "13", "14", "FizzBuzz"]},
            {"args": [1], "expected": ["1"]},
        ],
        "hint": "先判断能否被 15 整除，再判断 3 和 5。",
        "solution": "def fizzbuzz(n):\n    out = []\n    for i in range(1, n + 1):\n        if i % 15 == 0:\n            out.append('FizzBuzz')\n        elif i % 3 == 0:\n            out.append('Fizz')\n        elif i % 5 == 0:\n            out.append('Buzz')\n        else:\n            out.append(str(i))\n    return out\n",
    },
    {
        "slug": "flatten",
        "title": "嵌套列表扁平化",
        "category": "算法进阶", "difficulty": "medium", "func": "flatten",
        "body": "实现函数 flatten(nested)，把任意深度嵌套的列表展开成一维列表，保持元素顺序。\n\n示例：flatten([1, [2, [3, 4]], 5]) -> [1, 2, 3, 4, 5]",
        "starter": "def flatten(nested):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [[1, [2, [3, 4]], 5]], "expected": [1, 2, 3, 4, 5]},
            {"args": [[]], "expected": []},
            {"args": [[1, 2, 3]], "expected": [1, 2, 3]},
            {"args": [[[1]], [[2]], 3], "expected": [1, 2, 3]},
        ],
        "hint": "递归：遇到 list 就继续展开，否则加入结果。",
        "solution": "def flatten(nested):\n    out = []\n    for x in nested:\n        if isinstance(x, list):\n            out.extend(flatten(x))\n        else:\n            out.append(x)\n    return out\n",
    },
    {
        "slug": "two-sum",
        "title": "两数之和（下标）",
        "category": "算法进阶", "difficulty": "medium", "func": "two_sum",
        "body": "实现函数 two_sum(nums, target)，在列表中找到两个数使它们的和等于 target，\n返回这两个数的下标（升序排列）。假设有且仅有一组解，不能重复使用同一元素。\n\n示例：two_sum([2, 7, 11, 15], 9) -> [0, 1]",
        "starter": "def two_sum(nums, target):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [[2, 7, 11, 15], 9], "expected": [0, 1]},
            {"args": [[3, 2, 4], 6], "expected": [1, 2]},
            {"args": [[3, 3], 6], "expected": [0, 1]},
            {"args": [[1, 5, 3], 4], "expected": [0, 2]},
        ],
        "hint": "用字典记录「值 -> 下标」，遍历时查找 target - 当前值是否出现过。",
        "solution": "def two_sum(nums, target):\n    seen = {}\n    for i, v in enumerate(nums):\n        if target - v in seen:\n            return [seen[target - v], i]\n        seen[v] = i\n    return []\n",
    },
    {
        "slug": "valid-brackets",
        "title": "有效的括号",
        "category": "算法进阶", "difficulty": "medium", "func": "valid_brackets",
        "body": "实现函数 valid_brackets(s)，判断字符串中的括号是否合法匹配。\n只考虑 () [] {} 三种括号，其它字符忽略。\n\n示例：valid_brackets('({[]})') -> True\n     valid_brackets('([)]')   -> False",
        "starter": "def valid_brackets(s):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": ["({[]})"], "expected": True},
            {"args": ["([)]"], "expected": False},
            {"args": ["()"], "expected": True},
            {"args": ["("], "expected": False},
            {"args": [""], "expected": True},
            {"args": ["{[]}"], "expected": True},
        ],
        "hint": "用栈：遇到左括号入栈，遇到右括号就与栈顶比对。",
        "solution": "def valid_brackets(s):\n    pairs = {')': '(', ']': '[', '}': '{'}\n    stack = []\n    for c in s:\n        if c in '([{':\n            stack.append(c)\n        elif c in pairs:\n            if not stack or stack[-1] != pairs[c]:\n                return False\n            stack.pop()\n    return not stack\n",
    },
    {
        "slug": "climb-stairs",
        "title": "爬楼梯",
        "category": "算法进阶", "difficulty": "medium", "func": "climb_stairs",
        "body": "实现函数 climb_stairs(n)：一共有 n 级台阶，每次可以走 1 级或 2 级，\n返回共有多少种不同的走法。\n\n示例：climb_stairs(3) -> 3 （1+1+1 / 1+2 / 2+1）",
        "starter": "def climb_stairs(n):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [3], "expected": 3},
            {"args": [1], "expected": 1},
            {"args": [2], "expected": 2},
            {"args": [5], "expected": 8},
            {"args": [10], "expected": 89},
        ],
        "hint": "这是斐波那契的变形：dp[n] = dp[n-1] + dp[n-2]。",
        "solution": "def climb_stairs(n):\n    if n <= 2:\n        return n\n    a, b = 1, 2\n    for _ in range(3, n + 1):\n        a, b = b, a + b\n    return b\n",
    },
    {
        "slug": "longest-common-prefix",
        "title": "最长公共前缀",
        "category": "算法进阶", "difficulty": "medium", "func": "longest_common_prefix",
        "body": "实现函数 longest_common_prefix(strs)，返回字符串列表中所有字符串的最长公共前缀。\n若不存在公共前缀，返回空字符串 ''。\n\n示例：longest_common_prefix(['flower', 'flow', 'flight']) -> 'fl'",
        "starter": "def longest_common_prefix(strs):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [["flower", "flow", "flight"]], "expected": "fl"},
            {"args": [["dog", "racecar", "car"]], "expected": ""},
            {"args": [["a"]], "expected": "a"},
            {"args": [["abc", "ab", "a"]], "expected": "a"},
        ],
        "hint": "以第一个字符串为基准，逐个字符与其余字符串比较。",
        "solution": "def longest_common_prefix(strs):\n    if not strs:\n        return ''\n    first = strs[0]\n    for i in range(len(first)):\n        for s in strs[1:]:\n            if i >= len(s) or s[i] != first[i]:\n                return first[:i]\n    return first\n",
    },
    {
        "slug": "transpose",
        "title": "矩阵转置",
        "category": "算法进阶", "difficulty": "medium", "func": "transpose",
        "body": "实现函数 transpose(matrix)，把二维矩阵转置（行变列，列变行）。\n返回列表的列表。\n\n示例：transpose([[1, 2, 3], [4, 5, 6]]) -> [[1, 4], [2, 5], [3, 6]]",
        "starter": "def transpose(matrix):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [[[1, 2, 3], [4, 5, 6]]], "expected": [[1, 4], [2, 5], [3, 6]]},
            {"args": [[[1]]], "expected": [[1]]},
            {"args": [[[1, 2], [3, 4]]], "expected": [[1, 3], [2, 4]]},
        ],
        "hint": "zip(*matrix) 可以直接转置，再转成 list of list。",
        "solution": "def transpose(matrix):\n    return [list(row) for row in zip(*matrix)]\n",
    },
    {
        "slug": "quick-sort",
        "title": "快速排序",
        "category": "算法进阶", "difficulty": "hard", "func": "quick_sort",
        "body": "实现函数 quick_sort(lst)，用快速排序把列表升序排列并返回新列表。\n不能使用 sorted()。\n\n示例：quick_sort([3, 6, 1, 8, 2]) -> [1, 2, 3, 6, 8]",
        "starter": "def quick_sort(lst):\n    # 不能使用 sorted()\n    pass\n",
        "tests": [
            {"args": [[3, 6, 1, 8, 2]], "expected": [1, 2, 3, 6, 8]},
            {"args": [[]], "expected": []},
            {"args": [[5]], "expected": [5]},
            {"args": [[2, 2, 1]], "expected": [1, 2, 2]},
            {"args": [[9, 1, 8, 2, 7, 3]], "expected": [1, 2, 3, 7, 8, 9]},
        ],
        "hint": "选基准 pivot，把小于、等于、大于基准的三部分分别递归排序后拼接。",
        "solution": "def quick_sort(lst):\n    if len(lst) <= 1:\n        return lst\n    pivot = lst[len(lst) // 2]\n    left = [x for x in lst if x < pivot]\n    mid = [x for x in lst if x == pivot]\n    right = [x for x in lst if x > pivot]\n    return quick_sort(left) + mid + quick_sort(right)\n",
    },
    {
        "slug": "longest-substring",
        "title": "最长无重复字符子串",
        "category": "算法进阶", "difficulty": "hard", "func": "length_of_longest_substring",
        "body": "实现函数 length_of_longest_substring(s)，返回字符串中不含重复字符的最长子串的长度。\n\n示例：length_of_longest_substring('abcabcbb') -> 3（'abc'）\n     length_of_longest_substring('pwwkew')   -> 3（'wke'）",
        "starter": "def length_of_longest_substring(s):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": ["abcabcbb"], "expected": 3},
            {"args": ["bbbbb"], "expected": 1},
            {"args": ["pwwkew"], "expected": 3},
            {"args": [""], "expected": 0},
            {"args": ["dvdf"], "expected": 3},
        ],
        "hint": "滑动窗口：用字典记录字符最后出现的位置，遇到重复就移动左边界。",
        "solution": "def length_of_longest_substring(s):\n    last = {}\n    left = 0\n    best = 0\n    for i, ch in enumerate(s):\n        if ch in last and last[ch] >= left:\n            left = last[ch] + 1\n        last[ch] = i\n        best = max(best, i - left + 1)\n    return best\n",
    },
    {
        "slug": "max-profit",
        "title": "股票最佳买卖时机",
        "category": "算法进阶", "difficulty": "hard", "func": "max_profit",
        "body": "实现函数 max_profit(prices)：prices[i] 是第 i 天的股价，\n只允许买卖一次（先买后卖），求最大利润。若不可能盈利则返回 0。\n\n示例：max_profit([7, 1, 5, 3, 6, 4]) -> 5（第 2 天买 1，第 5 天卖 6）",
        "starter": "def max_profit(prices):\n    # 在这里写你的代码\n    pass\n",
        "tests": [
            {"args": [[7, 1, 5, 3, 6, 4]], "expected": 5},
            {"args": [[7, 6, 4, 3, 1]], "expected": 0},
            {"args": [[1]], "expected": 0},
            {"args": [[2, 4, 1]], "expected": 2},
            {"args": [[3, 8, 1, 9]], "expected": 8},
        ],
        "hint": "遍历时维护「到目前为止的最低买入价」，用当天价减去它更新最大利润。",
        "solution": "def max_profit(prices):\n    if not prices:\n        return 0\n    low = prices[0]\n    best = 0\n    for p in prices[1:]:\n        if p < low:\n            low = p\n        elif p - low > best:\n            best = p - low\n    return best\n",
    },
]


CATEGORIES = ["基础语法", "字符串", "列表", "字典与集合", "函数与递归", "算法进阶"]


def seed_problems(conn=None) -> int:
    """把 PROBLEMS 写入数据库；已存在（按 slug）则更新。返回题目总数。"""
    import json as _json
    from .db import get_conn, query_one

    own = conn is None
    if own:
        conn = get_conn()
    n = 0
    try:
        for p in PROBLEMS:
            tests_json = _json.dumps(p["tests"], ensure_ascii=False)
            row = query_one("SELECT id FROM problems WHERE slug = ?", (p["slug"],))
            if row:
                conn.execute(
                    "UPDATE problems SET title=?, body=?, difficulty=?, category=?, "
                    "starter=?, func=?, tests=?, hint=?, solution=? WHERE id=?",
                    (p["title"], p["body"], p["difficulty"], p["category"],
                     p["starter"], p["func"], tests_json, p.get("hint", ""),
                     p.get("solution", ""), row["id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO problems(slug,title,body,difficulty,category,"
                    "starter,func,tests,hint,solution) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (p["slug"], p["title"], p["body"], p["difficulty"], p["category"],
                     p["starter"], p["func"], tests_json, p.get("hint", ""),
                     p.get("solution", "")),
                )
            n += 1
        conn.commit()
    finally:
        if own:
            conn.close()
    return n
