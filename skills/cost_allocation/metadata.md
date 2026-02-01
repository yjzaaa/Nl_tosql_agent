# 业务元数据

```json
{
  "tables": {
    "cost": "cost_database",
    "rate": "rate_table",
    "cc_mapping": "cc_mapping",
    "cost_text_mapping": "cost_text_mapping"
  },
  "default_tables": ["cost"],
  "intent_table_map": {
    "allocation": ["cost", "rate"],
    "general_query": ["cost"],
    "compare_budget_vs_actual": ["cost", "rate"],
    "trend": ["cost", "rate"]
  },
  "keyword_table_map": {
    "分摊": ["cost", "rate"],
    "allocation": ["cost", "rate"],
    "rate": ["rate"],
    "预算": ["cost"],
    "实际": ["cost"],
    "趋势": ["cost"],
    "对比": ["cost"],
    "费率": ["rate"],
    "比例": ["rate"]
  },
  "table_schemas": {
    "cost_database": {
      "description": "成本数据库表，存储原始成本和Allocation成本。Scenario字段的值必须严格匹配数据库中实际存在的值（如 'Actual', 'Budget1'）。禁止使用任何未在数据库中出现的别名（如 'Plan', 'Forecast'）。",
      "columns": [
        {"name": "year", "type": "TEXT", "description": "财年"},
        {"name": "scenario", "type": "TEXT", "description": "场景/版本 (必须使用数据库中的精确值，如 'Actual', 'Budget1')"},
        {"name": "function", "type": "TEXT", "description": "功能类型 (必须使用数据库中的精确值)"},
        {"name": "cost_text", "type": "TEXT", "description": "成本文本 (必须使用数据库中的精确值)"},
        {"name": "account", "type": "TEXT", "description": "总账科目 (必须使用数据库中的精确值)"},
        {"name": "category", "type": "TEXT", "description": "成本类型 (必须使用数据库中的精确值)"},
        {"name": "key", "type": "TEXT", "description": "分摊依据 (必须使用数据库中的精确值)"},
        {"name": "year_total", "type": "FLOAT", "description": "全年12个月合计"},
        {"name": "month", "type": "TEXT", "description": "月份 (必须使用数据库中的精确值，如 'Jan', 'Feb')"},
        {"name": "amount", "type": "FLOAT", "description": "金额"}
      ]
    },
    "rate_table": {
      "description": "费率表，存储分摊比例。Scenario字段的值必须严格匹配数据库中实际存在的值（如 'Actual', 'Budget1'）。",
      "columns": [
        {"name": "bl", "type": "TEXT", "description": "业务线 (必须使用数据库中的精确值)"},
        {"name": "cc", "type": "TEXT", "description": "成本中心 (必须使用数据库中的精确值)"},
        {"name": "year", "type": "TEXT", "description": "财年"},
        {"name": "scenario", "type": "TEXT", "description": "场景 (必须使用数据库中的精确值，如 'Actual', 'Budget1')"},
        {"name": "month", "type": "TEXT", "description": "月份 (必须使用数据库中的精确值)"},
        {"name": "key", "type": "TEXT", "description": "分摊依据 (必须使用数据库中的精确值)"},
        {"name": "rate_no", "type": "FLOAT", "description": "分摊比例 (小数)"}
      ]
    },
    "cc_mapping": {
      "description": "成本中心映射表",
      "columns": [
        {"name": "cost_center_number", "type": "TEXT", "description": "成本中心编号"},
        {"name": "business_line", "type": "TEXT", "description": "业务线"}
      ]
    },
    "cost_text_mapping": {
      "description": "成本文本映射表",
      "columns": [
        {"name": "cost_text", "type": "TEXT", "description": "成本文本"},
        {"name": "function", "type": "TEXT", "description": "功能类型"}
      ]
    }
  }
}
```
