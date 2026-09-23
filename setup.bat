@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo   PyOJ 耘码 · 首次运行准备
echo   ----------------------------------------
echo   本脚本会做两件事：
echo     1. 在本目录创建独立的 Python 虚拟环境 ven\
echo     2. 安装 requirements.txt 里的全部依赖
echo   装完之后，双击 run.bat 即可启动网站。
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo   [错误] 没检测到 Python，请先安装 Python 3.9 以上版本：
    echo          https://www.python.org/downloads/
    echo          安装时务必勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo   正在创建虚拟环境 ven\ ...
python -m venv ven
if errorlevel 1 (
    echo   [错误] 虚拟环境创建失败，请确认 Python 已正确安装。
    pause
    exit /b 1
)

echo   正在安装依赖（首次约需 1-3 分钟，请耐心等待）...
"ven\Scripts\python.exe" -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple
"ven\Scripts\python.exe" -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo.
    echo   [提示] 清华源安装失败，改用官方源重试...
    "ven\Scripts\python.exe" -m pip install -r requirements.txt
)

echo.
echo   ============================================
echo     依赖安装完成！现在可以双击 run.bat 启动网站。
echo   ============================================
echo.
pause
