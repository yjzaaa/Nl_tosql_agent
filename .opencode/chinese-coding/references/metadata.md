# 中文编码规范 - 业务元数据

## 表名映射

| 中文名 | 英文表名 | 说明 |
|--------|----------|------|
| 成本数据库 | SSME_FI_InsightBot_CostDataBase | 存储成本数据主表 |
| 费率表 | SSME_FI_InsightBot_Rate | 存储分摊费率 |
| 成本中心映射 | cc_mapping | 成本中心映射关系 |
| 成本文本映射 | cost_text_mapping | 成本描述映射 |

## 意图与关键词映射

| 意图类型 | 关键词 | 说明 |
|----------|--------|------|
| 成本分摊 | allocation, 分摊 | 计算成本分摊 |
| 预算对比 | budget, 预算, 实际 | 预算与实际对比 |
| 趋势分析 | trend, 趋势, 同比, 环比 | 数据趋势分析 |
| 汇总统计 | summary, 汇总, 合计 | 数据汇总统计 |

## 字段映射

| 中文名 | 英文字段 | 类型 | 说明 |
|--------|----------|------|------|
| 金额 | Amount | FLOAT | 成本金额 |
| 财年 | Year | VARCHAR | 财年标识 |
| 场景 | Scenario | VARCHAR | 预算/实际 |
| 功能 | Function | VARCHAR | 功能部门 |
| 月份 | Month | VARCHAR | 月份 |
| 成本描述 | cost text | VARCHAR | 成本描述 |
| 分摊键 | Allocation Key | VARCHAR | 分摊依据 |
