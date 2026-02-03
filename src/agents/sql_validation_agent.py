"""SQL 验证 Agent - 使用依赖注入"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage

from src.core.data_sources.context_provider import get_data_source_context_provider
from src.core.llm import get_llm
from src.prompts.manager import SQL_VALIDATION_PROMPT, render_prompt_template
from src.core.metadata import get_sql_generation_rules
 
# from sqlserver import get_schema_columns_info


if TYPE_CHECKING:
    from workflow.graph import AgentState


def validate_sql_node(state: AgentState) -> AgentState:
    """SQL 验证节点 - 通过 DataSourceContextProvider 获取数据源信息"""
    

    try:
        sql = state.get("sql_query", "")
        context_provider = get_data_source_context_provider()

        if sql.strip().startswith("{") and "tool_call" in sql:
            state["sql_valid"] = True
            state["error_message"] = ""
            return state

        if not sql or sql.strip() == "":
            state["error_message"] = "Code validation failed: SQL query cannot be empty."
            state["sql_valid"] = False
            return state

        forbidden_keywords = [
            "delete",
            "drop",
            "insert",
            "update",
            "replace",
            "alter",
            "create",
            "truncate",
            "exec(",
            "eval(",
            "__import__",
            "open(",
            "write(",
            "system(",
            "os.",
            "sys.",
        ]
        sql_upper = sql.upper()
        for keyword in forbidden_keywords:
            if keyword in sql:
                state["error_message"] = (
                    f"Code validation failed: contains forbidden keyword '{keyword}'."
                    "Please use read-only SELECT syntax only."
                )
                state["sql_valid"] = False
                return state

        if context_provider.is_excel_mode():
            state["sql_valid"] = True
            state["error_message"] = ""
            return state

        # columns_info = get_schema_columns_info(state.get("table_names"))
        # Use context provider to get schema info for SQL mode (Postgres)
        columns_info = context_provider.get_data_source_context(state.get("table_names"))

        data_source_type = state.get("data_source_type") or "postgresql"
        if context_provider.is_excel_mode():
            data_source_type = "excel"
        elif context_provider.is_sql_server_mode():
            data_source_type = "sqlserver"

        skill = state.get("skill")
        sql_rules = get_sql_generation_rules(data_source_type, skill=skill)

        prompt = render_prompt_template(
            SQL_VALIDATION_PROMPT,
            database_context=columns_info,
            sql_query=sql,
            extra_rule=f"""
            重要校验规则：
            {sql_rules}
            3. 语法错误/字段错误/非 SELECT 语法 => INVALID；
            4. 仅返回【VALID】或【INVALID + 原因】。
            """,
        )

        llm = state.get("llm") or get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        result = response.content.strip().upper()

        if "INVALID" in result:
            state["error_message"] = f"Code validation failed: {response.content.strip()}"
            state["sql_valid"] = False
            return state

        state["sql_valid"] = True
        state["error_message"] = ""
        return state
    except Exception as e:
        state["error_message"] = f"validate_sql_node error: {str(e)}"
        return state
