@echo off
REM ============================================================
REM  enable_pages.bat - 一键启用 GitHub Pages
REM  复用之前 git credential helper 配好的 PAT
REM ============================================================

setlocal

set PYTHON_EXE=C:\Users\Administrator\.workbuddy\binaries\python\envs\default\Scripts\python.exe
set SCRIPT_DIR=%~dp0
set SCRIPT=%SCRIPT_DIR%enable_pages.py

echo.
echo ============================================================
echo   auto-money-agent - GitHub Pages 自动启用脚本
echo ============================================================
echo.

"%PYTHON_EXE%" "%SCRIPT%"

echo.
pause
endlocal