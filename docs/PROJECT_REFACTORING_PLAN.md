# 项目架构分析与修改建议

## 一、项目结构对比

### 1. 当前项目结构 (ExcelMind-main)

```
ExcelMind-main/
├── src/
│   ├── agents/                    # Agent节点实现
│   │   ├── __init__.py
│   │   ├── intent_analysis_agent.py
│   │   ├── sql_generation_agent.py
│   │   ├── sql_validation_agent.py
│   │   ├── execute_sql_agent.py
│   │   ├── result_review_agent.py
│   │   ├── refine_answer_agent.py
│   │   └── llm.py
│   ├── core/                      # 核心模块
│   │   ├── data_sources/            # 数据源策略模式
│   │   ├── interfaces.py
│   │   ├── loader.py
│   │   ├── metadata.py
│   │   └── schemas.py
│   ├── workflow/                  # 工作流定义
│   │   ├── __init__.py
│   │   └── skill_aware.py          # SkillAwareWorkflow类
│   ├── prompts/                   # Prompt管理器
│   │   ├── __init__.py
│   │   └── manager.py              # 统一的prompt模板
│   ├── skills/                    # Skill加载器
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── loader.py
│   ├── config/                    # 配置管理
│   │   ├── logger_interface.py
│   │   ├── logger.py
│   │   └── settings.py
│   ├── main.py
│   └── nl_to_sql_agent.py         # NLToSQLAgent主类
├── tests/
├── config.yaml
├── SKILL.md
└── pyproject.toml
```

### 2. Zip文件项目结构

```
ExcelMind-main/
├── src/
│   ├── agents/                    # Agent节点实现
│   │   ├── __init__.py
│   │   ├── intent_analysis_agent.py
│   │   ├── sql_generation_agent.py
│   │   ├── sql_validation_agent.py
│   │   ├── execute_sql_agent.py
│   │   ├── result_review_agent.py
│   │   ├── refine_answer_agent.py
│   │   └── llm.py
│   ├── graph/                     # 工作流定义
│   │   ├── __init__.py
│   │   └── graph.py              # Graph工作流类
│   ├── prompts/                   # Prompt模板（独立文件）
│   │   ├── __init__.py
│   │   ├── intent_analysis_prompt.md
│   │   ├── sql_generation_prompt.md
│   │   ├── sql_validation_prompt.md
│   │   ├── result_review_prompt.md
│   │   ├── answer_refinement_prompt.md
│   │   ├── join_suggest_prompt.md
│   │   └── system_prompt.md
│   ├── excel_agent/              # Excel Agent完整实现
│   │   ├── __init__.py
│   │   ├── main.py               # Web服务入口
│   │   ├── api.py                # FastAPI接口
│   │   ├── graph.py              # 工作流
│   │   ├── prompts.py            # Prompt模板
│   │   ├── excel_loader.py        # Excel加载器
│   │   ├── business_metadata.py   # 业务元数据
│   │   ├── business_tools.py      # 业务工具
│   │   ├── tools.py             # 数据分析工具
│   │   ├── knowledge_base.py      # 知识库管理
│   │   ├── stream.py            # 流式对话
│   │   ├── config.py            # 配置
│   │   ├── logger.py            # 日志
│   │   ├── schemas.py           # 数据模式
│   │   ├── feedback_manager.py   # 反馈管理
│   │   ├── cache.py             # 缓存
│   │   ├── allocationagent.py    # 分摊agent
│   │   ├── join_service.py      # 联表服务
│   │   ├── sqlserver.py         # SQL Server适配器
│   │   ├── trace_store.py       # 跟踪存储
│   │   ├── agent-skills.code-workspace
│   │   └── frontend/
│   │       └── index.html       # Web前端
│   ├── sqlserver.py               # SQL Server连接
│   ├── draw_graph.py             # 图表绘制
│   ├── inspect_data.py           # 数据检查
│   ├── test_workflow.py          # 工作流测试
│   └── main.py                  # 简单入口
├── business/                      # 业务文档
│   ├── README.md
│   ├── metadata.md               # 业务元数据
│   ├── sql_examples_basic.md
│   ├── sql_examples_allocation.md
│   ├── sql_examples_trend.md
│   └── sql_generator_template.md
├── tests/
├── main.py
├── pyproject.toml
└── README.md
```

## 二、架构差异分析

### 关键区别

| 方面 | 当前项目 | Zip项目 |
|------|---------|---------|
| **工作流** | `workflow/skill_aware.py` (类) | `graph/graph.py` (类) |
| **Prompt管理** | `prompts/manager.py` (统一管理器) | `prompts/*.md` (独立文件) |
| **数据源** | `core/data_sources/` (策略模式) | `excel_agent/sqlserver.py` (简单适配) |
| **核心模块** | `core/` (模块化) | `excel_agent/` (集成) |
| **Skill系统** | `skills/loader.py` | `agent-skills.code-workspace` |
| **主入口** | `src/main.py` + `src/nl_to_sql_agent.py` | `src/main.py` (简单) |
| **Web前端** | 无 | `excel_agent/frontend/index.html` |
| **工具系统** | `tools/common.py` | `excel_agent/tools.py` + `business_tools.py` |
| **知识库** | 无 | `excel_agent/knowledge_base.py` |
| **业务文档** | `SKILL.md` | `business/` 目录 |

### 优先级

根据业务需求和功能完整性，Zip项目的功能更完整，建议将当前项目改造为Zip项目的架构。

## 三、修改建议

### Phase 1: 工作流迁移 (高优先级)

**目标**: 将 `workflow/skill_aware.py` 迁移到 `graph/graph.py` 架构

**步骤**:
1. 创建 `src/graph/__init__.py`
2. 创建 `src/graph/graph.py`，复制 `workflow/skill_aware.py` 的功能
3. 更新所有agent节点的导入路径
4. 更新 `nl_to_sql_agent.py` 中的工作流引用

**修改文件**:
- 新增: `src/graph/__init__.py`
- 新增: `src/graph/graph.py`
- 修改: `src/nl_to_sql_agent.py`
- 修改: `src/agents/*.py` (更新导入)

### Phase 2: Prompt模板分离 (高优先级)

**目标**: 将 `prompts/manager.py` 中的模板迁移到独立的md文件

**步骤**:
1. 创建 `src/prompts/` 目录结构
2. 提取 `manager.py` 中的模板到独立md文件:
   - `src/prompts/intent_analysis_prompt.md`
   - `src/prompts/sql_generation_prompt.md`
   - `src/prompts/sql_validation_prompt.md`
   - `src/prompts/result_review_prompt.md`
   - `src/prompts/answer_refinement_prompt.md`
3. 更新 `src/prompts/__init__.py` 加载md文件
4. 更新agent节点导入新的prompt

**修改文件**:
- 新增: `src/prompts/*.md` (6个文件)
- 修改: `src/prompts/__init__.py`
- 修改: `src/agents/*.py`

### Phase 3: 数据源适配 (中优先级)

**目标**: 添加SQL Server支持和Excel适配器

**步骤**:
1. 复制 `src/excel_agent/sqlserver.py` 到 `src/core/data_sources/sqlserver_source.py`
2. 复制 `src/excel_agent/excel_loader.py` 到 `src/core/data_sources/excel_source.py`
3. 更新 `DataSourceManager` 注册新的数据源
4. 添加连接字符串支持

**修改文件**:
- 新增: `src/core/data_sources/sqlserver_source.py`
- 新增: `src/core/data_sources/excel_loader.py`
- 修改: `src/core/data_sources/manager.py`
- 修改: `src/core/data_sources/__init__.py`

### Phase 4: Web服务集成 (中优先级)

**目标**: 集成FastAPI和前端界面

**步骤**:
1. 复制 `src/excel_agent/api.py` 到 `src/api.py`
2. 复制 `src/excel_agent/frontend/` 到 `src/frontend/`
3. 更新 `src/main.py` 作为服务入口
4. 配置uvicorn和FastAPI

**修改文件**:
- 新增: `src/api.py`
- 新增: `src/frontend/index.html`
- 修改: `src/main.py`
- 新增: `requirements.txt` 或更新 `pyproject.toml`

### Phase 5: 工具系统完善 (中优先级)

**目标**: 添加完整的数据分析工具集

**步骤**:
1. 创建 `src/tools/` 目录
2. 从 `excel_agent/tools.py` 复制工具函数
3. 从 `excel_agent/business_tools.py` 复制业务工具
4. 创建 `src/tools/__init__.py` 统一导出
5. 更新agent节点导入工具

**修改文件**:
- 新增: `src/tools/`
- 修改: `src/agents/sql_generation_agent.py`

### Phase 6: 知识库系统 (低优先级)

**目标**: 添加Chroma向量数据库和知识管理

**步骤**:
1. 复制 `excel_agent/knowledge_base.py` 到 `src/knowledge_base.py`
2. 复制 `excel_agent/feedback_manager.py` 到 `src/feedback_manager.py`
3. 复制 `excel_agent/cache.py` 到 `src/cache.py`
4. 添加Chroma依赖到pyproject.toml

**修改文件**:
- 新增: `src/knowledge_base.py`
- 新增: `src/feedback_manager.py`
- 新增: `src/cache.py`
- 修改: `pyproject.toml`

### Phase 7: 业务文档迁移 (低优先级)

**目标**: 添加business目录和业务元数据

**步骤**:
1. 创建 `business/` 目录
2. 复制所有business文件
3. 更新 `business/metadata.md` 为当前业务规则
4. 更新提示词加载逻辑读取business目录

**修改文件**:
- 新增: `business/` 目录及所有文件
- 修改: `src/prompts/__init__.py`

## 四、具体代码修改示例

### 1. 创建 graph/graph.py

```python
"""Graph-based Workflow Definition"""

from langchain_core.messages.base import BaseMessage
from typing import Annotated, Any, Dict, List, Literal, TypedDict, Optional
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from config.logger_interface import get_logger
from agents.load_context_agent import load_context_node
from agents.intent_analysis_agent import analyze_intent_node
from agents.sql_generation_agent import generate_sql_node
from agents.sql_validation_agent import validate_sql_node
from agents.execute_sql_agent import execute_sql_node
from agents.result_review_agent import review_result_node
from agents.refine_answer_agent import refine_answer_node

logger = get_logger("graph")


class AgentState(TypedDict):
    """Agent State"""
    trace_id: Annotated[Optional[str], lambda x, y: y]
    messages: Annotated[List[BaseMessage], add_messages]
    intent_analysis: Annotated[Any, lambda x, y: y]
    user_query: Annotated[Optional[str], lambda x, y: y]
    sql_query: Annotated[Optional[str], lambda x, y: y]
    sql_valid: Annotated[bool, lambda x, y: y]
    execution_result: Annotated[Optional[str], lambda x, y: y]
    review_passed: Annotated[Optional[bool], lambda x, y: y]
    review_message: Annotated[Optional[str], lambda x, y: y]
    table_names: Annotated[Optional[List[str]], lambda x, y: y]
    data_source_type: Annotated[Optional[str], lambda x, y: y]
    error_message: Annotated[Optional[str], lambda x, y: y]
    retry_count: Annotated[Optional[int], lambda x, y: y]


class GraphWorkflow:
    def __init__(self):
        self.graph = None

    def build_graph(self) -> StateGraph:
        """Build workflow graph"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("load_context", load_context_node)
        workflow.add_node("analyze_intent", analyze_intent_node)
        workflow.add_node("generate_sql", generate_sql_node)
        workflow.add_node("validate_sql", validate_sql_node)
        workflow.add_node("execute_sql", execute_sql_node)
        workflow.add_node("review_result", review_result_node)
        workflow.add_node("refine_answer", refine_answer_node)

        # Set entry point
        workflow.set_entry_point("analyze_intent")

        # Add edges
        workflow.add_edge("analyze_intent", "load_context")
        workflow.add_edge("load_context", "generate_sql")
        workflow.add_edge("generate_sql", "validate_sql")
        
        # Conditional edges
        workflow.add_conditional_edges(
            "validate_sql",
            self._route_after_validation,
            {
                "execute_sql": "execute_sql",
                "generate_sql": "generate_sql",
                "refine_answer": "refine_answer",
            },
        )
        workflow.add_conditional_edges(
            "execute_sql",
            self._route_after_execution,
            {
                "review_result": "review_result",
                "generate_sql": "generate_sql",
                "analyze_intent": "analyze_intent",
            },
        )
        workflow.add_conditional_edges(
            "review_result",
            self._route_after_review,
            {
                "refine_answer": "refine_answer",
                "generate_sql": "generate_sql",
                "analyze_intent": "analyze_intent",
            },
        )

        workflow.add_edge("refine_answer", END)

        return workflow.compile()

    def _route_after_validation(self, state: AgentState) -> Literal["execute_sql", "generate_sql", "refine_answer"]:
        if state.get("sql_valid"):
            return "execute_sql"
        if state.get("retry_count", 0) >= 5:
            return "refine_answer"
        return "generate_sql"

    def _route_after_execution(self, state: AgentState) -> Literal["review_result", "analyze_intent", "generate_sql"]:
        error = state.get("error_message", "")
        if not error:
            return "review_result"
        if state.get("retry_count", 0) >= 5:
            return "review_result"
        if state.get("retry_count", 0) > 2:
            state["intent_analysis"] = None
            return "analyze_intent"
        return "generate_sql"

    def _route_after_review(self, state: AgentState) -> Literal["refine_answer", "generate_sql", "analyze_intent"]:
        if state.get("review_passed"):
            return "refine_answer"
        if state.get("retry_count", 0) >= 5:
            return "refine_answer"
        if state.get("retry_count", 0) > 2:
            state["intent_analysis"] = None
            return "analyze_intent"
        return "generate_sql"

    def get_graph(self):
        if self.graph is None:
            self.graph = self.build_graph()
        return self.graph
```

### 2. 创建 prompts/*.md 文件

**src/prompts/intent_analysis_prompt.md**:
```markdown
You are an expert SQL query analyzer for a cost allocation database.

Your task is to analyze user's natural language query and determine:
1. Query intent (query, aggregate, filter, join, etc.)
2. Tables involved
3. Columns needed
4. Filter conditions
5. Grouping requirements
6. Aggregation functions needed
7. Sorting requirements
8. Limit requirements

## Database Context
{excel_summary}

## User Query
{user_query}

## Instructions
1. Analyze user query to understand intent
2. Identify which tables are relevant to query
3. Extract any filters, groupings, aggregations mentioned
4. Determine query type (simple, aggregate, join, complex)
5. Provide confidence score (0.0 to 1.0) for your analysis

## Output Format
Return a JSON object with following structure:
{
  "intent_type": "string",
  "confidence": 0.0,
  "entities": [
    {"type": "table", "value": "table_name"},
    {"type": "column", "value": "column_name"}
  ],
  "query_type": "simple|aggregate|join|complex",
  "filters": [
    {"column": "col_name", "value": "val", "operator": "="}
  ],
  "groupings": ["col1", "col2"],
  "aggregations": [
    {"column": "col_name", "function": "SUM|COUNT|AVG|MAX|MIN"}
  ],
  "sort_order": {"column": "col_name", "direction": "ASC|DESC"},
  "limit": null,
  "explanation": "Brief explanation of analysis"
}
```

### 3. 更新 src/prompts/__init__.py

```python
"""Prompt Templates"""

import os
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent

def load_prompt(filename: str) -> str:
    """Load prompt from markdown file"""
    prompt_file = PROMPTS_DIR / filename
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8")

# Load all prompts
INTENT_ANALYSIS_PROMPT = load_prompt("intent_analysis_prompt.md")
SQL_GENERATION_PROMPT = load_prompt("sql_generation_prompt.md")
SQL_VALIDATION_PROMPT = load_prompt("sql_validation_prompt.md")
RESULT_REVIEW_PROMPT = load_prompt("result_review_prompt.md")
ANSWER_REFINEMENT_PROMPT = load_prompt("answer_refinement_prompt.md")

def render_prompt(template: str, **kwargs) -> str:
    """Render prompt template with variables"""
    result = template
    for key, value in kwargs.items():
        placeholder = f"{{{key}}}"
        result = result.replace(placeholder, str(value))
    return result
```

### 4. 更新 src/agents/intent_analysis_agent.py

```python
"""意图分析 Agent"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage

from core.schemas import IntentAnalysisResult
from core.data_sources.context_provider import get_data_source_context_provider
from core.metadata import resolve_table_names

from prompts import INTENT_ANALYSIS_PROMPT, render_prompt
from agents.llm import get_llm

if TYPE_CHECKING:
    from graph.graph import AgentState

def analyze_intent_node(state: "AgentState") -> "AgentState":
    """意图分析节点 - 通过 DataSourceContextProvider 获取数据源上下文"""
    
    try:
        user_query = state.get("user_query", "")
        if not user_query:
            for msg in reversed(state.get("messages", [])):
                if isinstance(msg, HumanMessage):
                    user_query = msg.content
                    break
        
        table_names = state.get("table_names") or resolve_table_names(
            user_query, state.get("intent_analysis")
        )
        state["table_names"] = table_names
        
        context_provider = get_data_source_context_provider()
        
        try:
            excel_summary = context_provider.get_data_source_context(table_names)
        except Exception as e:
            excel_summary = f"Cannot get data source schema: {e}. Please infer fields from user query."
        
        error_context = state.get("error_message", "")
        
        additional_instruction = ""
        if error_context:
            additional_instruction = (
                f"\n\nLast attempt failed, error: {error_context}."
                "\nPlease check user query carefully and extract missing parameters."
            )
        
        prompt = (
            render_prompt(
                INTENT_ANALYSIS_PROMPT,
                excel_summary=excel_summary,
                user_query=user_query,
            )
            + additional_instruction
        )
        
        llm = get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        state["intent_analysis"] = response
        
        return state
    except Exception as e:
        state["error_message"] = f"Intent analysis node error: {str(e)}"
        return state
```

## 五、修改优先级时间表

| 阶段 | 任务 | 优先级 | 预计时间 |
|-------|------|--------|---------|
| Phase 1 | 工作流迁移 | 高 | 2小时 |
| Phase 2 | Prompt模板分离 | 高 | 1小时 |
| Phase 3 | 数据源适配 | 中 | 3小时 |
| Phase 4 | Web服务集成 | 中 | 4小时 |
| Phase 5 | 工具系统完善 | 中 | 2小时 |
| Phase 6 | 知识库系统 | 低 | 3小时 |
| Phase 7 | 业务文档迁移 | 低 | 1小时 |

**总计**: 约16小时

## 六、测试验证

修改完成后，需要进行的测试：

1. **单元测试**: 运行所有现有单元测试
2. **集成测试**: 测试完整工作流
3. **LLM交互测试**: 验证prompt模板正确加载
4. **API测试**: 测试FastAPI接口
5. **前端测试**: 验证Web界面正常工作

## 七、风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 导入路径破坏 | Agent节点无法工作 | 逐步迁移，保持向后兼容 |
| Prompt模板丢失 | LLM调用失败 | 验证所有md文件存在 |
| 数据源兼容性 | 现有连接失败 | 保留现有管理器，添加新数据源 |
| 依赖冲突 | 项目无法启动 | 仔细管理pyproject.toml |

## 八、回滚计划

如果修改导致严重问题：

1. 保留原有代码在备份目录
2. 使用git进行版本控制
3. 分阶段修改，每个阶段都可以独立回滚
4. 保留原有测试套件验证功能

## 九、总结

建议采用渐进式改造策略：
1. 先完成Phase 1和Phase 2（核心架构）
2. 验证基本功能正常
3. 再逐步添加Phase 3-7（扩展功能）

这样可以确保核心功能稳定的前提下，逐步扩展和完善系统。
