---
rules:
  - id: allocation_calculation
    description: "分摊计算公式"
    rule: |
      分摊金额 = ABS(Cost_Amount) * RateNo
      其中：
      1. Cost_Amount 来自 CostDataBase 表，通常 Allocation 类型的成本为负数，需取绝对值。
      2. RateNo 来自 Rate 表，为小数形式。
      3. 单一 CC 场景：直接使用该 CC 的 RateNo。
      4. 业务线 (BL) 场景：SUM(该 BL 下所有 CC 的 RateNo)。

  - id: function_key_mapping
    description: "Function 与 Key 的对应关系"
    rule: |
      不同的 Function 使用特定的 Key 进行分摊：
      - IT: WCW, SAM, Win Acc
      - IT Allocation: 480056 Cycle
      - HR: headcount
      - HR Allocation: 480055 Cycle
      - Procurement: WCW, SAM, Pooling, IM
      - Procurement Allocation: 480055 Cycle

  - id: cost_data_sign
    description: "成本数据的符号规则"
    rule: |
      - Original 成本（如 IT, HR, Procurement）为正数。
      - Allocation 成本（如 IT Allocation）为负数。
      - 同一 Function 的 Total + Allocation = 0（100% 分摊）。

  - id: date_handling
    description: "财年周期"
    rule: "财年周期为 10月 至 次年 9月。"

  - id: query_priority
    description: "分摊优先级"
    rule: "当业务线 (BL) 有多个成本中心 (CC) 时，如果查询对象可以明确到具体成本中心，必须以成本中心 (CC) 维度为准进行计算。"
---

# 业务规则详情

## 1. 分摊计算逻辑
当计算分摊费用时，必须关联 `CostDataBase` 和 `Rate` 表。
SQL 逻辑：
```sql
SELECT 
    ABS(c.Amount) * r.RateNo as AllocatedAmount
FROM SSME_FI_InsightBot_CostDataBase c
JOIN SSME_FI_InsightBot_Rate r 
    ON c.Year = r.Year 
    AND c.Scenario = r.Scenario 
    AND c.Month = r.Month 
    AND c.Key = r.Key
WHERE ...
```

## 2. 费率汇总
如果按 BL (Business Line) 汇总，必须先对 Rate 表按 BL 进行聚合，或者在连接后按 BL 分组。
建议方式：
```sql
-- 获取某 BL 在某 Key 下的总 Rate
SELECT SUM(RateNo) FROM SSME_FI_InsightBot_Rate WHERE BL = 'TargetBL' ...
```
