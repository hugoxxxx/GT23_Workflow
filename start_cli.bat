@echo off
REM GT23 Film Workflow - CLI Launcher
REM EN: Quick launcher for CLI application
REM CN: CLI 应用快速启动脚本

echo ========================================
echo    GT23 Film Workflow - CLI Launcher
echo    GT23 胶片工作流 - CLI 启动器
echo ========================================
echo.

REM Activate environment and run
echo [*] Starting CLI... / 正在启动 CLI...
call conda activate gt23
python main_cli.py

if errorlevel 1 (
    echo.
    echo [ERROR] CLI failed to start / CLI 启动失败
    pause
)
