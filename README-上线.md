# 🚀 把 PyOJ 搬到公网（GitHub + Render）

分两步：**先把代码传到 GitHub**，**再让 Render 从 GitHub 拉取并生成外网网址**。
全程不用买服务器、不用备案。

---

## 第一步：传到 GitHub（约 1 分钟）

项目已经和你的仓库绑定好了（`https://github.com/b555561/python_oj.git`），代码也已提交。

### 做法：双击项目根目录的 `push-github.bat`

- 第一次运行会**自动弹出浏览器**让你登录 GitHub，点绿色的 **Authorize** 授权
- 之后命令行会滚动一堆 `Writing objects`，最后出现：

  ```
  * [new branch]      main -> main
  ```

  就是成功了

- 如果浏览器没弹出来，就自己去 <https://github.com/login/device> 看有没有待授权提示

### 以后改了代码想同步

双击 `sync-github.bat`（自动提交 + 推送），Render 会**自动重新部署**。

### 手动命令版（可选）

```bash
cd D:\python_oj
git push -u origin main
```

---

## 第二步：Render 一键生成外网网址（约 3 分钟）

仓库里已经放好了 `render.yaml`，Render 会照着它自动配置，你只要点几下。

1. 打开 <https://render.com> → 右上角 **Get Started**（用 GitHub 账号登录最省事）
2. 登录后点 **Dashboard** → 右上角 **New +** → **Blueprint**（⚠️ 选 Blueprint，不要选 Web Service）
3. 选中仓库 `b555561/python_oj` → 点 **Connect**
4. Render 读到 `render.yaml`，直接点 **Apply**
5. 等 3～5 分钟构建（第一次要装依赖），状态变绿 **Live** 之后，
   页面顶部就会出现网址：

   ```
   https://pyoj.onrender.com      ← 把这个发给别人就行
   ```

   名字可能被占用，Render 会自动改成 `pyoj-xxxx.onrender.com` 之类，以实际显示为准。

### 改配置（可选）

想换名字 / 换地区，改仓库根目录的 `render.yaml`：

```yaml
services:
  - type: web
    name: pyoj              # 改这里 = 改网址前缀
    region: singapore       # 新加坡节点，国内访问相对快
    plan: free
```

改完 `sync-github.bat` 推上去，Render 会自动重新部署。

---

## ⚠️ 免费版必须知道的两件事

| 事项 | 说明 | 影响 |
|---|---|---|
| **会休眠** | 15 分钟没人访问，实例自动睡；下次有人打开要等 30～60 秒才起来 | 第一次打开慢，之后就快了 |
| **数据会重置** | 免费版磁盘不持久，实例重启/重新部署后 `database.db` 归零 | 注册的账号、种下的菜会没了（34 道题会自动重新灌入，代码不受影响） |

**只是给人看效果、演示用** → 免费版完全够。
**想让账号和数据长期保留** → 需要 Render 付费 Starter（$7/月，可挂持久磁盘），
或者换下面两个方案之一。

---

## 备选方案

### 方案 B：Railway（数据可持久）

1. <https://railway.app> → 用 GitHub 登录 → **New Project** → **Deploy from GitHub repo**
2. 选 `python_oj`，Railway 会识别 `Procfile` 自动部署
3. 进服务页 → **Settings** → **Networking** → **Generate Domain** 得到 `https://xxx.up.railway.app`
4. 想保留数据：**Variables** 里加 `DATABASE_PATH=/data/database.db`，再挂一个 Volume 到 `/data`

新账号有试用额度，用完需付费。

### 方案 C：PythonAnywhere（免费 + 数据持久，但要手动配置）

1. 注册 <https://www.pythonanywhere.com>（免费 Beginner 账号）
2. 打开 **Bash console**，执行：

   ```bash
   git clone https://github.com/b555561/python_oj.git
   cd python_oj
   pip install --user -r requirements.txt
   ```

3. 顶部 **Web** 页签 → **Add a new web app** → 选 **Manual configuration** → Python 3.11
4. 改 WSGI 配置文件内容为：

   ```python
   import sys
   sys.path.insert(0, "/home/你的用户名/python_oj")
   from main import app as application
   ```

5. 点绿色 **Reload** → 网址是 `https://你的用户名.pythonanywhere.com`

免费版磁盘持久，数据不会丢；缺点是国内访问速度一般，且 3 个月不登录会停用。

---

## 部署前的自检（可选但建议）

```bash
cd D:\python_oj
.\ven\Scripts\python.exe run.py          # 先启动
.\ven\Scripts\python.exe tools\run_all_tests.py   # 跑全量回归，全过再推
```

---

## 常见问题

**Q：推 GitHub 时提示 `Authentication failed`？**
A：GitHub 从 2021 年起不再接受账号密码。用 `push-github.bat` 走浏览器授权，
或者去 <https://github.com/settings/tokens> 生成一个 **repo** 权限的 Personal Access Token，
把它当密码填。

**Q：Render 构建失败说 `pip install` 报错？**
A：多半是 `requirements.txt` 里某个版本在你环境装不上。可先改成不锁版本：

```
fastapi
uvicorn
jinja2
python-multipart
pydantic
requests
```

**Q：网址打开是 502 / 一直转圈？**
A：免费实例在睡觉，等 1 分钟再刷新。若持续 502，去 Render 的 **Logs** 看报错。

**Q：会不会把我的密钥传上去？**
A：不会。`.gitignore` 已经把 `.secret_key`、`database.db`、`config.json` 全部排除，
`git status` 里看不到它们。部署到云端后这些文件会自动重新生成。
