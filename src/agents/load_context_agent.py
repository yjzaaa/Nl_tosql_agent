"""上下文加载 Agent - 使用依赖注入"""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage

from src.core.data_sources.context_provider import get_data_source_context_provider
from src.core.llm import get_llm


if TYPE_CHECKING:
    from src.graph.graph import AgentState


def load_context_node(state: AgentState) -> AgentState:
    """初始化上下文节点 - 通过 DataSourceContextProvider 与数据源交互"""
    skill_context = state.get("skill_context") or {}
    llm = state.get("llm") or get_llm()
    user_query = state.get("user_query", "")
    retry_count = state.get("retry_count", 0) or 0

    if not state.get("trace_id"):
        state["trace_id"] = str(uuid.uuid4())

    prompt = (
        "你是一个数据上下文加载助手。请根据用户问题与技能上下文识别需要加载的表名。\n\n"
        "要求：仅返回 JSON 数组，每个元素包含 table_name 与 fields(字段名列表)。\n\n"
        f"用户问题:\n{user_query}\n\n"
        f"技能上下文(JSON):\n{json.dumps(skill_context, ensure_ascii=False, indent=2)}\n"
    )

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.replace("```json", "").replace("```", "").strip()

    try:
        schema_json = json.loads(content)
        if not isinstance(schema_json, list):
            schema_json = []
    except Exception as e:
        schema_json = []
        state["error_message"] = f"Failed to parse schema JSON: {e}"

    state["table_names"] = [
        table.get("table_name")
        for table in schema_json
        if isinstance(table, dict) and table.get("table_name")
    ]

    context_provider = get_data_source_context_provider()
    context_provider.detect_sources(state.get("table_names", []))
    schema_text = context_provider.get_data_source_context(state.get("table_names", []))
    state["data_source_schema"] = schema_text

    state["user_query"] = user_query
    state["retry_count"] = retry_count
    state["error_message"] = state.get("error_message", "")

    return state
