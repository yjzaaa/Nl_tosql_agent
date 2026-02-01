@echo off
REM 虚拟环境测试运行脚本
REM 使用方法: run_tests_venv.bat [测试文件路径]

echo ========================================
echo 虚拟环境测试脚本
echo ========================================
echo.

REM 检查虚拟环境是否存在
if not exist ".venv\Scripts\python.exe" (
    echo [错误] 虚拟环境不存在！
    echo 请先运行: python -m venv .venv
    exit /b 1
)

echo [✓] 虚拟环境已找到
echo.

REM 获取参数
set TEST_PATH=%1
if "%TEST_PATH%"=="" (
    echo 运行所有测试...
    .venv\Scripts\python.exe -m pytest -v
) else (
    echo 运行测试: %TEST_PATH%
    .venv\Scripts\python.exe -m pytest %TEST_PATH% -v
)

echo.
echo ========================================
echo 测试完成
echo ========================================
pause
