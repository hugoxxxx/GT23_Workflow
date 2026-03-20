@echo off
REM scripts/sync_assets.bat
REM EN: Multi-Remote Sync Script for GT23_Assets (GitHub & Gitee)
REM CN: GT23_Assets 多仓库同步脚本 (GitHub & Gitee)

SET ASSET_DIR=GT23_Assets

echo [1/3] Navigating to Assets Submodule...
cd %ASSET_DIR%

REM EN: Check if Gitee remote exists, add if not
git remote get-url gitee >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Gitee remote not found. Please provide Gitee URL or run:
    echo     git remote add gitee https://gitee.com/USER/GT23_Assets.git
    echo.
    set /p GITEE_URL="Enter Gitee Repo URL (or press Enter to skip): "
    if not "%GITEE_URL%"=="" git remote add gitee %GITEE_URL%
)

echo [2/3] Pulling from GitHub (origin)...
git pull origin main

echo [3/3] Pushing to both remotes...
echo --- Pushing to GitHub (origin) ---
git push origin main

git remote get-url gitee >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo --- Pushing to Gitee (gitee) ---
    git push gitee main
) else (
    echo [!] Skipping Gitee push (remote not configured).
)

cd ..
echo [DONE] Asset Synchronization Complete!
pause
