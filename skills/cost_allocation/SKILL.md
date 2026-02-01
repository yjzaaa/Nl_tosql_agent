---
name: cost_allocation
version: 2.1.0
description: IT功能成本分摊业务逻辑与规则，用于支持成本分析、预算编制和成本管控。Invoke when analyzing cost allocation, budget vs actuals, or cost trends.
license: Private
---

# IT功能成本分摊业务技能

本技能包含了IT、HR、Procurement等功能成本分摊的业务逻辑、数据结构定义和计算规则。

## 适用范围
- 财年成本分摊分析
- 预算 vs 实际对比
- 趋势分析

## Available Scripts

### `generate_allocation_sql`
Generates the standard SQL query for cost allocation calculation.

**Usage:**
```python
skill.execute_script(
    "generate_allocation_sql",
    args=[
        "--years", "FY25",
        "--scenarios", "Actual",
        "--function", "IT Allocation",
        "--party_field", "t7.[BL]",
        "--party_value", "'CT'"
    ]
)
```

**Parameters:**
- `years`: List of fiscal years (e.g. FY24 FY25)
- `scenarios`: List of scenarios (e.g. Actual Budget)
- `function`: Function name to filter
- `party_field`: Field to group by (e.g. t7.[BL] or t7.[CC])
- `party_value`: Value to filter the party field
