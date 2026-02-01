# 分摊计算 SQL 示例

> 适用：基于 v2.0 业务逻辑的分摊计算。

## Q1: 计算 FY25 Actual 场景下，IT Allocation 分摊给 CT 业务线的费用

**业务逻辑解析**：
1.  **数据源**：`cost_database` (c) 和 `rate_table` (r)。
2.  **筛选条件**：
    *   c.year = 'FY25'
    *   c.scenario = 'Actual'
    *   c.function = 'IT Allocation'
    *   r.bl = 'CT'
3.  **连接条件**：year, scenario, month, key。
4.  **计算**：SUM(ABS(c.amount) * r.rate_no)。

**SQL 模板**：

```sql
SELECT 
    SUM(ABS(c.amount) * r.rate_no) as Total_Allocated_Cost
FROM cost_database c
JOIN rate_table r 
    ON c.year = r.year 
    AND c.scenario = r.scenario 
    AND c.month = r.month 
    AND c.key = r.key
WHERE 
    c.year = 'FY25' 
    AND c.scenario = 'Actual'
    AND c.function = 'IT Allocation'
    AND r.bl = 'CT';
```

## Q2: 计算 FY26 Budget1 下，分摊给 CC '413001' 的 HR 费用

**业务逻辑解析**：
1.  **Function**: HR Allocation (注意：通常分摊的是 Allocation 类型的科目)。
2.  **Key**: 根据业务规则，HR Allocation 对应 Key '480055 Cycle' (也可以通过 JOIN 自动匹配)。
3.  **Target**: r.cc = '413001'。
4.  **注意**: 所有的 Scenario, Function, CC 等字段值必须严格匹配数据库中实际存在的值（如 'Budget1', 'HR Allocation'）。

**SQL 模板**：

```sql
SELECT 
    SUM(ABS(c.amount) * r.rate_no) as Allocated_HR_Cost
FROM cost_database c
JOIN rate_table r 
    ON c.year = r.year 
    AND c.scenario = r.scenario 
    AND c.month = r.month 
    AND c.key = r.key
WHERE 
    c.year = 'FY26' 
    AND c.scenario = 'Budget1'
    AND c.function = 'HR Allocation'
    AND r.cc = '413001';
```

## Q3: 对比 FY25 Actual 和 FY26 Budget1 分摊给 CT 的 IT 费用变化

**业务逻辑解析**：
需要分别计算两个场景的费用，然后做差。

**SQL 模板**：

```sql
SELECT 
    c.year,
    c.scenario,
    SUM(ABS(c.amount) * r.rate_no) as Allocated_Cost
FROM cost_database c
JOIN rate_table r 
    ON c.year = r.year 
    AND c.scenario = r.scenario 
    AND c.month = r.month 
    AND c.key = r.key
WHERE 
    c.function = 'IT Allocation'
    AND r.bl = 'CT'
    AND (
        (c.year = 'FY25' AND c.scenario = 'Actual')
        OR 
        (c.year = 'FY26' AND c.scenario = 'Budget1')
    )
GROUP BY 
    c.year, c.scenario;
```
