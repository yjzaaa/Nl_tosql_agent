"""
可视化 Agent - 使用依赖注入

本模块负责根据执行数据生成图表配置，
为用户提供最佳的数据可视化建议。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Any, List

import json  # JSON 解析库

from langchain_core.messages import HumanMessage  # 人类消息类型

from src.core.llm import get_llm  # LLM 工厂函数
from src.prompts.manager import render_prompt_template  # 提示模板渲染函数

if TYPE_CHECKING:
    from workflow.graph import AgentState  # 工作流状态类型

# 可视化提示模板
# 用于指导 LLM 根据数据和用户查询生成合适的图表配置
VISUALIZATION_PROMPT = """
You are a data visualization expert.

Your task is to recommend the best chart type to visualize the provided data based on the user's query.

## User Query
{user_query}

## Data Sample (First 5 rows)
{data_sample}

## Instructions
1. Analyze the data and user intent.
2. Choose the most appropriate chart type from: bar, line, pie, scatter, area, or table.
3. Determine which columns should be on the X-axis (dimensions) and Y-axis (metrics).
4. Provide a title for the chart.

## Output Format
Return a JSON object with the following structure:
{{
  "chart_type": "bar|line|pie|scatter|area|table",
  "title": "Descriptive Chart Title",
  "config": {{
    "x_axis": "column_name_for_x",
    "y_axis": ["column_name_for_y1", "column_name_for_y2"],
    "series_names": ["Series 1 Name", "Series 2 Name"]
  }},
  "reasoning": "Explanation of why this chart type was chosen"
}}

If the data is not suitable for a chart (e.g., single value or too complex), set "chart_type" to "table".
"""


def visualization_node(state: AgentState) -> AgentState:
    """
    可视化节点 - 根据数据生成图表配置

    本节点完成以下功能：
    1. 分析执行数据的特点
    2. 根据用户查询意图推荐最佳图表类型
    3. 生成图表配置（标题、坐标轴、系列等）

    参数:
        state: 当前工作流状态

    返回:
        更新后的工作流状态，包含图表配置
    """
    # 从状态中获取执行数据
    execution_data = state.get("execution_data")
    if not execution_data:
        # 如果没有数据，直接返回
        return state

    # 获取用户查询
    user_query = state.get("user_query", "")

    # 取前 5 条数据作为样本
    data_sample = execution_data[:5]

    # 构建提示词
    prompt = render_prompt_template(
        VISUALIZATION_PROMPT,
        user_query=user_query,
        data_sample=json.dumps(data_sample, ensure_ascii=False, indent=2)
    )

    # 获取 LLM 实例
    llm = state.get("llm") or get_llm()

    try:
        # 调用 LLM 生成图表配置
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content.replace("```json", "").replace("```", "").strip()

        # 解析图表配置 JSON
        chart_config = json.loads(content)
        state["chart_config"] = chart_config

    except Exception as e:
        # 如果生成失败，设置错误信息（但不中断工作流）
        state["chart_config"] = {"error": str(e)}

    return state
