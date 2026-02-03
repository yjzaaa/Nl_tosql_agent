# 人在回路（Human-in-the-Loop）功能设计文档

## 1. 设计目标

按照 `HumanInTheLoopMiddleware` 规范，将人在回路功能以最小改动集成到现有工作流中：
- 使用 `create_agent` 模式封装 `execute_sql_node`
- 通过中间件的 `wrap_tool_call` 机制实现人类确认
- 通过 graph 状态传递人在回路相关配置

## 2. 架构设计

### 2.1 组件关系

```
Graph Workflow
    │
    ├── validate_sql (生成 SQL)
    │
    └── execute_sql_agent (create_agent 封装的执行节点)
            │
            └── HumanInTheLoopMiddleware (中间件)
                    │
                    └── wrap_tool_call (拦截工具调用)
                            │
                            └── interrupt (暂停等待用户确认)
```

### 2.2 核心组件

#### 2.2.1 HumanInTheLoopMiddleware

根据文档，Middleware 需要实现：
- `wrap_tool_call`: 拦截工具调用，在执行前暂停等待用户确认
- `interrupt_on`: 配置哪些工具需要确认

```python
from langgraph.middleware import HumanInTheLoopMiddleware

human_interrupt_middleware = HumanInTheLoopMiddleware(
    interrupt_on={
        "execute_sql": HumanInterruptConfig(
            allow_accept=True,
            allow_edit=True,
            allow_respond=True,
            description=lambda state: f"确认执行 SQL:\n{state.get('sql_query', '')}"
        )
    },
    description_prefix="SQL 执行需要您的确认"
)
```

#### 2.2.2 execute_sql_agent 使用 create_agent 封装

使用 `create_agent` 将 `execute_sql_node` 转换为可被中间件拦截的 Agent：

```python
from langchain_core.tools import create_tool
from src.tools.add_human_in_the_loop import add_human_in_the_loop

# 原始执行函数
def execute_sql_fn(sql_query: str, data_source_type: str = "excel") -> str:
    """执行 SQL 查询并返回结果"""
    context_provider = get_data_source_context_provider()
    df = context_provider.execute_sql(sql_query, data_source_type=data_source_type)
    return df.to_string(index=False)

# 使用 create_tool 转换为 BaseTool
execute_sql_tool = create_tool(
    execute_sql_fn,
    name="execute_sql",
    description="执行 SQL 查询"
)

# 使用 add_human_in_the_loop 包装，添加人在回路支持
execute_sql_tool_with_human_loop = add_human_in_the_loop(
    execute_sql_tool,
    interrupt_config=HumanInterruptConfig(
        allow_accept=True,
        allow_edit=True,
        allow_respond=True,
    )
)
```

#### 2.2.3 状态传递

在 `AgentState` 中添加人在回路相关状态：

```python
class AgentState(TypedDict):
    # ... 现有字段 ...

    # 人在回路相关状态
    human_approved: Annotated[Optional[bool], lambda x, y: y]
    human_action: Annotated[Optional[str], lambda x, y: y]  # accept, edit, respond
    human_edited_sql: Annotated[Optional[str], lambda x, y: y]
    human_feedback: Annotated[Optional[str], lambda x, y: y]
```

## 3. 实现步骤

### 3.1 修改 execute_sql_agent.py

```python
"""SQL 执行 Agent - 使用 create_agent + 人在回路"""

from __future__ import annotations
from typing import TYPE_CHECKING, Annotated, Any, Dict, List, Optional

from langchain_core.tools import create_tool, BaseTool
from langgraph.types import interrupt
from langgraph.agents.interrupt import HumanInterruptConfig, HumanInterrupt

from src.tools.add_human_in_the_loop import add_human_in_the_loop
from src.core.data_sources.context_provider import get_data_source_context_provider

if TYPE_CHECKING:
    from workflow.graph import AgentState


def execute_sql_fn(sql_query: str, data_source_type: str = "excel") -> str:
    """执行 SQL 查询"""
    context_provider = get_data_source_context_provider()
    df = context_provider.execute_sql(sql_query, data_source_type=data_source_type)
    return df.to_string(index=False)


def create_execute_sql_tool() -> BaseTool:
    """创建带人在回路支持的 SQL 执行工具"""
    base_tool = create_tool(
        execute_sql_fn,
        name="execute_sql",
        description="执行 SQL 查询并返回结果"
    )

    return add_human_in_the_loop(
        base_tool,
        interrupt_config=HumanInterruptConfig(
            allow_accept=True,
            allow_edit=True,
            allow_respond=True,
            description="SQL execution requires your confirmation"
        )
    )


def execute_sql_node(state: AgentState) -> AgentState:
    """SQL 执行节点 - 通过工具调用执行"""
    sql = state.get("sql_query", "")

    # 清理 SQL
    cleaned_sql = sql.strip()
    if cleaned_sql.lower().startswith("sql"):
        cleaned_sql = cleaned_sql[3:].lstrip()
    if cleaned_sql.startswith("```"):
        cleaned_sql = cleaned_sql.strip("`").lstrip()

    # SQL Server LIMIT 转换
    ds_type = state.get("data_source_type")
    context_provider = get_data_source_context_provider()
    if (ds_type == "sqlserver") or context_provider.is_sql_server_mode():
        import re
        match = re.search(r"\blimit\s+(\d+)\s*;?\s*$", cleaned_sql, re.IGNORECASE)
        if match and "top" not in cleaned_sql.lower():
            limit_n = match.group(1)
            cleaned_sql = re.sub(
                r"^\s*select\s+",
                f"SELECT TOP {limit_n} ",
                cleaned_sql,
                flags=re.IGNORECASE,
            )
            cleaned_sql = re.sub(
                r"\blimit\s+\d+\s*;?\s*$",
                "",
                cleaned_sql,
                flags=re.IGNORECASE,
            ).strip()

    try:
        result = execute_sql_fn(cleaned_sql, ds_type)
        state["execution_result"] = result
        state["error_message"] = ""
    except Exception as e:
        state["error_message"] = f"执行出错: {str(e)}"

    return state
```

### 3.2 修改 graph.py

```python
"""Graph-based Workflow Definition - 带人在回路"""

from langgraph.middleware import HumanInTheLoopMiddleware
from src.graph.middleware import SQLExecutionConfirmMiddleware

class GraphWorkflow:
    def build_graph(self) -> StateGraph:
        # ... 添加节点 ...

        # 添加中间件
        human_interrupt_middleware = HumanInTheLoopMiddleware(
            interrupt_on={
                "execute_sql": HumanInterruptConfig(
                    allow_accept=True,
                    allow_edit=True,
                    allow_respond=True,
                    description=lambda state: f"确认执行以下 SQL:\n\n{state.get('sql_query', '')}"
                )
            },
            description_prefix="SQL 执行需要您的确认"
        )

        return workflow.compile(middleware=[human_interrupt_middleware])
```

### 3.3 修改 add_human_in_the_loop.py

确保与 LangGraph 1.0.7 兼容：

```python
"""添加人在回路支持的工具包装器"""

from typing import Callable
from langchain_core.tools import BaseTool, tool as create_tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt
from langgraph.agents.interrupt import HumanInterruptConfig, HumanInterrupt


def add_human_in_the_loop(
    tool: Callable | BaseTool,
    *,
    interrupt_config: HumanInterruptConfig = None,
) -> BaseTool:
    """Wrap a tool to support human-in-the-loop review."""
    if not isinstance(tool, BaseTool):
        tool = create_tool(tool)

    if interrupt_config is None:
        interrupt_config = HumanInterruptConfig(
            allow_accept=True,
            allow_edit=True,
            allow_respond=True,
        )

    @create_tool(
        tool.name,
        description=tool.description,
        args_schema=tool.args_schema
    )
    def call_tool_with_interrupt(config: RunnableConfig, **tool_input):
        request: HumanInterrupt = {
            "action_request": {
                "action": tool.name,
                "args": tool_input
            },
            "config": interrupt_config,
            "description": "Please review the tool call"
        }

        response = interrupt([request])[0]

        if response["type"] == "accept":
            tool_response = tool.invoke(tool_input, config)
        elif response["type"] == "edit":
            tool_input = response["args"]["args"]
            tool_response = tool.invoke(tool_input, config)
        elif response["type"] == "response":
            tool_response = response["args"]
        else:
            raise ValueError(f"Unsupported interrupt response type: {response['type']}")

        return tool_response

    return call_tool_with_interrupt
```

## 4. 工作流状态变更

### 4.1 正常流程

```
validate_sql (sql_valid=True)
    ↓
execute_sql (工具被 HumanInTheLoopMiddleware 拦截)
    ↓
interrupt() 暂停，发送确认请求给用户
    ↓
用户选择 accept/edit/respond
    ↓
继续执行 execute_sql_node
    ↓
review_result
```

### 4.2 用户操作

| 操作 | 行为 |
|------|------|
| accept | 执行 SQL，返回结果 |
| edit | 修改参数后重新执行 |
| respond | 直接返回用户反馈，不执行 SQL |

## 5. 状态传递

通过 graph 的 `state` 传递人在回路信息：

```python
# 中间件接收的状态
state = {
    "sql_query": "SELECT * FROM users",
    "human_approved": True,
    "human_action": "accept",
    # ...
}

# 响应结果
response = {
    "action": "accept",  # or "edit", "respond"
    "args": {
        "sql_query": "SELECT * FROM users WHERE id=1"  # edited query
    }
}
```

## 6. 注意事项

1. **中间件顺序**: `HumanInTheLoopMiddleware` 应该在其他中间件之后
2. **checkpointer**: 必须配置 checkpointer 以保存中断状态
3. **工具名称**: `interrupt_on` 中的工具名称必须与 `create_tool` 创建的名称完全匹配
4. **返回值**: `interrupt()` 返回用户的选择，需要正确处理

## 7. 测试用例

```python
def test_human_approval_flow():
    """测试用户批准流程"""
    workflow = GraphWorkflow()
    graph = workflow.get_graph()

    inputs = {
        "sql_query": "SELECT * FROM users",
        "human_approved": True,
        "human_action": "accept",
    }

    # 执行应该被中断，等待用户确认
    for event in graph.stream(inputs):
        # 验证 interrupt 被调用
        pass


def test_human_edit_flow():
    """测试用户编辑 SQL 流程"""
    workflow = GraphWorkflow()
    graph = workflow.get_graph()

    inputs = {
        "sql_query": "SELECT * FROM users",
        "human_action": "edit",
        "human_edited_sql": "SELECT id, name FROM users LIMIT 10",
    }

    # 执行编辑后的 SQL
    pass
```
