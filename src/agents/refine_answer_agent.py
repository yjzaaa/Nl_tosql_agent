"""答案精炼 Agent - 使用依赖注入"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage

# from config.logger_interface import log_workflow_step

from src.agents.llm import get_llm
from src.prompts.manager import ANSWER_REFINEMENT_PROMPT, render_prompt_template


if TYPE_CHECKING:
    from workflow.graph import AgentState


def refine_answer_node(state: "AgentState") -> "AgentState":
    """生成最终回答节点"""
    # log_workflow_step("RefineAnswer", "开始生成最终回答", "running")

    user_query = state.get("user_query", "")
    sql = state.get("sql_query", "未生成 SQL")
    execution_result = state.get("execution_result", "无结果")

    prompt = render_prompt_template(
        ANSWER_REFINEMENT_PROMPT,
        user_query=user_query,
        sql_query=sql,
        execution_result=execution_result,
    )

    if (
        "error" in str(execution_result).lower()
        or "exception" in str(execution_result).lower()
    ):
        prompt += (
            "\n\nSYSTEM WARNING: 检测到执行结果包含错误信息。"
            "你必须停止尝试回答用户的问题数据。**绝对禁止**输出任何数据表格或数值。请仅解释错误原因。"
        )
        # log_workflow_step("RefineAnswer", "检测到执行错误，添加警告", "warning")

    llm = get_llm()
    response = llm.invoke([HumanMessage(content=prompt)])
    state["messages"] = [response]

    # log_workflow_step("RefineAnswer", "最终回答生成完成", "success")
    return state
