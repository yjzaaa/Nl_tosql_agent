# PostgreSQL 数据查询和统计报告

## 数据库连接信息

```
Host: localhost
Port: 5432
Database: cost_allocation
User: postgres
Password: 123456
Connection string: postgresql://postgres:123456@localhost:5432/cost_allocation
```

## 数据库表结构

### 表列表

| 表名 | 行数 | 说明 |
|------|------|------|
| cost_database | 1584 | 成本数据库表 |
| rate_table | 72576 | 费率表 |
| cc_mapping | 255 | 成本中心映射表 |
| cost_text_mapping | 0 | 成本文本映射表（空） |

### cost_database表字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 主键 |
| year | character varying | 财年 |
| scenario | character varying | 场景 |
| function | character varying | 功能类型 |
| cost_text | character varying | 成本文本 |
| account | character varying | 总账科目 |
| category | character varying | 成本类型 |
| key | character varying | 分摊依据 |
| year_total | numeric | 全年总额 |
| month | character varying | 月份 |
| amount | numeric | 金额 |

### rate_table表字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 主键 |
| bl | character varying | 业务线 |
| cc | character varying | 成本中心 |
| year | character varying | 财年 |
| scenario | character varying | 场景 |
| month | character varying | 月份 |
| key | character varying | 分摊依据 |
| rate_no | numeric | 分摊比例 |

### cc_mapping表字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | integer | 主键 |
| cost_center_number | character varying | 成本中心编码 |
| business_line | character varying | 业务线 |
| created_at | timestamp without time zone | 创建时间 |

## 数据统计

### 按Function分组

| Function | 行数 | 总金额 |
|----------|------|--------|
| IT | 792 | 139,274,913.84 |
| HR | 216 | 70,191,482.78 |
| Procurement | 288 | 25,657,466.00 |
| Procurement Allocation | 144 | -25,657,465.76 |
| HR Allocation | 72 | -70,738,766.16 |
| IT Allocation | 72 | -139,274,910.98 |

**关键发现**：
- Original成本（IT, HR, Procurement）为正数
- Allocation成本为负数
- 同一Function的Original + Allocation ≈ 0

### 按Key分组

| Key | 行数 | 总金额 |
|-----|------|--------|
| WCW | 648 | 70,241,867.64 |
| headcount | 216 | 70,191,482.78 |
| SAM | 72 | 64,938,845.06 |
| Win Acc | 72 | 4,094,201.14 |
| IM | 288 | 0.24 |
| Pooling | 144 | 0.00 |
| 480055 Cycle | 72 | -70,738,766.16 |
| 480056 Cycle | 72 | -139,274,910.98 |

### 按Business Line分组

| Business Line | 成本中心数量 |
|--------------|--------------|
| CS | 57 |
| MP | 42 |
| Key Supporting Function | 35 |
| CT | 20 |
| XP | 13 |
| CS_DX | 13 |
| Central | 13 |
| MI | 12 |
| D&A | 8 |
| DX | 7 |
| AT | 7 |
| TI | 7 |
| HRE | 6 |
| ME | 5 |
| US | 3 |
| DTI | 2 |
| UX | 2 |
| CTH | 1 |
| Cyber Security | 1 |
| Dummy | 1 |

### 月度汇总

| 月份 | 行数 | 总金额 |
|------|------|--------|
| Apr | 132 | -56,194.08 |
| Aug | 132 | -71,247.96 |
| Dec | 132 | 461,649.24 |
| Feb | 132 | -77,240.40 |
| Jan | 132 | 120,089.66 |
| Jul | 132 | -104,883.08 |
| Jun | 132 | 4,605.76 |
| Mar | 132 | -55,733.16 |
| May | 132 | -38,385.86 |
| Nov | 132 | 2,987,217.24 |
| Oct | 132 | -3,720,354.36 |
| Sep | 132 | 3,196.72 |

### 费率统计

| Key | 平均费率 | 数量 |
|-----|----------|------|
| 480056 Cycle | 0.007937 | 9072 |
| Headcount | 0.007937 | 9072 |
| SAM | 0.007937 | 9072 |
| WCW | 0.007937 | 9072 |
| 480055 Cycle | 0.007937 | 9072 |
| Win Acc | 0.007937 | 9072 |
| Pooling | 0.007937 | 9072 |
| IM | 0.007937 | 9072 |

**关键发现**：
- 所有Key的平均费率都相同（0.007937）
- 每个Key在每个月都有9072个记录

### 样本数据

| Year | Month | Function | Key | Amount |
|------|-------|----------|-----|--------|
| FY24 | Feb | IT Allocation | 480056 Cycle | -3,821,291.20 |
| FY24 | Dec | IT Allocation | 480056 Cycle | -3,649,091.70 |
| FY24 | Dec | IT Allocation | 480056 Cycle | -3,649,091.70 |
| FY25 | Aug | IT Allocation | 480056 Cycle | -3,092,311.57 |
| FY25 | Aug | IT Allocation | 480056 Cycle | -3,092,311.57 |
| FY25 | Dec | IT Allocation | 480056 Cycle | -2,929,845.52 |
| FY25 | Dec | IT Allocation | 480056 Cycle | -2,929,845.52 |
| FY25 | Dec | IT Allocation | 480056 Cycle | -2,896,999.90 |
| FY26 | Sep | IT Allocation | 480056 Cycle | -2,889,699.90 |

## 正确的SQL查询

### 1. 基本查询

```sql
-- 查看所有表
\dt

-- 查看表结构
\d cost_database

-- 查看所有数据
SELECT * FROM cost_database LIMIT 10;
```

### 2. 统计查询

```sql
-- 按Function分组统计
SELECT 
    function,
    COUNT(*) as row_count,
    SUM(amount) as total_amount
FROM cost_database
GROUP BY function
ORDER BY total_amount DESC;
```

### 3. Allocation成本查询

```sql
-- 只看Allocation成本
SELECT * FROM cost_database 
WHERE function LIKE '%Allocation%'
ORDER BY amount
LIMIT 20;
```

### 4. 关联查询

```sql
-- 成本+费率关联
SELECT 
    c.year,
    c.month,
    c.function,
    c.key,
    c.amount as cost_amount,
    r.rate_no,
    ABS(c.amount) * r.rate_no as allocated_amount
FROM cost_database c
LEFT JOIN rate_table r ON 
    c.key = r.key AND 
    c.month = r.month
LIMIT 20;
```

### 5. 分摊金额计算

```sql
-- 计算分摊金额
SELECT 
    c.year,
    c.month,
    c.function,
    c.key,
    c.amount as original_amount,
    r.rate_no,
    ABS(c.amount) * r.rate_no as allocated_amount
FROM cost_database c
LEFT JOIN rate_table r ON 
    c.key = r.key AND 
    c.month = r.month
WHERE c.function LIKE '%Allocation%'
ORDER BY c.year, c.month;
```

## 使用Python查询

```python
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='cost_allocation',
    user='postgres',
    password='123456'
)

cursor = conn.cursor()

# 执行查询
cursor.execute('SELECT * FROM cost_database LIMIT 10')
for row in cursor.fetchall():
    print(row)

conn.close()
```

## 使用命令行连接

```bash
# 连接到数据库
D:\postgres\bin\psql.exe -U postgres -d cost_allocation

# 执行查询
SELECT * FROM cost_database LIMIT 10;

# 退出
\q
```

## 文件清单

| 文件名 | 说明 |
|--------|------|
| `query_postgres.py` | Python查询脚本 |
| `CORRECT_SQL_QUERIES.md` | 正确的SQL查询示例 |

---

**报告生成时间**: 2026-02-01
**数据状态**: ✅ 已成功导入并查询
**下一步**: 使用pgAdmin或命令行进一步分析数据
