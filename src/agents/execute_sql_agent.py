"""SQL 执行 Agent - 使用依赖注入"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.core.data_sources.context_provider import get_data_source_context_provider
from src.tools.common import ALL_TOOLS
 


if TYPE_CHECKING:
    from workflow.graph import AgentState


def execute_sql_node(state: AgentState) -> AgentState:
    """SQL 执行节点 - 通过 DataSourceContextProvider 执行查询"""
    sql = state.get("sql_query", "")
    context_provider = get_data_source_context_provider()

    if sql.strip().startswith("{") and "tool_call" in sql:
        import json

        try:
            tool_data = json.loads(sql)
            tool_name = tool_data.get("tool_call")
            params = tool_data.get("parameters", {})

            target_tool = None
            for tool in ALL_TOOLS:
                if tool.name == tool_name:
                    target_tool = tool
                    break

            if target_tool:
                result = target_tool.invoke(params)

                if isinstance(result, dict) and "error" in result and result["error"]:
                    state["error_message"] = f"工具执行错误: {result['error']}"
                    return state

                state["execution_result"] = str(result)
                state["error_message"] = ""
                return state
            else:
                state["error_message"] = f"未找到工具: {tool_name}"
                return state

        except json.JSONDecodeError:
            pass
        except Exception as e:
            state["error_message"] = f"工具调用解析失败: {str(e)}"
            return state

    try:
        cleaned_sql = sql.strip()
        if cleaned_sql.lower().startswith("sql"):
            cleaned_sql = cleaned_sql[3:].lstrip()
        if cleaned_sql.startswith("```"):
            cleaned_sql = cleaned_sql.strip("`").lstrip()

        ds_type = state.get("data_source_type")
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

        df = context_provider.execute_sql(cleaned_sql, data_source_type=ds_type)
        state["execution_result"] = df.to_string(index=False)
        state["execution_data"] = df.to_dict(orient="records")
        state["error_message"] = ""

    except Exception as e:
        state["error_message"] = f"执行出错: {str(e)}"

    return state
