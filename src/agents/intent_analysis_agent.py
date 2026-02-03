"""意图分析 Agent - 使用依赖注入"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage

import json
from src.prompts.manager import render_prompt_template
from src.core.llm import get_llm
from src.config.logger import LoggerManager

if TYPE_CHECKING:
    from workflow.graph import AgentState


def analyze_intent_node(state: AgentState) -> AgentState:
    """意图分析节点 - 仅判断是否为数据相关问题"""
    try:
        user_query = state.get("user_query", "")
        if not user_query:
            for msg in reversed(state.get("messages", [])):
                if isinstance(msg, HumanMessage):
                    user_query = msg.content
                    break

        prompt = render_prompt_template(
            """
你是一个问题分类器。请判断用户问题是否与数据查询/数据分析相关。

## 用户问题
{user_query}

## 输出要求
仅返回 JSON：
{{"is_data_query": true|false, "reason": "简短原因"}}
""",
            user_query=user_query,
        )

        llm = state.get("llm") or get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        try:
            parsed = json.loads(content)
            state["intent_analysis"] = parsed
        except Exception:
            lowered = user_query.lower()
            is_data = any(
                key in lowered
                for key in ["查询", "统计", "报表", "数据", "sql", "select", "趋势", "对比", "分析"]
            )
            state["intent_analysis"] = {
                "is_data_query": is_data,
                "reason": "heuristic",
            }

        return state
    except Exception as e:
        state["error_message"] = f"Intent analysis node error: {str(e)}"
        return state
