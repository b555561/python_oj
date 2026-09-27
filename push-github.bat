@echo off
chcp 936 >nul
cd /d %~dp0
echo.
echo ====================================================
echo   把本地已提交的代码推送到 GitHub
echo   仓库： https://github.com/b555561/python_oj
echo.
echo   第一次运行会弹浏览器让你登录 GitHub，按提示点
echo   "Authorize" 即可，之后就一直记住了。
echo ====================================================
echo.
git push -u origin main
echo.
echo ----------------------------------------------------
echo 看到 "main -> main" 或 "Everything up-to-date" 就是成功。
echo ----------------------------------------------------
echo.
pause
