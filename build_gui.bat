@echo off
setlocal EnableExtensions
chcp 65001 >nul
REM GT23 Film Workflow - Build (GUI)
REM EN: Build GUI executable using existing conda env
REM CN: 使用现有 conda 环境打包 GUI 可执行文件

echo ========================================
echo    GT23 Film Workflow - GUI Build
echo    GT23 胶片工作流 - GUI 打包
echo ========================================
echo.

REM Ensure env exists and activate
call conda info --envs | findstr /C:"gt23" >nul 2>&1
if errorlevel 1 (
    echo [!] Environment 'gt23' not found / 未找到环境 'gt23'
    echo [*] Please run start_gui.bat once to create it
    echo [*] 请先运行 start_gui.bat 创建环境
    pause
    exit /b 1
)

echo [*] Activating env 'gt23'...
call conda activate gt23
if errorlevel 1 (
    echo [ERROR] Failed to activate env / 激活环境失败
    pause
    exit /b 1
)

echo [*] Installing/refreshing GUI deps...
pip install -r requirements-gui.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed / 依赖安装失败
    pause
    exit /b 1
)

echo [*] Cleaning previous build outputs...
echo [*] Checking running instance and unlocking files...
taskkill /F /IM GT23_Workflow.exe >nul 2>&1
timeout /t 1 >nul
if exist dist\GT23_Workflow.exe del /F /Q dist\GT23_Workflow.exe
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist

echo [*] Building with PyInstaller...
pyinstaller build.spec
if errorlevel 1 (
    echo [ERROR] Build failed / 打包失败
    pause
    exit /b 1
)

echo.
echo [OK] Build completed. Output:
echo      dist\GT23_Workflow\GT23_Workflow.exe
echo.
echo [Hint] Pin the new EXE to taskbar to update icon
echo [提示] 将新的 EXE 固定到任务栏以更新图标
pause
