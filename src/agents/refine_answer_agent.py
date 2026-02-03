"""
答案精炼 Agent - 使用依赖注入

本模块负责根据执行结果生成最终的回答，
将技术性的查询结果转换为用户友好的答案。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage  # 人类消息类型

from src.core.llm import get_llm  # LLM 工厂函数
from src.prompts.manager import ANSWER_REFINEMENT_PROMPT, render_prompt_template  # 答案精炼提示模板

if TYPE_CHECKING:
    from workflow.graph import AgentState  # 工作流状态类型


def refine_answer_node(state: AgentState) -> AgentState:
    """
    答案精炼节点 - 根据执行结果生成最终回答

    本节点完成以下功能：
    1. 将 SQL 执行结果转换为用户友好的回答
    2. 总结关键信息和洞察
    3. 如果结果包含错误，仅解释错误原因

    参数:
        state: 当前工作流状态

    返回:
        更新后的工作流状态，包含最终回答
    """
    # 从状态中获取必要信息
    user_query = state.get("user_query", "")
    # 如果没有 SQL，使用默认值
    sql = state.get("sql_query", "未生成 SQL")
    # 如果没有执行结果，使用默认值
    execution_result = state.get("execution_result", "无结果")

    # 构建提示词
    prompt = render_prompt_template(
        ANSWER_REFINEMENT_PROMPT,
        user_query=user_query,
        sql_query=sql,
        execution_result=execution_result,
    )

    # 检查执行结果是否包含错误
    # 如果包含错误，添加警告提示，禁止输出数据表格
    if (
        "error" in str(execution_result).lower()
        or "exception" in str(execution_result).lower()
    ):
        prompt += (
            "\n\nSYSTEM WARNING: 检测到执行结果包含错误信息。"
            "你必须停止尝试回答用户的问题数据。**绝对禁止**输出任何数据表格或数值。请仅解释错误原因。"
        )

    # 调用 LLM 生成最终回答
    llm = state.get("llm") or get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])

    # 将回答保存到消息列表
    state["messages"] = [response]

    return state
