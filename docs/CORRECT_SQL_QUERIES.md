# PostgreSQL 正确查询示例

## 表名说明

所有表名都是**小写**的，查询时请使用小写表名。

- `cost_database` - 成本数据库表
- `rate_table` - 费率表
- `cc_mapping` - 成本中心映射表
- `cost_text_mapping` - 成本文本映射表

## 正确的查询语法

### 1. 数据统计查询

```sql
-- 查看所有表的数据量
SELECT 
    'Total Cost Rows' as statistic, 
    (SELECT COUNT(*) FROM cost_database) as value
UNION ALL
SELECT 
    'Total Rate Rows' as statistic,
    (SELECT COUNT(*) FROM rate_table) as value
UNION ALL
SELECT 
    'Total CC Mappings' as statistic,
    (SELECT COUNT(*) FROM cc_mapping) as value;
```

### 2. 查看所有表

```sql
\dt

-- 或使用标准SQL
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename;
```

### 3. 查看表结构

```sql
\d cost_database

-- 或使用标准SQL
SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name = 'cost_database' 
ORDER BY ordinal_position;
```

### 4. 按Function分组统计

```sql
SELECT 
    function,
    COUNT(*) as row_count,
    SUM(amount) as total_amount,
    ROUND(AVG(amount), 2) as avg_amount
FROM cost_database
GROUP BY function
ORDER BY total_amount DESC;
```

### 5. 按Key分组统计

```sql
SELECT 
    key,
    COUNT(*) as row_count,
    SUM(amount) as total_amount,
    ROUND(AVG(amount), 2) as avg_amount
FROM cost_database
GROUP BY key
ORDER BY total_amount DESC;
```

### 6. 查看所有成本数据

```sql
SELECT * FROM cost_database 
ORDER BY ABS(amount) DESC 
LIMIT 10;
```

### 7. 查看Allocation成本

```sql
SELECT * FROM cost_database 
WHERE function LIKE '%Allocation%'
ORDER BY amount
LIMIT 20;
```

### 8. 查看Original成本

```sql
SELECT * FROM cost_database 
WHERE function NOT LIKE '%Allocation%'
ORDER BY amount DESC
LIMIT 20;
```

### 9. 按月度汇总

```sql
SELECT 
    month,
    SUM(amount) as total_amount,
    COUNT(*) as record_count
FROM cost_database
GROUP BY month
ORDER BY month;
```

### 10. 查看所有费率

```sql
SELECT * FROM rate_table 
ORDER BY rate_no DESC 
LIMIT 10;
```

### 11. 费率汇总

```sql
SELECT 
    key,
    AVG(rate_no) as avg_rate,
    MIN(rate_no) as min_rate,
    MAX(rate_no) as max_rate,
    COUNT(*) as count
FROM rate_table
GROUP BY key
ORDER BY avg_rate DESC;
```

### 12. 按CC查询费率

```sql
SELECT 
    cc,
    key,
    AVG(rate_no) as avg_rate,
    COUNT(*) as month_count
FROM rate_table
GROUP BY cc, key
ORDER BY cc, key
LIMIT 50;
```

### 13. 按BL查询费率

```sql
SELECT 
    bl,
    key,
    AVG(rate_no) as avg_rate,
    COUNT(*) as count
FROM rate_table
GROUP BY bl, key
ORDER BY bl, key
LIMIT 50;
```

### 14. 查看所有成本中心映射

```sql
SELECT 
    cost_center_number,
    business_line
FROM cc_mapping
ORDER BY business_line, cost_center_number;
```

### 15. 按BL列出所有CC

```sql
SELECT 
    business_line,
    STRING_AGG(cost_center_number, ', ' ORDER BY cost_center_number) as cost_centers
FROM cc_mapping
GROUP BY business_line
ORDER BY business_line;
```

### 16. 成本+费率关联查询

```sql
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
LIMIT 50;
```

### 17. 分摊金额计算

```sql
SELECT 
    c.year,
    c.month,
    c.function,
    c.key,
    c.amount as original_amount,
    r.rate_no,
    ABS(c.amount) * r.rate_no as allocated_amount,
    ROUND(ABS(c.amount) * r.rate_no, 2) as allocated_rounded
FROM cost_database c
LEFT JOIN rate_table r ON 
    c.key = r.key AND 
    c.month = r.month
WHERE c.function LIKE '%Allocation%'
ORDER BY c.year, c.month;
```

### 18. 月度分摊统计

```sql
SELECT 
    c.year,
    c.month,
    c.function,
    SUM(ABS(c.amount) * r.rate_no) as total_allocated
FROM cost_database c
LEFT JOIN rate_table r ON 
    c.key = r.key AND 
    c.month = r.month
WHERE c.function LIKE '%Allocation%'
GROUP BY c.year, c.month, c.function
ORDER BY c.year, c.month;
```

### 19. 按BL分摊总额

```sql
SELECT 
    r.bl,
    c.key,
    SUM(ABS(c.amount) * r.rate_no) as total_allocated
FROM cost_database c
LEFT JOIN rate_table r ON 
    c.key = r.key AND 
    c.month = r.month
WHERE c.function LIKE '%Allocation%'
GROUP BY r.bl, c.key
ORDER BY r.bl, c.key;
```

## 重要提示

### 1. 表名大小写

PostgreSQL在某些情况下对表名是大小写敏感的，除非使用了双引号。

- **推荐**：始终使用小写表名
- **列名**：同样推荐使用小写
- **字符串值**：如果列名有大小写混合，可能需要使用双引号

### 2. 数据库连接

```bash
# 连接到数据库
D:\postgres\bin\psql.exe -U postgres -d cost_allocation

# 如果需要密码
set PGPASSWORD=123456
D:\postgres\bin\psql.exe -U postgres -d cost_allocation
```

### 3. 批量执行SQL

```bash
# 将SQL保存为文件
echo "SELECT COUNT(*) FROM cost_database;" > test_query.sql

# 执行SQL文件
D:\postgres\bin\psql.exe -U postgres -d cost_allocation -f test_query.sql
```

### 4. 导出查询结果

```bash
# 导出为CSV
D:\postgres\bin\psql.exe -U postgres -d cost_allocation -c "COPY (SELECT * FROM cost_database LIMIT 10) TO STDOUT WITH CSV HEADER" > output.csv

# 或使用\o命令
D:\postgres\bin\psql.exe -U postgres -d cost_allocation -c "\t" -o output.txt
SELECT * FROM cost_database LIMIT 10;
```

## 常用错误和解决方法

### 错误1: relation does not exist

**错误信息**：
```
ERROR: relation "cost_database" does not exist
```

**原因**：使用了错误的表名（如大写）或连接到错误的数据库

**解决方法**：
```sql
-- 使用小写表名
SELECT * FROM cost_database;

-- 确认连接的数据库正确
\c cost_allocation
```

### 错误2: column does not exist

**错误信息**：
```
ERROR: column "Function" does not exist
```

**原因**：列名大小写错误或使用了双引号但列名不匹配

**解决方法**：
```sql
-- 使用小写列名
SELECT function FROM cost_database;

-- 或查看正确的列名
\d cost_database
```

### 错误3: syntax error

**错误信息**：
```
ERROR: syntax error at or near "SELECT"
```

**原因**：SQL语句格式错误，可能是复制粘贴时引入的格式问题

**解决方法**：
- 重新输入SQL语句
- 确保没有多余的引号或符号
- 使用标准的SQL格式

## 快速测试

### 测试1：基本连接

```sql
-- 连接测试
SELECT version();
```

### 测试2：表列表

```sql
-- 查看所有表
\dt
```

### 测试3：简单查询

```sql
-- 简单计数
SELECT COUNT(*) FROM cost_database;
```

### 测试4：数据预览

```sql
-- 查看前5条
SELECT * FROM cost_database LIMIT 5;
```

---

**最后更新**: 2026-02-01
**表名**: cost_database, rate_table, cc_mapping, cost_text_mapping
**连接**: postgresql://postgres:123456@localhost:5432/cost_allocation
