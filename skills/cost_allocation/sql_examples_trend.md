# 对比 / 趋势分析类（CTE）

> 适用：跨周期对比、变化额 / 变化率、环比趋势。

## Q5：采购费用 FY25 Actual 到 FY26 Budget1 变化？

**需求特征**：CTE 计算基期/现期 + 变化额 + 变化率，含除零保护。
**注意**: Scenario, Function 等字段必须使用数据库中存在的精确值。

**SQL 示例（单语句）**

```sql
WITH base_cost AS (
  SELECT 'FY26_Budget1' AS Period, year, scenario, function,
         SUM(amount) AS cost, 1 AS sort_key
  FROM cost_database
  WHERE year = 'FY26' AND scenario = 'Budget1' AND function = 'Procurement'
  GROUP BY year, scenario, function
  UNION ALL
  SELECT 'FY25_Actual' AS Period, year, scenario, function,
         SUM(amount) AS cost, 2 AS sort_key
  FROM cost_database
  WHERE year = 'FY25' AND scenario = 'Actual' AND function = 'Procurement'
  GROUP BY year, scenario, function
),
cost_values AS (
  SELECT
    (SELECT cost FROM base_cost WHERE Period = 'FY26_Budget1') AS fy26_cost,
    (SELECT cost FROM base_cost WHERE Period = 'FY25_Actual') AS fy25_cost
),
change_calc AS (
  SELECT
    'Change_Calculation' AS Period, '' AS year, '' AS scenario,
    'Procurement' AS function,
    fy26_cost - fy25_cost AS cost,
    3 AS sort_key,
    CASE WHEN fy25_cost = 0 THEN 0
         ELSE ROUND(((fy26_cost / fy25_cost) - 1) * 100, 2) END AS change_rate
  FROM cost_values
)
SELECT Period, year, scenario, function, cost AS Total_Procurement_Cost,
       '' AS "Cost_Change_Rate(%)", sort_key
FROM base_cost
UNION ALL
SELECT Period, year, scenario, function, cost AS Total_Procurement_Cost,
       change_rate AS "Cost_Change_Rate(%)", sort_key
FROM change_calc
ORDER BY sort_key ASC;
```

## Q6：HR 费用月度趋势（环比）

**需求特征**：CTE + month_num 排序 + 环比增长率。
**注意**: Month, Scenario 等字段必须使用数据库中存在的精确值（如 'Jan', 'Feb'）。

**SQL 示例（单语句）**

```sql
WITH monthly_cost AS (
  SELECT
    month,
    SUM(amount) AS cost,
    CASE month
      WHEN 'Jan' THEN 1 WHEN 'Feb' THEN 2 WHEN 'Mar' THEN 3 WHEN 'Apr' THEN 4
      WHEN 'May' THEN 5 WHEN 'Jun' THEN 6 WHEN 'Jul' THEN 7 WHEN 'Aug' THEN 8
      WHEN 'Sep' THEN 9 WHEN 'Oct' THEN 10 WHEN 'Nov' THEN 11 WHEN 'Dec' THEN 12
    END AS month_num
  FROM cost_database
  WHERE year = 'FY24' AND scenario = 'Actual' AND function = 'HR'
  GROUP BY month,
    CASE month
      WHEN 'Jan' THEN 1 WHEN 'Feb' THEN 2 WHEN 'Mar' THEN 3 WHEN 'Apr' THEN 4
      WHEN 'May' THEN 5 WHEN 'Jun' THEN 6 WHEN 'Jul' THEN 7 WHEN 'Aug' THEN 8
      WHEN 'Sep' THEN 9 WHEN 'Oct' THEN 10 WHEN 'Nov' THEN 11 WHEN 'Dec' THEN 12
    END
),
mom_result AS (
  SELECT
    curr.month,
    curr.cost AS Current_Month_Cost,
    prev.cost AS Previous_Month_Cost,
    CASE WHEN prev.cost = 0 OR prev.cost IS NULL THEN 0.00
         ELSE ROUND(((curr.cost / prev.cost) - 1) * 100, 2) END AS "MoM_Growth_Rate(%)",
    curr.month_num
  FROM monthly_cost curr
  LEFT JOIN monthly_cost prev
    ON curr.month_num = prev.month_num + 1
)
SELECT month, Current_Month_Cost, Previous_Month_Cost, "MoM_Growth_Rate(%)"
FROM mom_result
ORDER BY month_num ASC;
```
