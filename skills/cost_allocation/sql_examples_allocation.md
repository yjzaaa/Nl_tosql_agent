# 分摊计算 SQL 示例

> 适用：基于 v2.0 业务逻辑的分摊计算。

## Q1: 计算 FY25 Actual 场景下，IT Allocation 分摊给 CT 业务线的费用

**业务逻辑解析**：
1.  **数据源**：`SSME_FI_InsightBot_CostDataBase` (c) 和 `SSME_FI_InsightBot_Rate` (r)。
2.  **筛选条件**：
    *   c.Year = 'FY25'
    *   c.Scenario = 'Actual'
    *   c.Function = 'IT Allocation'
    *   r.BL = 'CT'
3.  **连接条件**：Year, Scenario, Month, Key。
4.  **计算**：SUM(ABS(c.Amount) * r.RateNo)。

**SQL 模板**：

```sql
SELECT 
    SUM(ABS(c.Amount) * r.RateNo) as Total_Allocated_Cost
FROM SSME_FI_InsightBot_CostDataBase c
JOIN SSME_FI_InsightBot_Rate r 
    ON c.Year = r.Year 
    AND c.Scenario = r.Scenario 
    AND c.Month = r.Month 
    AND c.Key = r.Key
WHERE 
    c.Year = 'FY25' 
    AND c.Scenario = 'Actual'
    AND c.Function = 'IT Allocation'
    AND r.BL = 'CT';
```

## Q2: 计算 FY26 Budget1 下，分摊给 CC '413001' 的 HR 费用

**业务逻辑解析**：
1.  **Function**: HR Allocation (注意：通常分摊的是 Allocation 类型的科目)。
2.  **Key**: 根据业务规则，HR Allocation 对应 Key '480055 Cycle' (也可以通过 JOIN 自动匹配)。
3.  **Target**: r.CC = '413001'.

**SQL 模板**：

```sql
SELECT 
    SUM(ABS(c.Amount) * r.RateNo) as Allocated_HR_Cost
FROM SSME_FI_InsightBot_CostDataBase c
JOIN SSME_FI_InsightBot_Rate r 
    ON c.Year = r.Year 
    AND c.Scenario = r.Scenario 
    AND c.Month = r.Month 
    AND c.Key = r.Key
WHERE 
    c.Year = 'FY26' 
    AND c.Scenario = 'Budget1'
    AND c.Function = 'HR Allocation'
    AND r.CC = '413001';
```

## Q3: 对比 FY25 Actual 和 FY26 Budget1 分摊给 CT 的 IT 费用变化

**业务逻辑解析**：
需要分别计算两个场景的费用，然后做差。

**SQL 模板**：

```sql
SELECT 
    c.Year,
    c.Scenario,
    SUM(ABS(c.Amount) * r.RateNo) as Allocated_Cost
FROM SSME_FI_InsightBot_CostDataBase c
JOIN SSME_FI_InsightBot_Rate r 
    ON c.Year = r.Year 
    AND c.Scenario = r.Scenario 
    AND c.Month = r.Month 
    AND c.Key = r.Key
WHERE 
    c.Function = 'IT Allocation'
    AND r.BL = 'CT'
    AND (
        (c.Year = 'FY25' AND c.Scenario = 'Actual')
        OR 
        (c.Year = 'FY26' AND c.Scenario = 'Budget1')
    )
GROUP BY 
    c.Year, c.Scenario;
```
