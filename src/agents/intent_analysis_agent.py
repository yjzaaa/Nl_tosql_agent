"""
意图分析 Agent - 使用依赖注入

本模块负责分析用户查询意图，判断是否为数据查询相关问题。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import json  # JSON 解析库

from langchain_core.messages import HumanMessage  # 人类消息类型

from src.prompts.manager import render_prompt_template  # 提示模板渲染
from src.core.llm import get_llm  # LLM 工厂函数
from src.config.logger import LoggerManager  # 日志管理器

if TYPE_CHECKING:
    from workflow.graph import AgentState  # 工作流状态类型


def analyze_intent_node(state: AgentState) -> AgentState:
    """
    意图分析节点 - 判断用户问题是否为数据查询相关

    本节点通过 LLM 分析用户输入，判断问题是否与数据查询/数据分析相关。
    如果 LLM 调用失败，会使用关键词匹配作为后备方案。

    参数:
        state: 当前工作流状态，包含用户查询等信息

    返回:
        更新后的工作流状态，包含意图分析结果
    """
    try:
        # 获取用户查询
        # 优先从 user_query 字段获取，如果为空则从消息历史中查找
        user_query = state.get("user_query", "")
        if not user_query:
            # 遍历消息历史，查找最后一条人类消息
            for msg in reversed(state.get("messages", [])):
                if isinstance(msg, HumanMessage):
                    user_query = msg.content
                    break

        # 构建提示词
        # 渲染提示模板，添加用户查询内容
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

        # 调用 LLM 进行意图分析
        llm = state.get("llm") or get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.strip()

        # 清理响应内容，移除 JSON 代码块标记
        content = content.replace("```json", "").replace("```", "").strip()

        # 解析 LLM 返回的 JSON 结果
        try:
            parsed = json.loads(content)
            state["intent_analysis"] = parsed
        except Exception:
            # JSON 解析失败，使用关键词匹配作为后备方案
            lowered = user_query.lower()
            # 定义数据查询相关关键词
            data_keywords = [
                "查询", "统计", "报表", "数据", "sql", "select",
                "趋势", "对比", "分析"
            ]
            # 检查是否包含任意关键词
            is_data = any(
                key in lowered
                for key in data_keywords
            )
            # 设置意图分析结果
            state["intent_analysis"] = {
                "is_data_query": is_data,
                "reason": "heuristic",  # 使用启发式方法判断
            }

        return state

    except Exception as e:
        # 捕获异常，设置错误信息
        state["error_message"] = f"Intent analysis node error: {str(e)}"
        return state
