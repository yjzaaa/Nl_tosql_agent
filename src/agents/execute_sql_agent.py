"""SQL 执行 Agent - 使用 create_agent + 人在回路模式"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Optional

from langchain_core.tools import BaseTool, tool as create_tool
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt

from src.core.data_sources.context_provider import get_data_source_context_provider
from src.tools.add_human_in_the_loop import add_human_in_the_loop, HumanInterruptConfig


if TYPE_CHECKING:
    from workflow.graph import AgentState


def _clean_sql_query(sql_query: str) -> str:
    """Clean SQL query string."""
    cleaned = sql_query.strip()
    if cleaned.lower().startswith("sql"):
        cleaned = cleaned[3:].lstrip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").lstrip()
    return cleaned


def _convert_limit_to_top(sql_query: str, data_source_type: str) -> str:
    """Convert LIMIT clause to TOP for SQL Server."""
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


def execute_sql_impl(sql_query: str, data_source_type: str = "excel") -> Dict[str, Any]:
    """Execute SQL query implementation.

    Args:
        sql_query: The SQL query to execute
        data_source_type: Type of data source (excel, sqlserver, postgresql)

    Returns:
        Dictionary with 'result' or 'error' key
    """
    try:
        cleaned_sql = _clean_sql_query(sql_query)
        cleaned_sql = _convert_limit_to_top(cleaned_sql, data_source_type)

        context_provider = get_data_source_context_provider()
        df = context_provider.execute_sql(cleaned_sql, data_source_type=data_source_type)

        return {
            "result": df.to_string(index=False),
            "data": df.to_dict(orient="records"),
            "success": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }


def execute_sql_fn(sql_query: str, data_source_type: str = "excel") -> str:
    """Execute SQL query function for use with create_tool.

    Args:
        sql_query: The SQL query to execute
        data_source_type: Type of data source

    Returns:
        String representation of results or error
    """
    result = execute_sql_impl(sql_query, data_source_type)
    if result.get("success"):
        return result["result"]
    else:
        return f"Error: {result.get('error')}"


def create_execute_sql_tool(data_source_type: str = "excel") -> BaseTool:
    """Create SQL execution tool with human-in-the-loop support.

    Args:
        data_source_type: Type of data source to use

    Returns:
        BaseTool with human confirmation before execution
    """
    base_tool = create_tool(
        execute_sql_fn,
        description="Execute a SQL query against the configured data source. Requires human confirmation before execution."
    )

    return add_human_in_the_loop(
        base_tool,
        interrupt_config=HumanInterruptConfig(
            allow_accept=True,
            allow_edit=True,
            allow_respond=True,
            description="SQL execution requires your confirmation. Please review the generated SQL before proceeding."
        )
    )




def execute_sql_tool_node(config: RunnableConfig, sql_query: str, data_source_type: str = "excel") -> Dict[str, Any]:
    """SQL 执行工具节点 - 用于 create_agent 模式。

    Args:
        config: RunnableConfig from the graph
        sql_query: SQL query to execute
        data_source_type: Type of data source

    Returns:
        Tool execution result
    """
    result = execute_sql_impl(sql_query, data_source_type)
    return result
