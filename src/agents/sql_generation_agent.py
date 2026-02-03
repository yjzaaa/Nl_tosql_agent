"""
SQL 生成 Agent - 使用依赖注入

本模块负责根据用户查询意图和数据源上下文生成 SQL 语句。
支持动态加载业务逻辑技能，根据不同数据源类型生成适配的 SQL。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import json  # JSON 解析库

from langchain_core.messages import HumanMessage, ToolMessage  # 消息类型

from src.core.schemas import IntentAnalysisResult  # 意图分析结果模式
from src.core.data_sources.context_provider import get_data_source_context_provider  # 数据源上下文提供者
from src.tools.common import (
    execute_pandas_query,  # 执行 pandas 查询
    calculate_allocated_costs,  # 计算分摊成本
    compare_scenarios,  # 对比场景
    compare_allocated_costs,  # 对比分摊成本
    analyze_cost_composition,  # 分析成本构成
)

# 核心工具列表 - 用于 ReAct 模式的工具调用
CORE_TOOLS = [
    execute_pandas_query,
    calculate_allocated_costs,
    compare_scenarios,
    compare_allocated_costs,
    analyze_cost_composition,
]

from src.core.llm import get_llm  # LLM 工厂函数

from src.prompts import SQL_GENERATION_PROMPT, render_prompt_template  # SQL 生成提示模板
from src.core.metadata import get_sql_generation_rules  # SQL 生成规则

if TYPE_CHECKING:
    from workflow.graph import AgentState  # 工作流状态类型


def generate_sql_node(state: AgentState) -> AgentState:
    """
    SQL 生成节点 - 根据用户意图和数据源上下文生成 SQL 语句

    本节点完成以下功能：
    1. 获取数据源上下文和表结构信息
    2. 根据意图分析结果生成 SQL
    3. 支持动态加载业务逻辑技能
    4. 处理执行工具调用（ReAct 模式）

    参数:
        state: 当前工作流状态

    返回:
        更新后的工作流状态，包含生成的 SQL 语句
    """
    try:
        # 获取技能对象和数据源上下文提供者
        skill = state.get("skill")
        context_provider = get_data_source_context_provider()

        # 获取数据源上下文（表结构信息）
        data_source_context = context_provider.get_data_source_context(
            state.get("table_names", []), skill=skill
        )

        # 获取用户查询和意图分析结果
        user_query = state.get("user_query", "")
        intent_analysis = state.get("intent_analysis", "")

        # 如果意图分析结果是对象类型，转换为 JSON 字符串
        if isinstance(intent_analysis, IntentAnalysisResult):
            intent_analysis = intent_analysis.model_dump_json(indent=2)

        # 获取错误上下文（如果有）
        error_context = state.get("error_message", "")

        # 如果有错误信息，添加到提示词中
        if error_context:
            error_context = (
                f"上一次尝试失败，错误信息：{error_context}。请根据错误修正代码。"
            )

        # 获取数据源类型
        prompt_template = SQL_GENERATION_PROMPT
        data_source_type = state.get("data_source_type") or "postgresql"
        # 根据上下文提供者判断数据源类型
        if context_provider.is_excel_mode():
            data_source_type = "excel"
        elif context_provider.is_sql_server_mode():
            data_source_type = "sqlserver"

        # 获取 SQL 生成规则（包含数据源特定的语法规则）
        sql_rules = get_sql_generation_rules(data_source_type, skill=skill)
        # 获取技能上下文
        skill_context = state.get("skill_context", "")

        # 渲染提示词模板
        prompt = render_prompt_template(
            prompt_template,
            database_context=data_source_context,
            intent_analysis=intent_analysis,
            user_query=user_query,
            error_context=error_context,
            sql_rules=sql_rules,
            skill_context=skill_context,
        )

        # 获取 LLM 实例
        llm = state.get("llm") or get_llm()

        # 定义工具集 - 仅保留执行工具
        execution_tools = CORE_TOOLS
        all_tools = execution_tools

        # 绑定工具到 LLM
        llm_with_tools = llm.bind_tools(all_tools)

        # 初始化消息历史
        messages = [HumanMessage(content=prompt)]

        # ReAct 循环逻辑
        # 最大迭代次数
        MAX_ITERATIONS = 1
        sql = ""

        for i in range(MAX_ITERATIONS):
            # 调用 LLM 获取响应
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            # 如果没有工具调用，直接作为 SQL 代码处理
            if not response.tool_calls:
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

                # 如果调用了执行工具
                if tool_name in [t.name for t in execution_tools]:
                    # 序列化为 JSON，由 execute_sql_node 执行
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

        # 保存生成的 SQL 到状态
        state["sql_query"] = sql
        # 增加重试计数
        state["retry_count"] = state.get("retry_count", 0) + 1

        return state

    except Exception as e:
        # 捕获异常，设置错误信息
        state["error_message"] = f"generate_sql节点执行错误。错误详情：{str(e)}"
        state["retry_count"] = state.get("retry_count", 0) + 1
        return state
