# 业务元数据

```json
{
  "tables": {
    "cost": "SSME_FI_InsightBot_CostDataBase",
    "rate": "SSME_FI_InsightBot_Rate",
    "cc_mapping": "CC Mapping",
    "cost_text_mapping": "Cost text mapping"
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
    "SSME_FI_InsightBot_CostDataBase": {
      "description": "成本数据库表，存储原始成本和Allocation成本",
      "columns": [
        {"name": "Year", "type": "TEXT", "description": "财年"},
        {"name": "Scenario", "type": "TEXT", "description": "场景/版本 (Actual/Budget1)"},
        {"name": "Function", "type": "TEXT", "description": "功能类型"},
        {"name": "Cost text", "type": "TEXT", "description": "成本文本"},
        {"name": "Account", "type": "TEXT", "description": "总账科目"},
        {"name": "Category", "type": "TEXT", "description": "成本类型"},
        {"name": "Key", "type": "TEXT", "description": "分摊依据"},
        {"name": "Year Total", "type": "FLOAT", "description": "全年12个月合计"},
        {"name": "Month", "type": "TEXT", "description": "月份"},
        {"name": "Amount", "type": "FLOAT", "description": "金额"}
      ]
    },
    "SSME_FI_InsightBot_Rate": {
      "description": "费率表，存储分摊比例",
      "columns": [
        {"name": "BL", "type": "TEXT", "description": "业务线"},
        {"name": "CC", "type": "TEXT", "description": "成本中心"},
        {"name": "Year", "type": "TEXT", "description": "财年"},
        {"name": "Scenario", "type": "TEXT", "description": "场景"},
        {"name": "Month", "type": "TEXT", "description": "月份"},
        {"name": "Key", "type": "TEXT", "description": "分摊依据"},
        {"name": "RateNo", "type": "FLOAT", "description": "分摊比例 (小数)"}
      ]
    }
  }
}
```
