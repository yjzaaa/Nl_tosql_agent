# PostgreSQL 图形化界面使用指南

## 一、pgAdmin4 图形化工具

### 启动方式

#### 方法1：使用批处理脚本（推荐）

```bash
# 双击运行
start_pgadmin.bat
```

#### 方法2：直接运行可执行文件

```bash
# 在命令行中运行
"D:\postgres\pgAdmin 4\runtime\pgAdmin4.exe"
```

### 首次配置

1. **启动pgAdmin4**后，浏览器会自动打开`http://127.0.0.1:58125`

2. **设置主密码**
   - 在首次启动时，设置pgAdmin主密码
   - 记住此密码，下次启动时需要

3. **连接到PostgreSQL服务器**
   - 点击"Add New Server"
   - General页面：
     - Name: `PostgreSQL Local`
     - Host: `localhost`
     - Port: `5432`
     - Maintenance database: `postgres`
     - Username: `postgres`
     - Password: `123456`
   - 点击"Save"

4. **展开服务器树**
   - 点击服务器名称（PostgreSQL Local）
   - 输入服务器密码：`123456`
   - 展开`Databases`
   - 展开`cost_allocation`

### 使用pgAdmin查询数据

1. **打开Query Tool**
   - 右键点击`cost_allocation`数据库
   - 选择`Query Tool`

2. **执行SQL查询**
   - 在SQL编辑器中输入SQL语句
   - 点击`Execute`（F5）或闪电图标

3. **常用SQL查询**

```sql
-- 查看所有表
\dt

-- 查看cost_database表结构
\d cost_database

-- 查看cost_database表数据
SELECT * FROM cost_database LIMIT 10;

-- 按Function分组统计
SELECT "Function", COUNT(*) as count, SUM("Amount") as total
FROM cost_database
GROUP BY "Function"
ORDER BY total DESC;

-- 按Key分组统计
SELECT "Key", COUNT(*) as count, SUM("Amount") as total
FROM cost_database
GROUP BY "Key"
ORDER BY total DESC;

-- 查看Allocation成本
SELECT * FROM cost_database
WHERE "Function" LIKE '%Allocation%'
ORDER BY "Amount";

-- 关联查询（成本+费率）
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
LIMIT 20;
```

## 二、Web界面查询工具

### 启动Web界面

```bash
# 双击打开HTML文件
postgres_web_interface.html
```

### Web界面功能

1. **预设SQL查询**
   - 数据统计
   - 成本数据查询
   - 费率数据查询
   - 映射关系查询
   - 关联查询

2. **自定义SQL查询**
   - 在文本框中输入自定义SQL
   - 点击"执行自定义查询"按钮

3. **功能说明**
   - 所有查询会生成标准SQL语句
   - 可复制SQL到pgAdmin或命令行中执行
   - 界面友好，适合快速查询

### 使用步骤

1. **打开Web界面**
   ```bash
   # 直接在浏览器中打开HTML文件
   file:///D:/AI_Python/Excel/ExcelMind-main%20(1)/ExcelMind-main/postgres_web_interface.html
   ```

2. **选择查询类型**
   - 点击相应的功能按钮
   - 系统会生成对应的SQL语句

3. **复制SQL到pgAdmin**
   - 点击"复制结果"按钮
   - 在pgAdmin的Query Tool中粘贴并执行

4. **或在命令行中执行**
   - 将SQL保存为.sql文件
   - 使用`psql`命令执行

## 三、常用SQL查询汇总

### 数据统计类

```sql
-- 查看所有表的数据量
SELECT 
    'cost_database' as table_name, 
    (SELECT COUNT(*) FROM cost_database) as row_count
UNION ALL
SELECT 'rate_table', (SELECT COUNT(*) FROM rate_table)
UNION ALL
SELECT 'cc_mapping', (SELECT COUNT(*) FROM cc_mapping);

-- 按Function分组统计
SELECT 
    "Function",
    COUNT(*) as row_count,
    SUM("Amount") as total_amount,
    AVG("Amount") as avg_amount
FROM cost_database
GROUP BY "Function"
ORDER BY total_amount DESC;

-- 按Key分组统计
SELECT 
    "Key",
    COUNT(*) as row_count,
    SUM("Amount") as total_amount,
    AVG("Amount") as avg_amount
FROM cost_database
GROUP BY "Key"
ORDER BY total_amount DESC;
```

### 成本数据查询类

```sql
-- 查看所有成本数据
SELECT * FROM cost_database 
ORDER BY ABS("Amount") DESC 
LIMIT 20;

-- 只看Allocation成本
SELECT * FROM cost_database 
WHERE "Function" LIKE '%Allocation%'
ORDER BY "Amount"
LIMIT 20;

-- 只看Original成本
SELECT * FROM cost_database 
WHERE "Function" NOT LIKE '%Allocation%'
ORDER BY "Amount" DESC
LIMIT 20;

-- 按月度汇总
SELECT 
    "Month",
    SUM("Amount") as total_amount,
    COUNT(*) as record_count
FROM cost_database
GROUP BY "Month"
ORDER BY "Month";
```

### 费率数据查询类

```sql
-- 查看所有费率
SELECT * FROM rate_table 
ORDER BY "rate_no" DESC 
LIMIT 20;

-- 费率汇总
SELECT 
    "Key",
    AVG("rate_no") as avg_rate,
    MIN("rate_no") as min_rate,
    MAX("rate_no") as max_rate,
    COUNT(*) as count
FROM rate_table
GROUP BY "Key"
ORDER BY avg_rate DESC;

-- 按CC查询费率
SELECT 
    cc,
    "Key",
    AVG("rate_no") as avg_rate,
    COUNT(*) as month_count
FROM rate_table
GROUP BY cc, "Key"
ORDER BY cc, "Key"
LIMIT 50;
```

### 映射关系查询类

```sql
-- 所有成本中心映射
SELECT 
    cost_center_number,
    business_line
FROM cc_mapping
ORDER BY business_line, cost_center_number;

-- 按BL列出所有CC
SELECT 
    business_line,
    STRING_AGG(cost_center_number, ', ' ORDER BY cost_center_number) as cost_centers
FROM cc_mapping
GROUP BY business_line
ORDER BY business_line;
```

### 关联查询类

```sql
-- 成本+费率关联
SELECT 
    c."Year",
    c."Month",
    c."Function",
    c."Key",
    c."Amount" as cost_amount,
    r.rate_no,
    ABS(c."Amount") * r.rate_no as allocated_amount
FROM cost_database c
LEFT JOIN rate_table r ON 
    c."Key" = r."Key" AND 
    c."Month" = r."Month"
LIMIT 50;

-- 分摊金额计算
SELECT 
    c."Year",
    c."Month",
    c."Function",
    c."Key",
    c."Amount" as original_amount,
    r.rate_no,
    ABS(c."Amount") * r.rate_no as allocated_amount,
    ROUND(ABS(c."Amount") * r.rate_no, 2) as allocated_rounded
FROM cost_database c
LEFT JOIN rate_table r ON 
    c."Key" = r."Key" AND 
    c."Month" = r."Month"
WHERE c."Function" LIKE '%Allocation%'
ORDER BY c."Year", c."Month";

-- 月度分摊统计
SELECT 
    c."Year",
    c."Month",
    c."Function",
    SUM(ABS(c."Amount") * r.rate_no) as total_allocated
FROM cost_database c
LEFT JOIN rate_table r ON 
    c."Key" = r."Key" AND 
    c."Month" = r."Month"
WHERE c."Function" LIKE '%Allocation%'
GROUP BY c."Year", c."Month", c."Function"
ORDER BY c."Year", c."Month";

-- 按BL分摊总额
SELECT 
    r.bl,
    c."Key",
    SUM(ABS(c."Amount") * r.rate_no) as total_allocated
FROM cost_database c
LEFT JOIN rate_table r ON 
    c."Key" = r."Key" AND 
    c."Month" = r."Month"
WHERE c."Function" LIKE '%Allocation%'
GROUP BY r.bl, c."Key"
ORDER BY r.bl, c."Key";
```

## 四、命令行连接方式

### 连接到数据库

```bash
# 连接到默认数据库
D:\postgres\bin\psql.exe -U postgres

# 连接到cost_allocation数据库
D:\postgres\bin\psql.exe -U postgres -d cost_allocation

# 使用密码连接
set PGPASSWORD=123456
D:\postgres\bin\psql.exe -U postgres -d cost_allocation

# 远程连接
psql -h host -p 5432 -U user -d database
```

### 常用psql命令

```sql
-- 列出所有表
\dt

-- 列出表结构
\d cost_database
\d rate_table
\d cc_mapping

-- 退出
\q

-- 执行SQL文件
\i query.sql

-- 导出查询结果到CSV
\o output.csv
\p tuple
SELECT * FROM cost_database;
\o

-- 显示查询执行时间
\timing on
```

## 五、文件清单

### 已创建的文件

1. **start_pgadmin.bat** - pgAdmin4启动脚本
2. **postgres_web_interface.html** - Web界面查询工具

### 数据库配置信息

```
Host: localhost
Port: 5432
Database: cost_allocation
User: postgres
Password: 123456
```

### 连接字符串

```
postgresql://postgres:123456@localhost:5432/cost_allocation
```

## 六、快速开始

### 1. 启动pgAdmin

```bash
# 双击运行
start_pgadmin.bat
```

### 2. 连接到数据库

- 浏览器会自动打开pgAdmin界面
- 输入主密码（首次启动时设置）
- 添加服务器连接到`localhost:5432`
- 用户名：`postgres`
- 密码：`123456`

### 3. 查询数据

- 展开`cost_allocation`数据库
- 右键点击表，选择`Query Tool`
- 输入SQL查询并执行

### 4. 使用Web界面（可选）

```bash
# 在浏览器中打开
postgres_web_interface.html
```

---

**文档版本**: 1.0
**最后更新**: 2026-02-01
