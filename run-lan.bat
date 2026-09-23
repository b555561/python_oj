@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   局域网模式：同一 WiFi 下的同学 / 同事都能打开你的网站
echo   启动后请把屏幕上打印出来的 http://192.168.x.x:8000 发给对方
echo   （打不开多半是防火墙拦了，处理方法见 README-部署.md）
echo.
"%~dp0ven\Scripts\python.exe" run.py --lan
pause
