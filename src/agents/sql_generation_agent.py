"""SQL 生成 Agent - 使用依赖注入"""

from __future__ import annotations

from typing import TYPE_CHECKING
import json

from langchain_core.messages import HumanMessage, ToolMessage
from src.core.schemas import IntentAnalysisResult
from src.core.data_sources.context_provider import get_data_source_context_provider
from src.tools.common import (
    execute_pandas_query,
    calculate_allocated_costs,
    compare_scenarios,
    compare_allocated_costs,
    analyze_cost_composition,
)

CORE_TOOLS = [
    execute_pandas_query,
    calculate_allocated_costs,
    compare_scenarios,
    compare_allocated_costs,
    analyze_cost_composition,
]

from src.core.llm import get_llm
 
from src.prompts import SQL_GENERATION_PROMPT, render_prompt_template
from src.core.metadata import get_sql_generation_rules

if TYPE_CHECKING:
    from workflow.graph import AgentState


def generate_sql_node(state: AgentState) -> AgentState:
    """SQL 生成节点 - 通过 DataSourceContextProvider 获取数据源上下文，并支持动态加载业务逻辑技能"""
    

    try:
        skill = state.get("skill")
        context_provider = get_data_source_context_provider()

        data_source_context = context_provider.get_data_source_context(
            state.get("table_names", []), skill=skill
        )

        user_query = state.get("user_query", "")
        intent_analysis = state.get("intent_analysis", "")

        if isinstance(intent_analysis, IntentAnalysisResult):
            intent_analysis = intent_analysis.model_dump_json(indent=2)

        error_context = state.get("error_message", "")

        if error_context:
            error_context = (
                f"上一次尝试失败，错误信息：{error_context}。请根据错误修正代码。"
            )

        prompt_template = SQL_GENERATION_PROMPT
        data_source_type = state.get("data_source_type") or "postgresql"
        if context_provider.is_excel_mode():
            data_source_type = "excel"
        elif context_provider.is_sql_server_mode():
            data_source_type = "sqlserver"

        sql_rules = get_sql_generation_rules(data_source_type, skill=skill)
        skill_context = state.get("skill_context", "")
        # 渲染初始 Prompt
        prompt = render_prompt_template(
            prompt_template,
            database_context=data_source_context,
            intent_analysis=intent_analysis,
            user_query=user_query,
            error_context=error_context,
            sql_rules=sql_rules,
            skill_context=skill_context,
        )

        llm = state.get("llm") or get_llm()

        # 定义工具集：仅保留执行工具（代理应返回）
        execution_tools = CORE_TOOLS
        all_tools = execution_tools

        # 绑定工具
        llm_with_tools = llm.bind_tools(all_tools)

        # 初始化消息历史，将 Prompt 作为用户输入
        messages = [HumanMessage(content=prompt)]

        # React 循环逻辑 (LangGraph 风格的简单实现)
        MAX_ITERATIONS = 1
        sql = ""

        for i in range(MAX_ITERATIONS):
            
            response = llm_with_tools.invoke(messages)
            messages.append(response)


            if not response.tool_calls:
                # 无工具调用，直接作为 SQL 代码处理
                sql = (
                    response.content.replace("```python", "").replace("```", "").strip()
                )

                break

            # 处理工具调用
            tool_calls = response.tool_calls
            should_continue = False

            for tool_call in tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                if tool_name in [t.name for t in execution_tools]:
                    # 如果调用了执行工具，这不仅是检索，而是最终的执行计划
                    # 我们将其序列化为 JSON 并作为结果返回，由 execute_sql_node 执行
                    sql = json.dumps(
                        {"tool_call": tool_name, "parameters": tool_args},
                        ensure_ascii=False,
                    )
                    should_continue = False
                    break  # 跳出内层循环

            if not should_continue:
                break  # 跳出外层循环

        else:
            # 如果达到最大迭代次数，使用最后的消息内容
            if not sql and messages:
                sql = (
                    messages[-1]
                    .content.replace("```python", "")
                    .replace("```", "")
                    .strip()
                )


        state["sql_query"] = sql
        state["retry_count"] = state.get("retry_count", 0) + 1
        return state

    except Exception as e:

        state["error_message"] = f"generate_sql节点执行错误。错误详情：{str(e)}"
        state["retry_count"] = state.get("retry_count", 0) + 1
        return state
