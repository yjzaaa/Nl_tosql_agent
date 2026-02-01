# PostgreSQL 安装和数据导入指南

## 状态检查

✅ **已完成**:
- PostgreSQL驱动（psycopg2-binary）已安装
- SQLAlchemy已安装
- 导入脚本（import_to_postgres.py）已创建
- Windows批处理脚本（install_postgres_and_import.bat）已创建
- 详细安装指南（POSTGRESQL_SETUP.md）已创建

❌ **需要完成**:
- 安装PostgreSQL服务器
- 创建数据库
- 导入Excel数据

## 快速开始（3步骤）

### 步骤1：安装PostgreSQL

#### 选项A：使用官方安装程序（推荐）

1. 下载PostgreSQL
   - 访问：https://www.postgresql.org/download/windows/
   - 点击"Download the installer"
   - 下载Windows x86-64版本

2. 安装PostgreSQL
   - 双击运行安装程序
   - 接受默认设置
   - 设置超级用户密码（重要：请记住此密码！）
   - 完成安装

3. 验证安装
   ```bash
   # 在命令行中运行
   psql --version
   ```

#### 选项B：使用Docker（推荐用于开发）

1. 安装Docker Desktop
   - 访问：https://www.docker.com/products/docker-desktop
   - 下载并安装Docker Desktop
   - 启动Docker Desktop

2. 运行PostgreSQL容器
   ```bash
   docker run --name postgres-cost-allocation ^
     -e POSTGRES_PASSWORD=cost2024 ^
     -e POSTGRES_DB=cost_allocation ^
     -p 5432:5432 ^
     -d postgres:16
   ```

3. 验证运行
   ```bash
   docker ps
   ```

### 步骤2：创建数据库

#### 使用pgAdmin（图形界面）

1. 启动pgAdmin（与PostgreSQL一起安装）
2. 连接到PostgreSQL服务器
3. 右键点击"Databases"
4. 选择"Create" > "Database"
5. 输入数据库名：`cost_allocation`
6. 点击"Save"

#### 使用命令行

```bash
# 连接到PostgreSQL
psql -U postgres

# 创建数据库
CREATE DATABASE cost_allocation;

# 退出
\q
```

### 步骤3：导入Excel数据

#### 方法1：使用批处理脚本（最简单）

```bash
# 双击运行
install_postgres_and_import.bat
```

#### 方法2：使用Python脚本

```bash
# 激活虚拟环境
cd "D:\AI_Python\Excel\ExcelMind-main (1)\ExcelMind-main"
.venv\Scripts\activate

# 运行导入脚本
python import_to_postgres.py --excel "D:\AI_Python\AI2\AI2\back_end_code\Data\Function cost allocation analysis to IT 20260104.xlsx" --db "postgresql://postgres:your_password@localhost:5432/cost_allocation"
```

#### 方法3：手动导入

```python
import pandas as pd
from sqlalchemy import create_engine

# 连接数据库
engine = create_engine("postgresql://postgres:your_password@localhost:5432/cost_allocation")

# 读取Excel并导入
excel_path = "D:\\AI_Python\\AI2\\AI2\\back_end_code\\Data\\Function cost allocation analysis to IT 20260104.xlsx"

# 导入成本数据库表
cost_df = pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_CostDataBase")
cost_df.to_sql("cost_database", engine, if_exists="replace", index=False)

# 导入费率表
rate_df = pd.read_excel(excel_path, sheet_name="SSME_FI_InsightBot_Rate")
rate_df.to_sql("rate_table", engine, if_exists="replace", index=False)

# 导入成本中心映射
cc_df = pd.read_excel(excel_path, sheet_name="CC Mapping")
cc_df.to_sql("cc_mapping", engine, if_exists="replace", index=False)

print("导入完成！")
```

## 数据库表结构

导入后将创建以下4个表：

### 1. cost_database（成本数据库表）
```sql
CREATE TABLE cost_database (
    id SERIAL PRIMARY KEY,
    year VARCHAR(10),
    scenario VARCHAR(50),
    function VARCHAR(100),
    cost_text VARCHAR(500),
    account VARCHAR(200),
    category VARCHAR(200),
    key VARCHAR(100),
    year_total NUMERIC(18,2),
    month VARCHAR(20),
    amount NUMERIC(18,2)
);
```

### 2. rate_table（费率表）
```sql
CREATE TABLE rate_table (
    id SERIAL PRIMARY KEY,
    bl VARCHAR(100),
    cc VARCHAR(50),
    year VARCHAR(10),
    scenario VARCHAR(50),
    month VARCHAR(20),
    key VARCHAR(100),
    rate_no NUMERIC(10,6)
);
```

### 3. cc_mapping（成本中心映射表）
```sql
CREATE TABLE cc_mapping (
    id SERIAL PRIMARY KEY,
    cost_center_number VARCHAR(50) UNIQUE,
    business_line VARCHAR(100)
);
```

### 4. cost_text_mapping（成本文本映射表）
```sql
CREATE TABLE cost_text_mapping (
    id SERIAL PRIMARY KEY,
    cost_text VARCHAR(500) UNIQUE,
    function VARCHAR(100)
);
```

## 连接字符串

```
postgresql://postgres:password@localhost:5432/cost_allocation
```

替换：
- `password`：你的PostgreSQL密码
- `localhost`：数据库服务器地址
- `5432`：端口号（如果不同）
- `cost_allocation`：数据库名

## 常用查询示例

### 查看所有Function
```sql
SELECT DISTINCT "Function" FROM cost_database ORDER BY "Function";
```

### 查看所有Key
```sql
SELECT DISTINCT "Key" FROM cost_database ORDER BY "Key";
```

### 按Function统计
```sql
SELECT 
    "Function",
    COUNT(*) as row_count,
    SUM("Amount") as total_amount
FROM cost_database
GROUP BY "Function"
ORDER BY total_amount DESC;
```

### 查看Allocation成本
```sql
SELECT * FROM cost_database 
WHERE "Function" LIKE '%Allocation%'
ORDER BY "Amount";
```

### 关联查询（成本+费率）
```sql
SELECT 
    c."Year",
    c."Month",
    c."Function",
    c."Amount" as cost_amount,
    r.rate_no,
    c."Amount" * r.rate_no as allocation_amount
FROM cost_database c
LEFT JOIN rate_table r ON 
    c."Key" = r."Key" AND 
    c."Month" = r."Month"
WHERE c."Function" LIKE '%Allocation%'
LIMIT 10;
```

## 故障排除

### 问题1：PostgreSQL未找到

**错误信息**：`'psql' is not recognized`

**解决方法**：
1. 安装PostgreSQL：https://www.postgresql.org/download/windows/
2. 或将PostgreSQL的bin目录添加到PATH环境变量
3. 默认位置：`C:\Program Files\PostgreSQL\16\bin`

### 问题2：连接被拒绝

**错误信息**：`could not connect to server: Connection refused`

**解决方法**：
1. 检查PostgreSQL服务是否运行
   - Windows服务：查看"Services.msc"
   - 找到"postgresql-x64-16"服务
   - 确保状态为"Running"
2. 检查端口是否正确（默认5432）
3. 检查防火墙设置

### 问题3：密码认证失败

**错误信息**：`password authentication failed`

**解决方法**：
1. 确认密码正确（区分大小写）
2. 确认用户名正确（通常是postgres）
3. 尝试使用localhost而不是IP地址

### 问题4：数据库不存在

**错误信息**：`database "cost_allocation" does not exist`

**解决方法**：
1. 创建数据库：`CREATE DATABASE cost_allocation;`
2. 或者在连接字符串中使用默认数据库：`.../postgres`

## 下一步

1. **完成PostgreSQL安装**
   - 下载并安装PostgreSQL
   - 设置密码并启动服务

2. **运行导入脚本**
   - 使用批处理脚本或Python脚本导入数据

3. **验证导入**
   - 运行查询验证数据正确性

4. **开始使用**
   - 使用提供的查询示例
   - 开发自定义查询
   - 集成到应用程序中

## 文件清单

已创建的文件：
- `import_to_postgres.py` - Python导入脚本
- `install_postgres_and_import.bat` - Windows批处理脚本
- `POSTGRESQL_SETUP.md` - 详细安装和配置指南
- `POSTGRESQL_QUICKSTART.md` - 本快速开始指南

---

**最后更新**：2026-02-01
**状态**：等待PostgreSQL安装完成
**下一步**：安装PostgreSQL并运行导入脚本
