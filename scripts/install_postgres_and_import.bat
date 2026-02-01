@echo off
REM PostgreSQL快速安装和导入脚本
REM 用于Windows环境

echo ========================================
echo PostgreSQL 安装和导入脚本
echo ========================================
echo.

REM 检查PostgreSQL是否已安装
where psql >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [OK] PostgreSQL is already installed
    psql --version
) else (
    echo [ERROR] PostgreSQL is not found!
    echo.
    echo Please install PostgreSQL first:
    echo 1. Visit: https://www.postgresql.org/download/windows/
    echo 2. Download and install PostgreSQL 16.x
    echo 3. Set superuser password (REMEMBER IT!)
    echo 4. Run this script again after installation
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Step 1: Create Database
echo ========================================
echo.

REM 提示输入数据库密码
set /p DB_PASSWORD="Enter PostgreSQL superuser password: "

REM 创建数据库
echo Creating database...
psql -U postgres -c "CREATE DATABASE cost_allocation;" -p %DB_PASSWORD%

if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Failed to create database (it may already exist)
) else (
    echo [OK] Database created successfully
)

echo.
echo ========================================
echo Step 2: Import Excel Data
echo ========================================
echo.

REM 设置Excel文件路径
set EXCEL_PATH=D:\AI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx

REM 检查Excel文件是否存在
if not exist "%EXCEL_PATH%" (
    echo [ERROR] Excel file not found: %EXCEL_PATH%
    echo.
    echo Please check the file path and try again.
    pause
    exit /b 1
)

echo [OK] Excel file found: %EXCEL_PATH%

REM 激活虚拟环境并运行导入脚本
echo.
echo Importing data to PostgreSQL...
echo.

call .venv\Scripts\activate
python import_to_postgres.py --excel "%EXCEL_PATH%" --db "postgresql://postgres:%DB_PASSWORD%@localhost:5432/cost_allocation"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Import failed!
    echo.
    echo Please check:
    echo 1. PostgreSQL password is correct
    echo 2. PostgreSQL service is running
    echo 3. Port 5432 is available
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Step 3: Verify Import
echo ========================================
echo.

echo Verifying imported data...
psql -U postgres -d cost_allocation -p %DB_PASSWORD% -c "SELECT COUNT(*) as total_rows FROM cost_database;"
psql -U postgres -d cost_allocation -p %DB_PASSWORD% -c "SELECT COUNT(*) as total_rows FROM rate_table;"
psql -U postgres -d cost_allocation -p %DB_PASSWORD% -c "SELECT COUNT(*) as total_rows FROM cc_mapping;"
psql -U postgres -d cost_allocation -p %DB_PASSWORD% -c "SELECT COUNT(*) as total_rows FROM cost_text_mapping;"

echo.
echo ========================================
echo Step 4: Statistics
echo ========================================
echo.

echo Rows by function:
psql -U postgres -d cost_allocation -p %DB_PASSWORD% -c "SELECT \"Function\", COUNT(*) as count FROM cost_database GROUP BY \"Function\" ORDER BY count DESC;"

echo.
echo Rows by key:
psql -U postgres -d cost_allocation -p %DB_PASSWORD% -c "SELECT \"Key\", COUNT(*) as count FROM cost_database GROUP BY \"Key\" ORDER BY count DESC;"

echo.
echo ========================================
echo Import Complete!
echo ========================================
echo.
echo Database: cost_allocation
echo User: postgres
echo Password: [your password]
echo Host: localhost
echo Port: 5432
echo.
echo Connection string:
echo postgresql://postgres:password@localhost:5432/cost_allocation
echo.
echo ========================================
echo.
echo To connect to the database:
echo   psql -U postgres -d cost_allocation
echo.
echo To run queries:
echo   psql -U postgres -d cost_allocation -c "SELECT * FROM cost_database LIMIT 10;"
echo.
echo ========================================

pause
