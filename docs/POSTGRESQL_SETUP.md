# PostgreSQL 安装和配置指南

## 一、安装PostgreSQL

### Windows环境

#### 方法1：使用PostgreSQL官方安装包（推荐）

1. **下载PostgreSQL**
   - 访问：https://www.postgresql.org/download/windows/
   - 下载最新版本的PostgreSQL安装包（例如PostgreSQL 16.x）
   - 文件名类似：`postgresql-16.x-x-windows-x64.exe`

2. **安装步骤**
   ```
   1. 双击运行安装程序
   2. 选择安装目录（默认：C:\Program Files\PostgreSQL\16）
   3. 设置数据目录（默认：C:\Program Files\PostgreSQL\16\data）
   4. 设置超级用户密码（重要：请记住此密码！）
   5. 端口：默认5432
   6. 选择安装组件：全部选中
   7. 完成安装
   ```

3. **验证安装**
   ```bash
   # 在命令行中输入
   psql --version
   ```

#### 方法2：使用Docker（推荐用于开发环境）

1. **安装Docker Desktop**
   - 下载：https://www.docker.com/products/docker-desktop
   - 安装并启动Docker Desktop

2. **运行PostgreSQL容器**
   ```bash
   docker run --name postgres-cost-allocation \
     -e POSTGRES_PASSWORD=cost2024 \
     -e POSTGRES_DB=cost_allocation \
     -p 5432:5432 \
     -d postgres:16
   ```

3. **验证运行**
   ```bash
   docker ps
   ```

#### 方法3：使用PostgreSQL安装脚本

1. **下载并安装**
   ```bash
   # 使用chocolatey（如果已安装）
   choco install postgresql

   # 或使用winget（Windows 10/11自带）
   winget install PostgreSQL.PostgreSQL
   ```

2. **初始化数据库**
   ```bash
   # 初始化数据库集群
   initdb -D "C:\Program Files\PostgreSQL\16\data" -U postgres
   ```

## 二、创建数据库

### 方法1：使用pgAdmin（推荐）

1. **启动pgAdmin**
   - 安装PostgreSQL时会自动安装pgAdmin
   - 从开始菜单启动pgAdmin

2. **创建数据库**
   ```
   1. 右键点击"Databases"
   2. 选择"Create" > "Database"
   3. 输入数据库名：cost_allocation
   4. 点击"Save"
   ```

### 方法2：使用命令行

```bash
# 连接到PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE cost_allocation;

# 退出
\q
```

### 方法3：使用Python脚本

```python
import psycopg2
from psycopg2 import sql

# 连接到PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="postgres",
    user="postgres",
    password="your_password"
)

conn.autocommit = True
cursor = conn.cursor()

# 创建数据库
cursor.execute("CREATE DATABASE cost_allocation")

print("Database created successfully!")
conn.close()
```

## 三、连接字符串格式

### PostgreSQL连接字符串格式

```
postgresql://user:password@host:port/database
```

### 示例

```bash
# 本地PostgreSQL
postgresql://postgres:cost2024@localhost:5432/cost_allocation

# Docker PostgreSQL
postgresql://postgres:cost2024@localhost:5432/cost_allocation

# 远程服务器
postgresql://user:password@server.example.com:5432/cost_allocation
```

## 四、导入数据到PostgreSQL

### 方法1：使用导入脚本（推荐）

```bash
# 激活虚拟环境
cd "D:\AI_Python\Excel\ExcelMind-main (1)\ExcelMind-main"
.venv\Scripts\activate

# 运行导入脚本
python import_to_postgres.py \
   --excel "D:\AI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx" \
   --db "postgresql://postgres:cost2024@localhost:5432/cost_allocation"
```

### 方法2：使用Python代码

```python
import pandas as pd
from sqlalchemy import create_engine

# 读取Excel
excel_path = "D:\\AI_Python\\AI2\\AI2\\back_end_code\\Data\\Function cost allocation analysis to IT 20260104.xlsx"

# 连接PostgreSQL
engine = create_engine("postgresql://postgres:cost2024@localhost:5432/cost_allocation")

# 导入成本数据库表
cost_df = pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_CostDataBase")
cost_df.to_sql("cost_database", engine, if_exists="append", index=False)

# 导入费率表
rate_df = pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_Rate")
rate_df.to_sql("rate_table", engine, if_exists="append", index=False)

# 导入成本中心映射表
cc_df = pd.read_excel(excel_path, sheet_name="CC Mapping")
cc_df.to_sql("cc_mapping", engine, if_exists="append", index=False)

print("Data imported successfully!")
```

### 方法3：使用psql命令行

```bash
# 导入CSV文件（如果先将Excel转换为CSV）
psql -U postgres -d cost_allocation -c "\COPY cost_database FROM 'cost_database.csv' DELIMITER ',' CSV HEADER"
```

## 五、验证导入

### 查看导入的数据

```bash
# 连接到数据库
psql -U postgres -d cost_allocation

# 查看表
\dt

# 查看成本数据库表数据
SELECT COUNT(*) FROM cost_database;

# 查看前10行
SELECT * FROM cost_database LIMIT 10;

# 按Function分组统计
SELECT "Function", COUNT(*) 
FROM cost_database 
GROUP BY "Function";

# 退出
\q
```

### 使用Python查询数据

```python
import pandas as pd
from sqlalchemy import create_engine, text

# 连接数据库
engine = create_engine("postgresql://postgres:cost2024@localhost:5432/cost_allocation")

# 查询数据
with engine.connect() as conn:
    # 查看表结构
    result = conn.execute(text("SELECT * FROM cost_database LIMIT 10"))
    df = pd.DataFrame(result.fetchall(), columns=result.keys())
    print(df)
    
    # 查看统计信息
    result = conn.execute(text("""
        SELECT "Function", COUNT(*) as count, SUM("Amount") as total
        FROM cost_database 
        GROUP BY "Function"
    """))
    stats = pd.DataFrame(result.fetchall(), columns=result.keys())
    print("\nStatistics:")
    print(stats)
```

## 六、常用SQL查询

### 按Function统计
```sql
SELECT "Function", 
       COUNT(*) as row_count, 
       SUM("Amount") as total_amount,
       AVG("Amount") as avg_amount
FROM cost_database
GROUP BY "Function"
ORDER BY total_amount DESC;
```

### 按Key统计
```sql
SELECT "Key",
       COUNT(*) as row_count,
       SUM("Amount") as total_amount
FROM cost_database
GROUP BY "Key"
ORDER BY total_amount DESC;
```

### 查看Allocation成本
```sql
SELECT *
FROM cost_database
WHERE "Function" LIKE '%Allocation%'
ORDER BY "Amount";
```

### 关联查询（成本+费率）
```sql
SELECT 
    c."Year",
    c."Month",
    c."Function",
    c."Amount",
    r.rate_no,
    c."Amount" * r.rate_no as allocation_amount
FROM cost_database c
LEFT JOIN rate_table r ON 
    c."Key" = r."Key" AND 
    c."Month" = r."Month"
WHERE c."Function" LIKE '%Allocation%'
LIMIT 100;
```

## 七、故障排除

### 问题1：连接失败
```
错误：connection refused
解决：
1. 检查PostgreSQL服务是否运行
2. 检查端口是否正确（默认5432）
3. 检查防火墙设置
```

### 问题2：认证失败
```
错误：password authentication failed
解决：
1. 检查用户名和密码是否正确
2. 检查pg_hba.conf配置
3. 尝试使用localhost而不是IP地址
```

### 问题3：数据库不存在
```
错误：database "cost_allocation" does not exist
解决：
1. 先创建数据库：CREATE DATABASE cost_allocation;
2. 或者在连接字符串中使用默认数据库postgres
```

### 问题4：编码问题
```
错误：character encoding issue
解决：
1. 在连接字符串中添加编码：postgresql://.../cost_allocation?client_encoding=utf8
2. 或在CREATE DATABASE时指定编码：CREATE DATABASE cost_allocation ENCODING 'UTF8';
```

## 八、安全建议

### 生产环境配置

1. **修改默认密码**
   ```bash
   psql -U postgres
   ALTER USER postgres WITH PASSWORD 'your_strong_password';
   ```

2. **限制远程访问**
   - 编辑 `postgresql.conf`
   - 设置 `listen_addresses = 'localhost'`
   - 或使用防火墙限制访问

3. **使用SSL连接**
   ```
   postgresql://user:password@host:port/database?sslmode=require
   ```

4. **定期备份**
   ```bash
   pg_dump -U postgres cost_allocation > backup.sql
   ```

## 九、快速开始脚本

### 自动化安装和导入脚本

```bash
#!/bin/bash
# install_and_import.sh

echo "=== PostgreSQL Installation and Import Script ==="

# 1. 检查PostgreSQL是否已安装
if command -v psql &> /dev/null
then
    echo "✅ PostgreSQL is already installed"
else
    echo "❌ PostgreSQL not found. Please install PostgreSQL first."
    exit 1
fi

# 2. 创建数据库
echo "Creating database..."
psql -U postgres -c "CREATE DATABASE cost_allocation;"

# 3. 导入数据
echo "Importing data..."
python import_to_postgres.py \
   --excel "D:\AI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx" \
   --db "postgresql://postgres:cost2024@localhost:5432/cost_allocation"

# 4. 验证导入
echo "Verifying import..."
psql -U postgres -d cost_allocation -c "SELECT COUNT(*) FROM cost_database;"

echo "=== Installation and Import Complete ==="
```

## 十、推荐配置

### 开发环境配置

```
Host: localhost
Port: 5432
Database: cost_allocation
User: postgres
Password: cost2024
```

### 测试环境配置

```
Host: test-server.example.com
Port: 5432
Database: cost_allocation_test
User: test_user
Password: [strong_password]
```

### 生产环境配置

```
Host: prod-server.example.com
Port: 5432
Database: cost_allocation_prod
User: app_user
Password: [very_strong_password]
SSL: required
```

---

**文档版本**: 1.0
**最后更新**: 2026-02-01
**适用版本**: PostgreSQL 14+
