"""结果审查 Agent - 使用依赖注入"""

from __future__ import annotations

from typing import TYPE_CHECKING

import json
import re
from langchain_core.messages import HumanMessage

# from config.logger_interface import log_workflow_step

from src.core.llm import get_llm
from src.prompts.manager import RESULT_REVIEW_PROMPT, render_prompt_template


if TYPE_CHECKING:
    from workflow.graph import AgentState


def review_result_node(state: AgentState) -> AgentState:
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

        llm = state.get("llm") or get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        decision = response.content.strip()

        cleaned = decision.replace("```json", "").replace("```", "").strip()
        parsed = None
        try:
            parsed = json.loads(cleaned)
        except Exception:
            try:
                match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
            except Exception:
                parsed = None

        if isinstance(parsed, dict) and "passed" in parsed:
            state["review_passed"] = bool(parsed.get("passed"))
            state["review_message"] = parsed.get("refined_answer", "")
            state["error_message"] = "" if state["review_passed"] else cleaned
            return state

        lowered = cleaned.lower()
        if '"passed"' in lowered:
            if '"passed"' in lowered and "true" in lowered:
                state["review_passed"] = True
                state["review_message"] = ""
                state["error_message"] = ""
                return state
            if '"passed"' in lowered and "false" in lowered:
                state["review_passed"] = False
                state["review_message"] = cleaned
                state["error_message"] = cleaned
                return state

        if decision.upper().startswith("PASS"):
            state["review_passed"] = True
            state["review_message"] = ""
            return state

        if decision.upper().startswith("RETRY"):
            state["review_passed"] = False
            state["review_message"] = decision
            state["error_message"] = decision
            return state

        state["review_passed"] = False
        state["review_message"] = f"RETRY: 无法解析审查结果: {decision}"
        state["error_message"] = state["review_message"]
        return state
    except Exception as e:
        state["review_passed"] = False
        state["review_message"] = f"RETRY: 审查节点异常: {str(e)}"
        state["error_message"] = state["review_message"]
        # log_workflow_step("ResultReview", f"审查异常: {e}", "error")
        return state
