"""基于图的工作流定义 - NL to SQL 智能查询助手

工作流流程:
用户问题 → 选择技能 → 意图分析 → 加载上下文 → 生成SQL → 校验SQL → 执行SQL(ReAct Agent) → 审查结果 → 精炼答案 → 结束
"""

from langchain_core.messages.base import BaseMessage
from typing import Annotated, Any, Dict, List, Literal, TypedDict, Optional
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from src.config.logger_interface import get_logger
from src.agents.load_context_agent import load_context_node
from src.agents.intent_analysis_agent import analyze_intent_node
from src.agents.sql_generation_agent import generate_sql_node
from src.agents.sql_execution_agent import (
    sql_validation_node,
    sql_execution_node,
    create_validate_sql_tool,
    create_execute_sql_tool,
)
from src.agents.result_review_agent import review_result_node
from src.agents.refine_answer_agent import refine_answer_node
from src.skills.middleware.skill_middleware import select_skill_node
from langgraph.checkpoint.memory import MemorySaver

logger = get_logger("graph")


class AgentState(TypedDict):
    """智能体状态 - 定义工作流中传递的状态数据"""

    # 基础信息
    trace_id: Annotated[Optional[str], lambda x, y: y]  # 追踪ID
    messages: Annotated[List[BaseMessage], add_messages]  # 消息历史

    # 用户查询
    user_query: Annotated[Optional[str], lambda x, y: y]  # 用户原始问题

    # 意图分析
    intent_analysis: Annotated[Any, lambda x, y: y]  # 意图分析结果

    # SQL 生成与执行
    sql_query: Annotated[Optional[str], lambda x, y: y]  # 生成的SQL语句
    sql_valid: Annotated[bool, lambda x, y: y]  # SQL是否校验通过
    execution_result: Annotated[Optional[str], lambda x, y: y]  # SQL执行结果
    execution_data: Annotated[Optional[List[Dict[str, Any]]], lambda x, y: y]  # 执行返回的数据

    # 结果审查
    review_passed: Annotated[Optional[bool], lambda x, y: y]  # 结果是否通过审查
    review_message: Annotated[Optional[str], lambda x, y: y]  # 审查消息

    # 数据源信息
    table_names: Annotated[Optional[List[str]], lambda x, y: y]  # 涉及的表名列表
    data_source_type: Annotated[Optional[str], lambda x, y: y]  # 数据源类型
    data_source_schema: Annotated[Optional[Dict[str, Any]], lambda x, y: y]  # 数据源模式

    # 错误与重试
    error_message: Annotated[Optional[str], lambda x, y: y]  # 错误信息
    retry_count: Annotated[Optional[int], lambda x, y: y]  # 重试次数

    # 图表配置
    chart_config: Annotated[Optional[Dict[str, Any]], lambda x, y: y]  # 图表配置

    # 技能上下文
    skill_context: Annotated[Optional[Dict[str, Any]], lambda x, y: y]  # 技能上下文
    skill_selected_by: Annotated[Optional[str], lambda x, y: y]  # 技能选择方式
    skill_confidence: Annotated[Optional[float], lambda x, y: y]  # 技能选择置信度

    # 人在回路相关状态
    human_confirmed: Annotated[Optional[bool], lambda x, y: y]  # 用户是否确认
    human_confirmation_action: Annotated[Optional[str], lambda x, y: y]  # 用户操作类型
    human_feedback: Annotated[Optional[str], lambda x, y: y]  # 用户反馈
    human_edited_sql: Annotated[Optional[str], lambda x, y: y]  # 用户编辑后的SQL


class GraphWorkflow:
    """基于图的工作流 - 管理整个查询流程"""

    def __init__(self):
        """初始化工作流"""
        self.graph = None
        sel

    def build_graph(self) -> StateGraph:
        """构建工作流图"""
        workflow = StateGraph(AgentState)

        # ========== 核心节点 ==========

        # 1. 技能选择节点 - 根据用户问题选择合适的技能
        workflow.add_node("select_skill", select_skill_node)

        # 2. 意图分析节点 - 分析用户的查询意图
        workflow.add_node("analyze_intent", analyze_intent_node)

        # 3. 上下文加载节点 - 加载数据源上下文
        workflow.add_node("load_context", load_context_node)

        # 4. SQL生成节点 - 根据意图生成SQL语句
        workflow.add_node("generate_sql", generate_sql_node)

        # 5. SQL校验节点 - 校验SQL安全性
        workflow.add_node("sql_validation", sql_validation_node)

        # 6. SQL执行节点 - ReAct Agent 模式执行SQL（带人在回路）
        workflow.add_node("sql_execution", sql_execution_node)

        # 7. 结果审查节点 - 审查执行结果
        workflow.add_node("review_result", review_result_node)

        # 8. 答案精炼节点 - 生成最终答案
        workflow.add_node("refine_answer", refine_answer_node)

        # ========== 设置入口点 ==========
        workflow.set_entry_point("select_skill")

        # ========== 设置边（节点之间的连接） ==========

        workflow.add_edge("select_skill", "analyze_intent")  # 选择技能 → 分析意图
        workflow.add_edge("analyze_intent", "load_context")  # 分析意图 → 加载上下文
        workflow.add_edge("load_context", "generate_sql")    # 加载上下文 → 生成SQL
        workflow.add_edge("generate_sql", "sql_validation")  # 生成SQL → 校验SQL
        workflow.add_edge("sql_validation", "sql_execution") # 校验SQL → 执行SQL
        workflow.add_edge("sql_execution", "review_result")  # 执行SQL → 审查结果
        workflow.add_edge("refine_answer", END)              # 精炼答案 → 结束

        # ========== 条件边（根据状态决定下一步） ==========

        # SQL校验后的路由
        workflow.add_conditional_edges(
            "sql_validation",
            self._route_after_validation,
            {
                "sql_execution": "sql_execution",  # 校验通过，执行SQL
                "generate_sql": "generate_sql",     # 校验失败，重试生成
                "refine_answer": "refine_answer",   # 重试次数过多，直接生成答案
            },
        )

        # 结果审查后的路由
        workflow.add_conditional_edges(
            "review_result",
            self._route_after_review,
            {
                "refine_answer": "refine_answer",   # 审查通过，精炼答案
                "generate_sql": "generate_sql",     # 审查失败，重试生成
                "analyze_intent": "analyze_intent", # 多次失败，重新分析意图
            },
        )

        return workflow.compile(checkpointer=MemorySaver())

    def _route_after_validation(self, state: AgentState) -> Literal["sql_execution", "generate_sql", "refine_answer"]:
        """
        SQL校验后的路由逻辑

        Args:
            state: 当前状态

        Returns:
            下一个节点名称
        """
        # 校验通过，执行SQL
        if state.get("sql_valid"):
            return "sql_execution"

        # 重试次数超过3次，放弃执行直接生成答案
        if state.get("retry_count", 0) >= 3:
            return "refine_answer"

        # 否则重新生成SQL
        return "generate_sql"

    def _route_after_review(self, state: AgentState) -> Literal["refine_answer", "generate_sql", "analyze_intent"]:
        """
        结果审查后的路由逻辑

        Args:
            state: 当前状态

        Returns:
            下一个节点名称
        """
        # 审查通过，精炼答案
        if state.get("review_passed"):
            return "refine_answer"

        # 重试次数超过3次，放弃直接生成答案
        if state.get("retry_count", 0) >= 3:
            return "refine_answer"

        # 重试次数大于2次，重新分析意图
        if state.get("retry_count", 0) > 2:
            state["intent_analysis"] = None
            return "analyze_intent"

        # 否则重新生成SQL
        return "generate_sql"

    def get_graph(self):
        """获取构建好的图"""
        if self.graph is None:
            self.graph = self.build_graph()
        return self.graph


