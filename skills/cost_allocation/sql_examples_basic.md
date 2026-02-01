# 基础查询与筛选类（示例库）

> 适用：枚举查询、单表聚合、明细 + 汇总。

## Q1：XX 费用包括哪些服务？分摊依据是什么？（枚举查询 + 去重）

**需求特征**：筛选指定 Function，枚举服务内容 [cost_text] 和分摊依据 [key]，无计算 / 聚合，需 DISTINCT 去重。
**注意**: Function 值必须严格匹配数据库中实际存在的值。

**SQL 示例（单语句）**

```sql
SELECT DISTINCT
  cost_text AS Service_Content,
  key AS Allocation_Key
FROM cost_database
WHERE function = 'IT'
```

## Q2：FY26 计划了多少 HR 费用预算？（明细查询 + 汇总）

**需求特征**：筛选 Year/Scenario/Function，明细 + 汇总；汇总用 SUM(amount)。
**注意**: Scenario, Function 等字段必须使用数据库中存在的精确值（如 'Budget1' 而非 'Plan'）。

**SQL 示例（CTE + 单语句）**

```sql
WITH DetailedData AS (
  SELECT
    year,
    scenario,
    function,
    cost_text AS Service_Content,
    key AS Allocation_Key,
    month,
    COALESCE(amount, 0.0) AS Amount
  FROM cost_database
  WHERE year = 'FY26' AND scenario = 'Budget1' AND function = 'HR'
),
AggregatedData AS (
  SELECT
    year,
    scenario,
    function,
    SUM(COALESCE(amount, 0.0)) AS Total_HR_Cost_FY26_Budget1
  FROM cost_database
  WHERE year = 'FY26' AND scenario = 'Budget1' AND function = 'HR'
  GROUP BY year, scenario, function
)
SELECT * FROM DetailedData
UNION ALL
SELECT year, scenario, function, NULL, NULL, NULL, Total_HR_Cost_FY26_Budget1
FROM AggregatedData
ORDER BY year DESC, scenario, function;
```
