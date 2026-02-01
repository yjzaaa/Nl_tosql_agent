---
name: cost_allocation_test
description: 执行IT成本分摊业务场景的端到端测试。当用户需要验证成本分摊逻辑、预算对比或运行Question 1-5的业务验收测试时调用此技能。
---

# IT Cost Allocation Business Test Skill

本技能封装了针对 IT 成本分摊业务的自动化验收测试。它通过模拟自然语言查询，验证系统是否能够正确回答核心业务问题。

## 覆盖的业务场景 (Question 1-5)

1.  **IT 服务与分摊键查询**: 验证基础元数据查询能力。
2.  **HR 预算汇总**: 验证特定财年、场景和功能的成本聚合。
3.  **IT 费用分摊计算**: 验证跨表（Cost * Rate）分摊逻辑。
4.  **采购费用同比分析**: 验证跨财年/场景的差异计算。
5.  **HR 分摊变化分析**: 验证复杂的分摊后同比分析。

## 可用脚本

### `run_scenarios`

执行端到端测试脚本。该脚本会初始化 `NLToSQLAgent` 并针对真实数据库运行上述 5 个测试用例。

**用法:**

```python
# 运行所有测试
skill.execute_script("run_scenarios")
```

## 依赖
- 需要 `cost_allocation` 技能已加载。
- 需要 PostgreSQL 数据库连接配置正确。
