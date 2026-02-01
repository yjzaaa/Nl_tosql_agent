@echo off
REM PostgreSQL图形化界面启动脚本
REM 用于启动pgAdmin4

echo ========================================
echo PostgreSQL Graphical Interface Launcher
echo ========================================
echo.

REM 设置pgAdmin路径
set PGADMIN_PATH=D:\postgres\pgAdmin 4\runtime\pgAdmin4.exe

REM 检查pgAdmin是否存在
if not exist "%PGADMIN_PATH%" (
    echo [ERROR] pgAdmin not found at: %PGADMIN_PATH%
    echo.
    echo Please check PostgreSQL installation.
    echo.
    pause
    exit /b 1
)

echo [OK] pgAdmin4 found
echo.

REM 检查PostgreSQL服务是否运行
sc query postgresql-x64-18 | find "RUNNING" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] PostgreSQL service is running
) else (
    echo [WARNING] PostgreSQL service may not be running
    echo.
    echo To start PostgreSQL service:
    echo   sc start postgresql-x64-18
    echo.
)

echo.
echo ========================================
echo Starting pgAdmin4...
echo ========================================
echo.

REM 启动pgAdmin4
start "" "%PGADMIN_PATH%"

echo [OK] pgAdmin4 is starting...
echo.
echo Please wait for pgAdmin4 to open in your browser.
echo.
echo ========================================
echo Database Connection Info:
echo ========================================
echo.
echo Host: localhost
echo Port: 5432
echo Database: cost_allocation
echo User: postgres
echo Password: 123456
echo.
echo Connection string:
echo postgresql://postgres:123456@localhost:5432/cost_allocation
echo.
echo ========================================
echo Commands to connect via psql:
echo ========================================
echo.
echo Connect to default database:
echo   D:\postgres\bin\psql.exe -U postgres
echo.
echo Connect to cost_allocation database:
echo   D:\postgres\bin\psql.exe -U postgres -d cost_allocation
echo.
echo View all tables:
echo   D:\postgres\bin\psql.exe -U postgres -d cost_allocation -c "\dt"
echo.
echo View cost_database table:
echo   D:\postgres\bin\psql.exe -U postgres -d cost_allocation -c "SELECT * FROM cost_database LIMIT 10;"
echo.
echo ========================================

pause
