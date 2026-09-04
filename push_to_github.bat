@echo off
REM ============================================================
REM Push auto-money-agent to GitHub and enable Pages (Windows).
REM Double-click or run from cmd / Git Bash.
REM ============================================================

setlocal enabledelayedexpansion

where git >nul 2>nul
if %errorlevel% neq 0 (
  echo ❌ git not found. Install from https://git-scm.com
  exit /b 1
)

echo.
echo === GitHub Deploy Helper ===
echo.

set /p GH_USER="GitHub username (e.g. haine2024): "
set /p REPO="Repo name on GitHub (e.g. auto-money-agent): "

if "%GH_USER%"=="" set GH_USER=haine2024
if "%REPO%"=="" set REPO=auto-money-agent

set REPO_URL=https://github.com/%GH_USER%/%REPO%.git

if not exist .git (
  git init
  git checkout -B main 2>nul || git branch -M main
) else (
  git branch -M main
)

git add .
git diff --cached --quiet
if %errorlevel% neq 0 (
  git commit -m "init: tool station pipeline + 3 demo tools"
) else (
  echo Nothing to commit.
)

git remote get-url origin >nul 2>&1
if %errorlevel% neq 0 (
  git remote add origin %REPO_URL%
) else (
  echo Remote origin already exists.
)

echo.
echo Pushing to %REPO_URL% ...
git push -u origin main
if %errorlevel% neq 0 (
  echo.
  echo ❌ Push failed. Most common causes:
  echo    - Repo doesn't exist on GitHub yet (create it first)
  echo    - Not logged in to git (run: gh auth login)
  echo    - Wrong HTTPS token / SSH key
  exit /b 1
)

echo.
echo ✅ Pushed.
echo.
echo One-time UI setup:
echo   1. Open https://github.com/%GH_USER%/%REPO%/settings/pages
echo   2. Source: "GitHub Actions"
echo   3. Wait ~60s. Site will be at https://%GH_USER%.github.io/%REPO%/
echo.

pause
