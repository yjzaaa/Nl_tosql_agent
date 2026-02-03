"""
结果审查 Agent - 使用依赖注入

本模块负责审查 SQL 执行结果，判断是否足以回答用户问题。
如果结果不合格，会提供改进建议。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import json  # JSON 解析库
import re  # 正则表达式库

from langchain_core.messages import HumanMessage  # 人类消息类型

from src.core.llm import get_llm  # LLM 工厂函数
from src.prompts.manager import RESULT_REVIEW_PROMPT, render_prompt_template  # 结果审查提示模板

if TYPE_CHECKING:
    from workflow.graph import AgentState  # 工作流状态类型


def review_result_node(state: AgentState) -> AgentState:
    """
    结果审查节点 - 判断执行结果是否足以回答用户问题

    本节点完成以下功能：
    1. 根据用户查询和 SQL 语句审查执行结果
    2. 判断结果是否满足用户需求
    3. 决定是继续使用结果还是需要重试

    参数:
        state: 当前工作流状态

    返回:
        更新后的工作流状态，包含审查结果
    """
    try:
        # 从状态中获取必要信息
        user_query = state.get("user_query", "")
        sql = state.get("sql_query", "")
        execution_result = state.get("execution_result", "")

        # 构建审查提示词
        prompt = render_prompt_template(
            RESULT_REVIEW_PROMPT,
            user_query=user_query,
            sql_query=sql,
            execution_result=execution_result,
        )

        # 调用 LLM 进行结果审查
        llm = state.get("llm") or get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        decision = response.content.strip()

        # 清理响应内容
        cleaned = decision.replace("```json", "").replace("```", "").strip()

        # 尝试解析 JSON 结果
        parsed = None
        try:
            parsed = json.loads(cleaned)
        except Exception:
            # 如果 JSON 解析失败，尝试使用正则表达式提取 JSON
            try:
                match = re.search(r"\{.*\}", cleaned, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
            except Exception:
                parsed = None

        # 如果成功解析 JSON
        if isinstance(parsed, dict) and "passed" in parsed:
            state["review_passed"] = bool(parsed.get("passed"))
            state["review_message"] = parsed.get("refined_answer", "")
            # 如果通过，清空错误信息；否则保存错误信息
            state["error_message"] = "" if state["review_passed"] else cleaned
            return state

        # 检查 passed 字段的字符串值
        lowered = cleaned.lower()
        if '"passed"' in lowered:
            # 检查 passed 是否为 true
            if '"passed"' in lowered and "true" in lowered:
                state["review_passed"] = True
                state["review_message"] = ""
                state["error_message"] = ""
                return state
            # 检查 passed 是否为 false
            if '"passed"' in lowered and "false" in lowered:
                state["review_passed"] = False
                state["review_message"] = cleaned
                state["error_message"] = cleaned
                return state

        # 检查响应是否以 PASS 开头
        if decision.upper().startswith("PASS"):
            state["review_passed"] = True
            state["review_message"] = ""
            return state

        # 检查响应是否以 RETRY 开头
        if decision.upper().startswith("RETRY"):
            state["review_passed"] = False
            state["review_message"] = decision
            state["error_message"] = decision
            return state

        # 无法解析审查结果，标记为需要重试
        state["review_passed"] = False
        state["review_message"] = f"RETRY: 无法解析审查结果: {decision}"
        state["error_message"] = state["review_message"]
        return state

    except Exception as e:
        # 捕获异常，设置错误信息
        state["review_passed"] = False
        state["review_message"] = f"RETRY: 审查节点异常: {str(e)}"
        state["error_message"] = state["review_message"]
        return state
