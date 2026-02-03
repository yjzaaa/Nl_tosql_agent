---
name: chinese-coding
version: 1.0.0
description: "OpenCode 中文编码规范技能 - 强制要求所有代码使用中文注释，集成开发必备的编码规范检查工具"
license: MIT
---

# OpenCode 中文编码规范技能

## 技能概述

本技能为 OpenCode 智能体提供中文编码规范支持，确保所有代码遵循以下原则：
- 所有注释必须使用中文
- 函数、类、变量命名遵循项目规范
- 代码结构清晰，易于维护

## 核心能力

1. **中文注释检查** - 验证所有代码注释使用中文
2. **编码规范验证** - 检查代码风格和命名规范
3. **开发规范指导** - 提供开发最佳实践建议

## 使用场景

- 新项目初始化时强制中文注释
- 代码审查时检查注释规范
- 团队协作时统一编码风格

## 技能配置

```yaml
skill:
  name: "chinese-coding"
  version: "1.0.0"
  
coding_standards:
  comments:
    language: "chinese"           # 强制中文注释
    required_for:
      - functions                 # 函数必须注释
      - classes                   # 类必须注释
      - complex_logic             # 复杂逻辑必须注释
    minimum_length: 5             # 最小注释长度
  
  naming:
    convention: "snake_case"      # 命名规范
    max_identifier_length: 50     # 标识符最大长度
  
  structure:
    max_function_lines: 100       # 函数最大行数
    max_class_lines: 500          # 类最大行数
    required_sections:
      - imports
      - type_definitions
      - constants
      - classes
      - functions
      - main
```

## 规则详情

### 中文注释规则

所有代码必须包含中文注释，包括但不限于：

```python
def calculate_allocation_rate(
    cost_amount: float,
    rate_no: float,
    allocation_key: str
) -> float:
    """
    计算分摊金额

    根据成本金额和分摊系数计算最终分摊金额。
    分摊金额 = ABS(成本金额) * 分摊系数

    参数:
        cost_amount: 原始成本金额（可能为负数）
        rate_no: 分摊系数
        allocation_key: 分摊键值（如 'Headcount', 'Revenue'）

    返回:
        float: 计算后的分摊金额
    """
    # 取绝对值，因为分摊类成本通常为负数
    absolute_cost = abs(cost_amount)
    
    # 计算分摊金额
    allocated_amount = absolute_cost * rate_no
    
    return allocated_amount
```

### 命名规范

```python
# 变量命名 - 使用描述性中文命名
total_cost_amount = 10000.0          # 总成本金额
monthly_budget_limit = 5000.0        # 月度预算上限

# 函数命名 - 动词+描述
def validate_sql_syntax(sql_query: str) -> bool:
    """校验 SQL 语法正确性"""
    pass

def generate_allocation_report(
    year: str,
    scenario: str,
    function: str
) -> Dict[str, Any]:
    """生成分摊报表数据"""
    pass

# 类命名 - PascalCase
class CostAllocationCalculator:
    """成本分摊计算器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化计算器配置"""
        self.config = config
        
    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """执行分摊计算"""
        pass
```

### 编码结构要求

```python
# 标准 Python 文件结构

# 1. 版权和说明（可选）
# 版权所有 2024 xxx

# 2. 导入模块
import os
import json
from typing import Dict, List, Optional

# 3. 导入第三方库
import pandas as pd
from langchain_core.messages import BaseMessage

# 4. 类型定义
class AgentState(TypedDict):
    """智能体状态定义"""
    trace_id: Optional[str]
    messages: List[BaseMessage]
    sql_query: Optional[str]

# 5. 常量定义
DEFAULT_MAX_ROWS = 1000          # 默认最大返回行数
SQL_KEYWORDS = ["SELECT", "FROM"] # SQL 关键词列表

# 6. 核心类
class DataSourceManager:
    """数据源管理器 - 负责数据库连接和查询"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化数据源配置"""
        self.config = config
        self.connection = None
    
    def connect(self) -> bool:
        """建立数据库连接"""
        pass

# 7. 核心函数
def validate_sql_query(sql: str) -> bool:
    """校验 SQL 查询语句的安全性"""
    pass

# 8. 主入口（如果需要）
if __name__ == "__main__":
    main()
```

## 错误处理规范

```python
class ValidationError(Exception):
    """校验异常 - 用于处理参数校验错误"""
    
    def __init__(self, message: str, field: str = None):
        """初始化异常信息
        
        参数:
            message: 错误描述信息
            field: 触发错误的字段名（可选）
        """
        super().__init__(message)
        self.field = field


def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """处理输入数据
    
    参数:
        data: 待处理的数据字典
        
    返回:
        处理后的数据字典
        
    异常:
        ValidationError: 数据校验失败时抛出
    """
    # 数据校验
    if "amount" not in data:
        raise ValidationError("缺少必要字段: amount", field="amount")
    
    # 数据处理逻辑
    processed = {**data}
    return processed
```

## 测试用例规范

```python
import unittest

class TestCostAllocation(unittest.TestCase):
    """成本分摊计算测试类"""
    
    def setUp(self):
        """测试初始化"""
        self.calculator = CostAllocationCalculator({})
    
    def test_positive_amount(self):
        """测试正数金额分摊计算"""
        result = self.calculator.calculate({"amount": 1000})
        self.assertEqual(result["allocated"], 1000)
    
    def test_negative_amount(self):
        """测试负数金额分摊计算（取绝对值）"""
        result = self.calculator.calculate({"amount": -1000})
        self.assertEqual(result["allocated"], 1000)
```

## 与项目集成

### 在项目中使用本技能

```python
from skills.loader import SkillLoader

# 加载中文编码技能
loader = SkillLoader(skill_path="./.opencode")
skill = loader.load_skill("chinese-coding")

# 获取编码规范
coding_standards = skill.get_module("coding_standards")

# 应用规范检查
is_valid = coding_standards.validate_code(source_code)
```

### 与 LLM Agent 集成

```python
from src.skills.middleware import SkillMiddleware

# 创建技能中间件
middleware = SkillMiddleware(
    skill_path=".opencode",
    default_skill="chinese-coding",
    llm=llm
)

# 技能会自动为代码生成任务提供中文注释规范指导
```

## 参考资料

- 业务元数据：references/metadata.md
- 编码规范细则：references/coding_standards.md
- 命名约定：references/naming_conventions.md
