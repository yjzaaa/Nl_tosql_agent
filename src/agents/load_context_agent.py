"""上下文加载 Agent - 使用依赖注入"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage

from src.core.metadata import resolve_table_names
from src.core.data_sources.context_provider import get_data_source_context_provider


if TYPE_CHECKING:
    from src.graph.graph import AgentState


def load_context_node(state: "AgentState") -> "AgentState":
    """初始化上下文节点 - 通过 DataSourceContextProvider 与数据源交互"""

    messages = state.get("messages", [])
    user_query = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break

    retry_count = state.get("retry_count", 0) or 0

    if not state.get("trace_id"):
        state["trace_id"] = str(uuid.uuid4())

    if not state.get("table_names"):
        state["table_names"] = resolve_table_names(
            user_query, state.get("intent_analysis")
        )

    context_provider = get_data_source_context_provider()
    context_provider.detect_sources(state.get("table_names", []))

    state["user_query"] = user_query
    state["retry_count"] = retry_count
    state["error_message"] = state.get("error_message", "")

    return state
