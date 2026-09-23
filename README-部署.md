# PyOJ 耘码 · 让别人访问你的网站（完整操作指南）

> 网站目录：`D:\python_oj`
> 本文所有命令都在项目目录里执行。先 `cd /d D:\python_oj`，或在资源管理器里打开该文件夹、地址栏输入 `cmd` 回车。

---

## 零、先说结论（30 秒版）

| 你想达到的效果 | 选哪个方案 | 难度 |
|---|---|---|
| **防止网站丢失**（最重要，必须做） | 第 1 节：备份 | ⭐ |
| 让别人拿到源码，自己电脑上跑 | 第 3 节：发源码包 | ⭐⭐ |
| 把代码托管起来，随时回滚 | 第 2 节：GitHub | ⭐⭐ |
| 同 WiFi 的人立刻能打开 | 第 4 节 A：局域网 | ⭐ |
| 外网（异地）的人能打开 | 第 4 节 B/C/D：内网穿透 / 云部署 | ⭐⭐⭐ |

**我的建议组合**：先做第 1 节备份 → 再做第 2 节 GitHub（这是最可靠的防丢失手段）→ 需要给别人用就走第 3 节或第 4 节。

---

## 一、防止丢失：备份（已完成，学会再来一次）

### 1.1 已经替你做好的

| 位置 | 文件 | 内容 |
|---|---|---|
| `D:\PyOJ备份\` | `PyOJ备份_完整版_2026-09-23_1637.zip` | **含数据库和密钥**，可原样恢复 |
| `D:\PyOJ备份\` | `PyOJ备份_纯净版_2026-09-23_1637.zip` | 不含数据，用于发给别人 |
| `C:\Users\Yangw\Desktop\` | 完整版副本一份 | 异地副本（C 盘，与 D 盘不共享风险） |
| `D:\python_oj\.git\` | 已做首次提交 | 代码版本快照，可随时回滚 |

另外代码已经 **git 提交** 了一次，等于多了一份带历史的存档。

### 1.2 以后想再备份，一条命令

```bat
ven\Scripts\python.exe tools\backup.py
```

加参数可以换模式：

```bat
ven\Scripts\python.exe tools\backup.py --public          :: 纯净版，发给别人用
ven\Scripts\python.exe tools\backup.py --to "E:\我的备份" :: 换输出目录
```

脚本会自动：打时间戳 → 压缩 → **读一遍校验 CRC**（坏包当场报错，不会给你一个打不开的 zip）。

### 1.3 可靠的备份习惯：3-2-1

- **3** 份副本：本机 `D:\PyOJ备份` + 桌面（已完成两份）+ GitHub（做完第 2 节就有第三份）
- **2** 种介质：硬盘 + 云端（GitHub / 网盘）
- **1** 份异地：桌面那份算一份，最好再往**网盘或邮箱**发一份纯净版

> 建议：每做完一轮大改动就跑一次备份命令，几秒钟的事。

---

## 二、方案 A：上传到 GitHub（最推荐，防丢失 + 方便分享）

**好处**：免费、有完整历史记录、随时回滚到任意版本、别人一键拿到源码、还能直接拿去云部署。

### 步骤 1：注册 GitHub

打开 https://github.com → Sign up → 用邮箱注册 → 到邮箱点验证链接。

### 步骤 2：新建仓库

1. 登录后右上角点 **+** → **New repository**
2. Repository name 填：`pyoj`（只能用英文/数字/横线）
3. 选 **Public**（公开，别人才能看到）或 Private（私密）
4. **重要**：下面三个勾选框**都不要勾**（Initialize README / Add .gitignore / Choose license）—— 因为本地已经有代码了，勾了会导致冲突
5. 点 **Create repository**

### 步骤 3：拿到你的推送地址

建好后页面会显示一个地址，形如：

```
https://github.com/你的用户名/pyojs.git
```

（如果建的是 Public，还会提示你用 HTTPS 还是 SSH，选 **HTTPS**）

### 步骤 4：在本地推送（我已经帮你做好了前面几步）

我已经完成了 `git init`、`git add`、首次 `git commit`，**你只需要执行下面两条命令**：

```bat
cd /d D:\python_oj

git remote add origin https://github.com/你的用户名/pyojs.git
git push -u origin master
```

> 把 `你的用户名` 换成你真实的 GitHub 用户名。

如果提示输入账号密码：

- **用户名**：你的 GitHub 用户名
- **密码**：**不是登录密码**！要去 GitHub 生成 Personal Access Token：
  右上角头像 → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token → 勾 `repo` → 生成后复制，粘到密码框里。

看到类似下面的输出就成功了：

```
Enumerating objects: 120, done.
...
To https://github.com/xxx/pyojs.git
 * [new branch]      master -> master
```

### 步骤 5：检查一下

刷新 GitHub 仓库页面，应该能看到 97 个文件。

**请确认这几样东西没有出现**（出现了就是泄露，赶紧删）：

- ❌ `.secret_key`
- ❌ `database.db`
- ❌ `config.json`
- ❌ `tools/push_config.json`
- ❌ `ven/` 文件夹

> 我已经在 `.gitignore` 里配好了排除规则，正常不会出现。

### 步骤 6：以后更新代码

```bat
git add -A
git commit -m "改了什么"
git push
```

### 别人怎么拿

把仓库地址发给他：`https://github.com/你的用户名/pyojs`
他点 **Code → Download ZIP**，或者：

```bat
git clone https://github.com/你的用户名/pyojs.git
```

---

## 三、方案 B：直接把源码发给对方（最简单）

### 步骤 1：生成纯净版包

```bat
ven\Scripts\python.exe tools\backup.py --public
```

产出在 `D:\PyOJ备份\PyOJ备份_纯净版_时间戳.zip`，约 **1.6 MB**，微信/QQ/邮件都能直接发。

> 为什么用纯净版而不是完整版：纯净版不含你的数据库（里面的测试账号、聊天记录）和会话密钥，发出去更安全。

### 步骤 2：发给对方

微信传文件、QQ、邮件附件、百度网盘 —— 都行。

### 步骤 3：告诉对方怎么运行（把这段话一起发过去）

> **运行方法（3 步）**
>
> 1. 先装 Python 3.9 以上：https://www.python.org/downloads/
>    **安装时务必勾选 "Add Python to PATH"**（安装界面最下面那个勾）
> 2. 解压后进入文件夹，**双击 `setup.bat`** —— 会自动装好所有依赖，等 1~3 分钟
> 3. 再**双击 `run.bat`** —— 浏览器会打印一个地址（如 `http://127.0.0.1:8000`），打开即可

### 对方可能遇到的问题

| 现象 | 原因 | 解决 |
|---|---|---|
| `setup.bat` 说找不到 Python | 没装或没勾 PATH | 重装 Python，勾上 Add to PATH |
| 双击 `run.bat` 一闪而过 | 依赖没装 | 先跑 `setup.bat` |
| 端口被占用 | 8000 被别的软件占了 | 脚本会自动换 8001/8002，看屏幕提示 |
| 杀毒软件报警 | Python 打包误报 | 选择允许 |
| 页面能开但图片不显示 | 极少见 | 检查 `static\images\banners\` 里有没有两个 png |

---

## 四、方案 C：让别人真正"在线访问"

这三种是让别人不用装任何东西、直接打开网址就能用。

### C-A：局域网（同一 WiFi）—— 零成本，30 秒搞定

适合：同学在同一个教室/办公室、家里两台电脑。

**操作**：双击 `run-lan.bat`

屏幕上会打印：

```
本机打开：     http://127.0.0.1:8000
局域网其他人： http://192.168.43.4:8000
```

把 `http://192.168.43.4:8000` 这个地址发给对方即可。

**如果对方打不开**（多半是 Windows 防火墙拦了）：

1. 按 `Win` 键，输入 `防火墙`，打开 **"Windows Defender 防火墙"**
2. 点左侧 **"允许应用或功能通过 Windows Defender 防火墙"**
3. 点 **"更改设置"** → **"允许其他应用"** → 浏览，选中 `D:\python_oj\ven\Scripts\python.exe` → 添加
4. 把"专用"和"公用"都勾上 → 确定

> 需要管理员权限。如果你的账户没有管理员权限，可以请机房管理员帮忙，或者改用其他方案。

**局限**：你的电脑关机，网站就没了。

---

### C-B：内网穿透 —— 临时给外网访问

适合：临时演示，几小时到几天。

推荐 **cpolar**（https://www.cpolar.com）或 **natapp**（https://natapp.cn）：

1. 注册账号（国内手机号，免费版够用）
2. 下载客户端，解压
3. 拿到你的 authtoken，在客户端里配置
4. 执行（把 8000 换成你实际的端口）：

```bat
cpolar http 8000
```

它会给你一个公网地址，形如 `https://abc123.cpolar.cn`，发给任何人都能打开。

**局限**：免费版域名每次重启会变；你的电脑关机就没了。

---

### C-C：云部署 Render.com —— 永久在线（免费）

适合：想要一个长期存在的公开网址。

**操作**：

1. 打开 https://render.com ，用 **GitHub 账号** 登录（所以要先做完第 2 节）
2. 点 **New +** → **Web Service**
3. 选中你刚推上去的 `pyoj` 仓库 → Connect
4. 填写：

| 项目 | 填什么 |
|---|---|
| Name | `pyoj` |
| Region | **Singapore**（新加坡，国内访问相对快） |
| Branch | `master` |
| Runtime | **Python 3** |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python run.py` |
| Instance Type | **Free** |

5. 展开 **Advanced**，加两个环境变量：

| Key | Value |
|---|---|
| `HOST` | `0.0.0.0` |
| `PORT` | `10000` |

6. 点 **Create Web Service**，等 3~5 分钟构建完成
7. 顶部会出现网址：`https://pyoj.onrender.com` —— 这就是你的公网地址

**⚠ 免费的代价（务必知道）**：

| 问题 | 说明 |
|---|---|
| 会休眠 | 15 分钟没人访问就睡，下次访问要**等 30~50 秒**才醒 |
| **数据不保** | 免费层的磁盘是临时的，重启后**用户账号、做题记录会全部重置**（34 道题会自动重建，因为题目是代码里生成的） |

> 所以免费云部署更适合当**演示站**（让人看看效果、注册个号体验一下）。
> 如果要当**真正长期使用的站**，需要 Render 付费磁盘（约 $7/月），或者用 C-D。

> 我已经把 `render.yaml` 和 `Dockerfile` 都准备好了，也可以用 **Blueprint** 方式一键部署（New → Blueprint → 选仓库，会自动读 `render.yaml`）。

---

### C-D：买一台云服务器 —— 最稳、数据不丢

适合：打算长期运营、数据必须保住。

**推荐**：腾讯云轻量应用服务器（经常有活动，2核2G 一年几十到一百多块）或阿里云。

**大致步骤**：

1. 买服务器，系统选 **Ubuntu 22.04** 或 **Windows Server**
2. 在控制台的**防火墙**里放行端口（比如 8000）
3. 用远程桌面/SSH 连上去，把纯净版 zip 传上去解压
4. Linux 上执行：

```bash
pip3 install -r requirements.txt
HOST=0.0.0.0 PORT=8000 nohup python3 run.py > pyoj.log 2>&1 &
```

5. 浏览器打开 `http://服务器公网IP:8000`

**好处**：数据 100% 在你自己手里，永不丢失，也不休眠。

---

## 五、数据保全：关于 `database.db`

### 它是什么

`D:\python_oj\database.db` 是 **SQLite 数据库**，里面存着：

- 所有用户账号、密码哈希
- 做题记录、AC 数、经验等级
- 菜园地块、菜篮、金币、能量
- 学习圈帖子、认证证书

**题目内容不在里面**（34 道题是 `core/seed.py` 在启动时自动灌入的），所以数据库丢了题还在，但**用户数据会没**。

### 怎么备份它

- 直接复制 `database.db` 文件即可（服务运行时复制可能不完整，用备份脚本最稳，它用了 SQLite 官方一致性快照接口）
- 完整版备份包里已经包含

### 怎么恢复

把 `database.db` 放回项目根目录，覆盖同名文件，重启网站即可。

### 云部署时的数据风险

Render 免费层会重置磁盘 → 用户数据会丢。
解决办法：① 升级付费磁盘；② 定期把 `database.db` 下载下来存档；③ 用 C-D 云服务器。

---

## 六、排障速查表

| 症状 | 原因 | 解决 |
|---|---|---|
| 双击 `run.bat` 一闪而过 | 缺依赖 | 先跑 `setup.bat` |
| 提示 `No module named fastapi` | 用了系统 Python 而不是虚拟环境 | 用 `ven\Scripts\python.exe` 运行 |
| 端口被占用 | 8000 被占 | 脚本自动换端口，看屏幕提示 |
| 页面 500 错误 | 模板文件缺失 | 检查 `templates\` 下有没有 `_nav.html` 等 6 个下划线开头的文件 |
| 局域网别人打不开 | 防火墙 | 见 C-A 的放行步骤 |
| 登录后立刻掉线 | `.secret_key` 被删了或换了机器 | 删掉 `.secret_key` 会自动重新生成，所有人需重新登录 |
| 改了代码页面没变 | 模板有缓存 | **重启服务**（关掉黑窗口重新双击 `run.bat`） |
| 数据库报错 `unable to open database file` | 权限问题 | 确认项目目录可写 |

---

## 附录：常用命令一览

```bat
:: 启动网站（本机）
run.bat

:: 启动网站（局域网共享）
run-lan.bat

:: 首次安装依赖
setup.bat

:: 备份（完整版，含数据）
ven\Scripts\python.exe tools\backup.py

:: 备份（纯净版，发别人）
ven\Scripts\python.exe tools\backup.py --public

:: 跑全站回归测试（16 个套件 / 1147 项）
ven\Scripts\python.exe tools\run_all_tests.py

:: 更新代码到 GitHub
git add -A
git commit -m "改了什么"
git push
```

---

## 现在建议你按这个顺序做

1. ✅ ~~备份~~（已完成，两份 + 桌面一份）
2. **做第 2 节 GitHub** —— 这是最可靠的防丢失手段，**强烈建议今天就做**
3. 需要给别人用 → 做第 3 节（发纯净版 zip）
4. 想要公网网址 → 做第 4 节（先试 C-A 局域网，效果好再上 C-C 或 C-D）
