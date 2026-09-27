@echo off
chcp 936 >nul
cd /d %~dp0
echo.
echo ====================================================
echo   一键保存本机改动并推送到 GitHub
echo   （会自动跳过 database.db / .secret_key 等私密文件）
echo ====================================================
echo.
git add -A
git commit -m "update: 本机改动同步"
git push origin main
echo.
echo ----------------------------------------------------
echo 看到 "main -> main" 就是成功。
echo ----------------------------------------------------
echo.
pause
