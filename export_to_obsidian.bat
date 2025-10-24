@echo off
chcp 65001 >nul
REM LAE Obsidian 导出工具 - 启动脚本

echo.
echo ========================================
echo LAE Obsidian 导出工具
echo ========================================
echo.

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 运行Python脚本
python export_to_obsidian.py

echo.
echo 按任意键退出...
pause >nul
