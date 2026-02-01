"""意图分析 Agent - 使用依赖注入"""

from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage

from src.core.schemas import IntentAnalysisResult
from src.core.data_sources.context_provider import get_data_source_context_provider
from src.core.metadata import resolve_table_names

from src.prompts.manager import INTENT_ANALYSIS_PROMPT, render_prompt_template
from src.agents.llm import get_llm
from src.config.logger import LoggerManager

if TYPE_CHECKING:
    from workflow.graph import AgentState


def analyze_intent_node(state: "AgentState") -> "AgentState":
    """意图分析节点 - 通过 DataSourceContextProvider 获取数据源上下文"""
    LoggerManager().info("Starting analyze_intent_node")

    try:
        user_query = state.get("user_query", "")
        if not user_query:
            for msg in reversed(state.get("messages", [])):
                if isinstance(msg, HumanMessage):
                    user_query = msg.content
                    break

        skill = state.get("skill")
        skill_metadata = skill.get_metadata() if skill else {}

        table_names = state.get("table_names") or resolve_table_names(
            user_query, state.get("intent_analysis"), skill_metadata
        )
        state["table_names"] = table_names

        context_provider = get_data_source_context_provider()

        try:
            excel_summary = context_provider.get_data_source_context(table_names)
        except Exception as e:
            excel_summary = f"Cannot get data source schema: {e}. Please infer fields from user query."

        error_context = state.get("error_message", "")

        additional_instruction = ""
        if error_context:
            additional_instruction = (
                f"\n\nLast attempt failed, error: {error_context}."
                "\nPlease check the user query carefully and extract missing parameters."
            )

        prompt = (
            render_prompt_template(
                INTENT_ANALYSIS_PROMPT,
                database_context=excel_summary,
                user_query=user_query,
            )
            + additional_instruction
        )

        llm = get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        state["intent_analysis"] = response

        return state
    except Exception as e:
        state["error_message"] = f"Intent analysis node error: {str(e)}"
        return state
