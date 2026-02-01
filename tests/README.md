# 测试指南

## 运行测试

### 运行所有测试
```bash
pytest
```

### 运行特定测试文件
```bash
pytest tests/test_skill_loader.py
```

### 运行特定测试类
```bash
pytest tests/test_skill_loader.py::TestSkillLoader
```

### 运行特定测试方法
```bash
pytest tests/test_skill_loader.py::TestSkillLoader::test_load_skill
```

### 运行测试并显示详细输出
```bash
pytest -v
```

### 运行测试并显示print输出
```bash
pytest -s
```

### 运行测试并生成覆盖率报告
```bash
pytest --cov=src --cov-report=html
```

### 运行测试并生成XML覆盖率报告
```bash
pytest --cov=src --cov-report=xml
```

### 运行测试但排除慢速测试
```bash
pytest -m "not slow"
```

### 只运行单元测试
```bash
pytest -m "unit"
```

### 只运行集成测试
```bash
pytest -m "integration"
```

## 测试结构

```
tests/
├── conftest.py              # pytest配置和fixtures
├── fixtures/                # 测试数据和fixtures
├── test_skill_loader.py     # 测试SkillLoader和Skill类
├── test_nl_to_sql_agent.py  # 测试NLToSQLAgent
├── test_workflow.py         # 测试SkillAwareWorkflow
├── test_agents.py           # 测试各个agent节点
└── test_config.py           # 测试配置管理
```

## 测试覆盖范围

### 已实现的测试

#### test_skill_loader.py
- SkillModule类测试
  - 创建模块
  - 加载模块内容
  - 转换为字典

- Skill类测试
  - 创建技能
  - 添加模块
  - 获取模块和内容
  - 获取业务规则
  - 获取元数据
  - 获取SQL模板
  - 列出脚本
  - 执行脚本

- SkillLoader类测试
  - 初始化
  - 加载技能
  - 缓存技能
  - 列出可用技能
  - 重新加载技能
  - 加载带模块的技能
  - 加载带引用的技能

- MultiSkillLoader类测试
  - 初始化
  - 添加路径
  - 加载技能
  - 列出所有技能
  - 重新加载所有
  - 获取技能信息

#### test_nl_to_sql_agent.py
- NLToSQLAgent类测试
  - 初始化（带/不带技能路径）
  - 加载技能
  - 无技能时的初始化
  - 基本查询
  - 带额外参数的查询
  - 工作流异常处理
  - 重新加载技能
  - 列出可用技能
  - 状态初始化
  - 结果结构

#### test_workflow.py
- SkillAwareState TypedDict测试
  - 创建状态

- SkillAwareWorkflow类测试
  - 初始化（带/不带技能）
  - 设置技能
  - 构建图
  - 缓存图
  - 路由逻辑（验证后、执行后、审核后）

- 工作流函数测试
  - 获取技能工作流
  - 缓存工作流
  - 重置工作流
  - 多个技能工作流

#### test_agents.py
- IntentAnalysisAgent测试
  - 基本意图分析
  - 带技能上下文的意图分析

- LoadContextAgent测试
  - 加载上下文
  - 带元数据的上下文加载

- SQLGenerationAgent测试
  - SQL生成
  - 带业务规则的SQL生成

- SQLValidationAgent测试
  - 验证有效SQL
  - 验证无效SQL

- ExecuteSQLAgent测试
  - 成功执行SQL
  - SQL执行错误

- ResultReviewAgent测试
  - 审核通过
  - 审核失败

- RefineAnswerAgent测试
  - 优化答案
  - 带执行结果的优化

#### test_config.py
- 配置加载测试
  - 从文件加载
  - 默认配置
  - 环境变量
  - 单例模式

- AppConfig测试
  - 默认值
  - ModelConfig
  - ExcelConfig
  - DataSourceConfig
  - LoggingConfig

- 配置验证测试
  - 无效配置类型
  - 嵌套配置验证

## Fixtures

### 项目级Fixtures
- `project_root`: 项目根目录
- `skills_dir`: skills目录
- `fixtures_dir`: fixtures目录

### 测试级Fixtures
- `temp_skill_dir`: 临时技能目录
- `sample_skill_content`: 示例技能内容
- `sample_business_rules`: 示例业务规则
- `sample_metadata`: 示例元数据
- `sample_config`: 示例配置
- `mock_excel_file`: 模拟Excel文件

## 添加新测试

### 创建新的测试文件
```bash
# 1. 创建tests/test_new_feature.py
touch tests/test_new_feature.py

# 2. 添加测试类和测试方法
# 3. 运行新测试
pytest tests/test_new_feature.py
```

### 测试模板
```python
"""Tests for new feature"""

import pytest
from unittest.mock import Mock, patch

from src.new_feature import NewFeature


class TestNewFeature:
    """Test NewFeature class"""

    @pytest.fixture
    def mock_dependency(self):
        """Create a mock dependency"""
        return Mock()

    def test_basic_functionality(self, mock_dependency):
        """Test basic functionality"""
        feature = NewFeature(dependency=mock_dependency)
        result = feature.do_something()
        
        assert result is not None

    @patch('src.new_feature.some_function')
    def test_with_mock(self, mock_func, mock_dependency):
        """Test with mocked function"""
        mock_func.return_value = "mocked result"
        
        feature = NewFeature(dependency=mock_dependency)
        result = feature.do_something()
        
        assert result == "mocked result"
```

## 调试测试

### 在第一个失败时停止
```bash
pytest -x
```

### 进入调试器
```bash
pytest --pdb
```

### 失败时进入调试器
```bash
pytest --pdb-failures
```

### 显示本地变量
```bash
pytest -l
```

## 持续集成

测试将在以下情况下自动运行：
- Pull Request创建
- Push到main分支

覆盖率要求：
- 最低覆盖率: 70%
- 目标覆盖率: 85%
