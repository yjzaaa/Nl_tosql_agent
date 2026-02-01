# PostgreSQL 数据导入和图形化界面 - 完成总结

## ✅ 已完成的任务

### 1. PostgreSQL 安装
- **路径**: `D:\postgres\`
- **版本**: PostgreSQL 18.1.2
- **端口**: 5432
- **数据目录**: `D:\postgres\data`
- **超级用户**: postgres
- **密码**: 123456

### 2. 数据库创建
- **数据库名**: `cost_allocation`
- **连接字符串**: `postgresql://postgres:123456@localhost:5432/cost_allocation`

### 3. 数据导入完成
- **成本数据库表**: `cost_database` (792 rows)
- **费率表**: `rate_table` (36288 rows)
- **成本中心映射表**: `cc_mapping` (255 rows)

### 4. 图形化界面配置

#### pgAdmin4
- **位置**: `D:\postgres\pgAdmin 4\runtime\pgAdmin4.exe`
- **启动脚本**: `start_pgadmin.bat`
- **默认端口**: 58125

#### Web界面
- **位置**: `postgres_web_interface.html`
- **功能**: 预设SQL查询生成和复制

## 📦 已创建的文件

| 文件名 | 用途 | 位置 |
|--------|------|------|
| `start_pgadmin.bat` | pgAdmin4启动脚本 | 项目根目录 |
| `postgres_web_interface.html` | Web查询界面 | 项目根目录 |
| `POSTGRESQL_GUI_GUIDE.md` | 图形界面使用指南 | 项目根目录 |
| `POSTGRESQL_SETUP.md` | 完整安装指南 | 项目根目录 |
| `POSTGRESQL_QUICKSTART.md` | 快速开始指南 | 项目根目录 |
| `import_to_postgres.py` | 数据导入脚本 | 项目根目录 |

## 🚀 启动图形化界面

### 方法1：使用批处理脚本（推荐）

```bash
# 双击运行
start_pgadmin.bat
```

### 方法2：直接运行可执行文件

```bash
"D:\postgres\pgAdmin 4\runtime\pgAdmin4.exe"
```

### 方法3：使用命令行

```bash
cd D:\postgres\pgAdmin 4\runtime
pgAdmin4.exe
```

## 📊 数据库统计

### 表统计

| 表名 | 行数 | 说明 |
|------|------|------|
| cost_database | 792 | 成本数据库表 |
| rate_table | 36288 | 费率表 |
| cc_mapping | 255 | 成本中心映射表 |

### 字段统计

#### cost_database表

- Year: 财年
- Scenario: 场景
- Function: 功能类型 (HR, HR Allocation, IT, IT Allocation, Procurement, Procurement Allocation)
- Cost text: 成本文本
- Key: 分摊依据 (headcount, 480055 Cycle, WCW, SAM, Win Acc, 480056 Cycle, IM, Pooling)
- Amount: 金额

#### rate_table表

- BL: 业务线 (CT, XP, MP, AT, TI, ME, D&A, CS, HRE, DTI, MI, US, UX)
- CC: 成本中心 (254个唯一值)
- Key: 分摊依据 (8种类型)
- RateNo: 分摊比例 (0.0 - 0.5906)

#### cc_mapping表

- CostCenterNumber: 成本中心编码 (254个唯一值)
- Business Line: 业务线 (15个唯一值: CT, XP, MP, AT, TI, ME, D&A, CS, HRE, DTI, MI, US, UX)

## 📝 数据库连接信息

### 连接参数

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

### 命令行连接

```bash
# 连接到PostgreSQL
D:\postgres\bin\psql.exe -U postgres -d cost_allocation -p 123456

# 连接到默认数据库
D:\postgres\postgres\bin\psql.exe -U postgres -p 123456
```

## 🎯 快速开始步骤

### 1. 启动pgAdmin
```bash
# 双击运行
start_pgadmin.bat
```

### 2. 首次配置（如果需要）

1. 浏览器会自动打开 pgAdmin（http://127.0.0.1:58125）
2. 设置 pgAdmin 主密码（记下来）
3. 点击 "Add New Server"
4. 配置连接信息：
   - Name: `PostgreSQL Local`
   - Host: `localhost`
   - Port: `5432`
   - Maintenance database: `postgres`
   - Username: `postgres`
   - **Password**: `123456`
5. 点击 "Save"
6. 输入服务器密码：`123456`

### 3. 查询数据

1. 展开 `PostgreSQL Local`
2. 展开 `Databases`
3. 展开 `cost_allocation`
4. 右键点击表，选择 `Query Tool`
5. 输入SQL查询并执行

### 4. 使用Web界面（可选）

```bash
# 在浏览器中打开
postgres_web_interface.html
```

## 📋 常用SQL查询示例

### 基础统计

```sql
-- 查看所有表
\dt

-- 查看cost_database表结构
\d cost_database

-- 查看前10条数据
SELECT * FROM cost_database LIMIT 10;
```

### 按Function分组

```sql
SELECT 
    "Function",
    COUNT(*) as row_count,
    SUM("Amount") as total_amount
FROM cost_database
GROUP BY "Function"
ORDER BY total_amount DESC;
```

### 按Key分组

```sql
SELECT 
    "Key",
    COUNT(*) as row_count,
    SUM("Amount") as total_amount
FROM cost_database
GROUP BY "Key"
ORDER BY total_amount DESC;
```

### Allocation成本查询

```sql
SELECT * FROM cost_database 
WHERE "Function" LIKE '%Allocation%'
ORDER BY "Amount"
LIMIT 20;
```

### 关联查询（成本+费率）

```sql
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
WHERE c."Function" LIKE '%Allocation%'
LIMIT 20;
```

### 按BL分摊统计

```sql
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

## 📖 文档说明

### POSTGRESQL_GUI_GUIDE.md
**pgAdmin4图形化界面使用指南**

内容：
- pgAdmin4启动方法
- 首次配置步骤
- 如何连接数据库
- 如何执行SQL查询
- 常用SQL查询示例
- Web界面使用说明

### POSTGRESQL_SETUP.md
**完整PostgreSQL安装和配置指南**

内容：
- PostgreSQL安装方法（3种）
- 数据库创建方法（3种）
- 数据导入方法（3种）
- 连接字符串格式
- 故障排除
- 安全建议
- 快速开始脚本

### POSTGRESQL_QUICKSTART.md
**快速开始指南**

内容：
- 3步快速开始流程
- 数据库连接信息
- 常用查询示例
- 故障排除

## 🔧 故障排除

### 问题1：pgAdmin无法启动

**原因**: pgAdmin可执行文件位置

**解决**:
```bash
# 使用完整路径启动
"D:\postgres\pgAdmin 4\runtime\pgAdmin4.exe"

# 或使用批处理脚本
start_pgadmin.bat
```

### 问题2：无法连接到数据库

**原因**: 密码错误或服务未运行

**解决**:
```bash
# 1. 检查PostgreSQL服务
sc query postgresql-x64-18

# 2. 如果未运行，启动服务
sc start postgresql-x64-18

# 3. 使用正确密码: 123456
```

### 问题3：浏览器无法访问pgAdmin

**原因**: pgAdmin端口被占用

**解决**:
```bash
# 检查端口占用
netstat -an | findstr "58125"

# pgAdmin会自动选择可用端口
# 查看浏览器地址栏中的实际端口
```

### 问题4：Web界面无法复制SQL

**原因**: 浏览器限制或JavaScript错误

**解决**:
- 手动选择SQL文本复制
- 或使用pgAdmin Query Tool直接输入SQL

## 📞 技术支持

### 命令行工具位置

```bash
# PostgreSQL工具
D:\postgres\bin\psql.exe
D:\postgres\bin\pg_dump.exe
D:\postgres\bin\pg_restore.exe

# pgAdmin
D:\postgres\pgAdmin 4\runtime\pgAdmin4.exe
```

### 常用命令

```bash
# 连接数据库
D:\postgres\bin\psql.exe -U postgres -d cost_allocation

# 执行SQL文件
D:\postgres\bin\psql.exe -U postgres -d cost_allocation -f query.sql

# 导出数据库
pg_dump -U postgres -d cost_allocation > backup.sql

# 导入数据库
psql -U postgres -d cost_allocation < backup.sql
```

---

**文档版本**: 1.0
**完成时间**: 2026-02-01
**状态**: ✅ 所有任务完成
**下一步**: 启动pgAdmin并开始查询数据
