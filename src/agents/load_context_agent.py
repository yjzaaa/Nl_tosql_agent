"""
上下文加载 Agent - 使用依赖注入

本模块负责根据用户查询和技能上下文加载数据源相关信息，
识别需要查询的表名并获取表结构信息。
"""

from __future__ import annotations

import json  # JSON 解析库
import uuid  # UUID 生成库
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage  # 人类消息类型

from src.core.data_sources.context_provider import get_data_source_context_provider  # 数据源上下文提供者
from src.core.llm import get_llm  # LLM 工厂函数

if TYPE_CHECKING:
    from src.graph.graph import AgentState  # 工作流状态类型


def load_context_node(state: AgentState) -> AgentState:
    """
    上下文加载节点 - 根据用户查询加载数据源上下文

    本节点完成以下功能：
    1. 根据用户查询识别需要访问的数据表
    2. 加载数据源上下文和表结构信息
    3. 为后续 SQL 生成提供数据源信息

    参数:
        state: 当前工作流状态

    返回:
        更新后的工作流状态，包含表名列表和数据源模式
    """
    # 从状态中获取必要信息
    # 技能上下文，用于理解业务逻辑
    skill_context = state.get("skill_context") or {}
    # LLM 实例，优先使用状态中保存的，否则使用全局默认
    llm = state.get("llm") or get_llm()
    # 用户原始查询
    user_query = state.get("user_query", "")
    # 重试次数，用于跟踪当前是第几次尝试
    retry_count = state.get("retry_count", 0) or 0

    # 生成追踪 ID，用于日志和问题排查
    if not state.get("trace_id"):
        state["trace_id"] = str(uuid.uuid4())

    # 构建提示词，要求 LLM 识别需要加载的表
    prompt = (
        "你是一个数据上下文加载助手。请根据用户问题与技能上下文识别需要加载的表名。\n\n"
        "要求：仅返回 JSON 数组，每个元素包含 table_name 与 fields(字段名列表)。\n\n"
        f"用户问题:\n{user_query}\n\n"
        f"技能上下文(JSON):\n{json.dumps(skill_context, ensure_ascii=False, indent=2)}\n"
    )

    # 调用 LLM 获取表名列表
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.replace("```json", "").replace("```", "").strip()

    # 解析 LLM 返回的 JSON 结果
    try:
        schema_json = json.loads(content)
        # 确保解析结果是数组类型
        if not isinstance(schema_json, list):
            schema_json = []
    except Exception as e:
        # JSON 解析失败，设置错误信息
        schema_json = []
        state["error_message"] = f"Failed to parse schema JSON: {e}"

    # 提取表名列表
    state["table_names"] = [
        table.get("table_name")
        for table in schema_json
        if isinstance(table, dict) and table.get("table_name")
    ]

    # 获取数据源上下文提供者
    context_provider = get_data_source_context_provider()
    # 检测可用数据源
    context_provider.detect_sources(state.get("table_names", []))
    # 获取数据源上下文（表结构信息）
    schema_text = context_provider.get_data_source_context(state.get("table_names", []))
    # 保存数据源模式到状态
    state["data_source_schema"] = schema_text

    # 根据实际数据源设置 data_source_type
    if context_provider.is_sql_server_mode():
        state["data_source_type"] = "sqlserver"
    elif context_provider.is_excel_mode():
        state["data_source_type"] = "excel"
    else:
        state["data_source_type"] = "postgresql"

    # 更新状态中的其他字段
    state["user_query"] = user_query
    state["retry_count"] = retry_count
    state["error_message"] = state.get("error_message", "")

    return state
