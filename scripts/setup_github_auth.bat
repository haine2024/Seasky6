@echo off
REM ============================================================
REM set up GitHub authentication with PAT (Windows cmd version)
REM PAT is typed at terminal prompt; never saved to disk unencrypted.
REM ============================================================

setlocal enabledelayedexpansion

cd /d "%~dp0\.."

echo === GitHub auth helper ===
echo.
echo We'll configure git so your PAT is remembered by Windows.
echo Credential Manager stores it encrypted; we never write it to disk.
echo.

set /p GH_USER="GitHub username (e.g. haine2024): "
set /p REPO="Repo name on GitHub (e.g. auto-money-agent): "

if "%GH_USER%"=="" set GH_USER=haine2024
if "%REPO%"=="" set REPO=auto-money-agent

set REPO_URL=https://github.com/%GH_USER%/%REPO%.git

git remote remove origin >nul 2>&1
git remote add origin %REPO_URL%
echo Remote set: %REPO_URL%
echo.

REM Use Git Credential Manager (comes with Git for Windows)
git config --global credential.helper manager
echo Credential helper → Windows Credential Manager (encrypted)
echo.

echo === Ready to push ===
echo When prompted:
echo   Username: %GH_USER%
echo   Password: ^<paste your PAT; nothing will appear while typing^>
echo.

set /p PUSH="Push now? [Y/n]: "
if /i "%PUSH%"=="n" goto :skip
git push -u origin main
if %errorlevel% neq 0 (
  echo.
  echo ❌ Push failed. If you got 403, your PAT is wrong or lacks 'repo' scope.
  echo Re-make the PAT and retry.
  pause
  exit /b 1
)
echo ✅ Pushed.
goto :eof

:skip
echo Skipped. Run later:  git push -u origin main

pause
