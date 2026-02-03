---
name: cost_allocation
version: 2.3.0
description: IT功能成本分摊业务逻辑与规则，用于成本分摊、预算/实际对比与趋势分析。
license: Private
---

# IT功能成本分摊业务技能（精简）

## 适用范围

- 成本分摊计算
- 预算 vs 实际对比
- 趋势/对比分析

## 资料导航（references/）

- 业务元数据（表名映射/意图与关键词映射）：references/metadata.md
- 业务规则摘要：references/business_rules.md
- 示例与说明：references/sql*examples*\*.md

工作流通过 skill 中间件读取表名后，从数据库自动拉取表结构。
元数据不包含字段级结构。

## 核心业务规则（摘要）

1. 分摊金额 = ABS(cost_amount) \* rate_no。
2. Allocation 类成本通常为负数，需取绝对值。
3. BL 场景先对 Rate 按 BL 汇总，再进行分摊。
4. Function 与 Key 存在固定映射（如 IT/HR/Procurement 的 Allocation Key）。
5. 财年周期为 10 月至次年 9 月。

## 可用脚本

### `generate_allocation_sql`

用于生成标准分摊 SQL。

示例调用：

```python
skill.execute_script(
    "generate_allocation_sql",
    args=[
        "--years", "FY25",
        "--scenarios", "Actual",
        "--function", "IT Allocation",
        "--party_field", "r.bl",
        "--party_value", "'CT'"
    ]
)
```
