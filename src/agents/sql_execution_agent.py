"""SQL Execution Agent - ReAct 模式 + 人在回路中间件

将 SQL 校验和执行分离：
- sql_validation_node: 独立校验节点
- sql_execution_node: ReAct Agent 模式，仅包含 execute_sql 工具
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional
from pydantic import BaseModel

from langchain_core.tools import BaseTool, tool as create_tool
from langchain_core.messages import HumanMessage
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from src.core.data_sources.context_provider import get_data_source_context_provider
from src.core.llm import get_llm
from src.prompts.manager import SQL_VALIDATION_PROMPT, render_prompt_template
from src.core.metadata import get_sql_generation_rules


if TYPE_CHECKING:
    from workflow.graph import AgentState


class ValidateSqlResult(BaseModel):
    """SQL 校验结果"""
    valid: bool
    error_message: Optional[str] = None


class ExecuteSqlResult(BaseModel):
    """SQL 执行结果"""
    success: bool
    result: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


def _clean_sql_query(sql_query: str) -> str:
    """清理 SQL 查询字符串"""
    cleaned = sql_query.strip()
    if cleaned.lower().startswith("sql"):
        cleaned = cleaned[3:].lstrip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").lstrip()
    return cleaned


def _convert_limit_to_top(sql_query: str, data_source_type: str) -> str:
    """将 LIMIT 子句转换为 SQL Server 的 TOP"""
    if data_source_type != "sqlserver":
        return sql_query

    import re

    context_provider = get_data_source_context_provider()
    if not context_provider.is_sql_server_mode():
        return sql_query

    match = re.search(r"\blimit\s+(\d+)\s*;?\s*$", sql_query, re.IGNORECASE)
    if match and "top" not in sql_query.lower():
        limit_n = match.group(1)
        sql_query = re.sub(
            r"^\s*select\s+",
            f"SELECT TOP {limit_n} ",
            sql_query,
            flags=re.IGNORECASE,
        )
        sql_query = re.sub(
            r"\blimit\s+\d+\s*;?\s*$",
            "",
            sql_query,
            flags=re.IGNORECASE,
        ).strip()

    return sql_query


def validate_sql_impl(sql_query: str, data_source_type: str = "excel", skill: Any = None) -> ValidateSqlResult:
    """
    校验 SQL 查询的安全性

    Args:
        sql_query: 待校验的 SQL 查询
        data_source_type: 数据源类型
        skill: 技能上下文

    Returns:
        ValidateSqlResult 校验结果
    """
    try:
        cleaned_sql = _clean_sql_query(sql_query)

        if not cleaned_sql or cleaned_sql.strip() == "":
            return ValidateSqlResult(
                valid=False,
                error_message="SQL query cannot be empty."
            )

        forbidden_keywords = [
            "delete", "drop", "insert", "update", "replace", "alter",
            "create", "truncate", "exec(", "eval(", "__import__",
            "open(", "write(", "system(", "os.", "sys.",
        ]

        sql_upper = cleaned_sql.upper()
        for keyword in forbidden_keywords:
            if keyword in sql_upper:
                return ValidateSqlResult(
                    valid=False,
                    error_message=f"Contains forbidden keyword '{keyword}'. Please use read-only SELECT syntax only."
                )

        context_provider = get_data_source_context_provider()

        if context_provider.is_excel_mode():
            return ValidateSqlResult(valid=True)

        columns_info = context_provider.get_data_source_context(
            table_names=[],
            skill=skill
        )

        sql_rules = get_sql_generation_rules(data_source_type, skill=skill)

        prompt = render_prompt_template(
            SQL_VALIDATION_PROMPT,
            database_context=columns_info,
            sql_query=cleaned_sql,
            extra_rule="""
            Important validation rules:
            1. Only allow SELECT queries (read-only)
            2. Syntax errors, field errors, or non-SELECT syntax => INVALID
            3. Return only 【VALID】 or 【INVALID + reason】
            """,
        )

        llm = get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        result = response.content.strip().upper()

        if "INVALID" in result:
            return ValidateSqlResult(
                valid=False,
                error_message=f"Validation failed: {response.content.strip()}"
            )

        return ValidateSqlResult(valid=True)

    except Exception as e:
        return ValidateSqlResult(
            valid=False,
            error_message=f"Validation error: {str(e)}"
        )


def execute_sql_impl(sql_query: str, data_source_type: str = "excel") -> ExecuteSqlResult:
    """
    执行 SQL 查询

    Args:
        sql_query: 待执行的 SQL 查询
        data_source_type: 数据源类型

    Returns:
        ExecuteSqlResult 执行结果
    """
    try:
        cleaned_sql = _clean_sql_query(sql_query)
        cleaned_sql = _convert_limit_to_top(cleaned_sql, data_source_type)

        context_provider = get_data_source_context_provider()
        df = context_provider.execute_sql(cleaned_sql, data_source_type=data_source_type)

        return ExecuteSqlResult(
            success=True,
            result=df.to_string(index=False),
            data=df.to_dict(orient="records")
        )
    except Exception as e:
        return ExecuteSqlResult(
            success=False,
            error=str(e)
        )


# ==================== 工具定义 ====================

def create_validate_sql_tool() -> BaseTool:
    """创建 SQL 校验工具"""
    def validate_sql_fn(sql_query: str, data_source_type: str = "excel") -> str:
        """校验 SQL 查询的安全性和正确性"""
        result = validate_sql_impl(sql_query, data_source_type)
        if result.valid:
            return "VALID"
        else:
            return f"INVALID: {result.error_message}"

    base_tool = create_tool(
        validate_sql_fn,
        description="Validate SQL query for safety and correctness. Returns VALID or INVALID with reason."
    )

    return base_tool


def create_execute_sql_tool(data_source_type: str = "excel") -> BaseTool:
    """创建 SQL 执行工具"""
    def execute_sql_fn(sql_query: str) -> str:
        """执行 SQL 查询并返回结果"""
        result = execute_sql_impl(sql_query, data_source_type)
        if result.success:
            return result.result or ""
        else:
            return f"Error: {result.error}"

    base_tool = create_tool(
        execute_sql_fn,
        name="execute_sql",
        description="Execute a SQL query against the configured data source."
    )

    return base_tool


# ==================== ReAct Agent ====================

def create_sql_execution_react_agent():
    """
    创建 SQL 执行的 ReAct Agent

    该 Agent 仅包含 execute_sql 工具，负责执行已校验的 SQL 查询
    """
    from langchain.agents import create_agent
    

    llm = get_llm()

    # 仅包含执行工具
    tools = [
        create_execute_sql_tool(),
    ]

    agent = create_agent(
        llm,
        tools,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "execute_sql": {"allowed_decisions": ["approve", "reject"]}
                },
                description_prefix="SQL execution pending approval.",
            )
        ],
        checkpointer=InMemorySaver(),
        system_prompt="""You are a SQL execution agent. Your job is to execute SQL queries safely.

You have access to one tool:
- execute_sql: Execute a SQL query against the configured data source

Before execution, you must wait for human confirmation. The user will review the SQL and:
- Accept: Proceed with execution
- Edit: Modify the SQL and then execute
- Respond: Provide feedback without execution

Workflow:
1. Present the SQL query to the user for confirmation
2. Wait for user action (accept/edit/respond)
3. Execute the query after confirmation

Important:
- Only execute queries that have been validated
- Report any errors clearly
- Present results in a readable format
""",
    )

    return agent


# ==================== 节点函数 ====================

def sql_validation_node(state: AgentState) -> AgentState:
    """
    SQL 校验节点 - 独立校验 SQL 安全性

    此节点完成以下功能：
    1. 检查 SQL 是否包含危险关键词
    2. 校验 SQL 语法正确性
    """
    sql = state.get("sql_query", "")
    ds_type = state.get("data_source_type", "excel")
    skill = state.get("skill")

    result = validate_sql_impl(sql, ds_type, skill)

    state["sql_valid"] = result.valid
    state["error_message"] = result.error_message or ""

    return state


def sql_execution_node(state: AgentState) -> AgentState:
    """
    SQL 执行节点 - ReAct Agent 模式

    此节点使用 ReAct Agent 调用 execute_sql 工具，
    执行前会触发人在回路确认。

    注意：SQL 校验应在独立的 sql_validation_node 中完成
    """
    sql = state.get("sql_query", "")
    ds_type = state.get("data_source_type", "excel")
    table_names = state.get("table_names", [])
    skill = state.get("skill")
    agent = create_sql_execution_react_agent()

    try:
        result = agent.invoke(
            {
                "sql_query": sql,
                "data_source_type": ds_type,
                "table_names": table_names,
            },
            config={"configurable": {"thread_id": state.get("trace_id") or "default"}},
        )

        agent_response = result.get("output", "")

        if "Error:" in agent_response:
            state["execution_result"] = ""
            state["error_message"] = agent_response
        else:
            state["execution_result"] = agent_response
            state["error_message"] = ""

        state["retry_count"] = state.get("retry_count", 0) + 1

    except Exception as e:
        state["error_message"] = f"Agent execution error: {str(e)}"
        state["sql_valid"] = False

    return state
