"""结果审查 Agent - 使用依赖注入"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage

# from config.logger_interface import log_workflow_step

from src.agents.llm import get_llm
from src.prompts.manager import RESULT_REVIEW_PROMPT, render_prompt_template


if TYPE_CHECKING:
    from workflow.graph import AgentState


def review_result_node(state: "AgentState") -> "AgentState":
    """结果审查节点：判断结果是否足以回答问题"""
    try:
        # log_workflow_step("ResultReview", "开始审查结果", "running")

        user_query = state.get("user_query", "")
        sql = state.get("sql_query", "")
        execution_result = state.get("execution_result", "")

        prompt = render_prompt_template(
            RESULT_REVIEW_PROMPT,
            user_query=user_query,
            sql_query=sql,
            execution_result=execution_result,
        )

        llm = get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        decision = response.content.strip()

        if decision.upper().startswith("PASS"):
            state["review_passed"] = True
            state["review_message"] = ""
            # log_workflow_step("ResultReview", "审查通过", "success")
            return state

        if decision.upper().startswith("RETRY"):
            state["review_passed"] = False
            state["review_message"] = decision
            state["error_message"] = decision
            # log_workflow_step("ResultReview", f"需要重试: {decision}", "warning")
            return state

        state["review_passed"] = False
        state["review_message"] = f"RETRY: 无法解析审查结果: {decision}"
        state["error_message"] = state["review_message"]
        # log_workflow_step("ResultReview", f"无法解析审查结果: {decision}", "warning")
        return state
    except Exception as e:
        state["review_passed"] = False
        state["review_message"] = f"RETRY: 审查节点异常: {str(e)}"
        state["error_message"] = state["review_message"]
        # log_workflow_step("ResultReview", f"审查异常: {e}", "error")
        return state
