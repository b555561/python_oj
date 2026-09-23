@echo off
chcp 65001 >nul
cd /d "%~dp0"
"%~dp0ven\Scripts\python.exe" run.py
pause
