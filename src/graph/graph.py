"""Graph-based Workflow Definition"""

from langchain_core.messages.base import BaseMessage
from typing import Annotated, Any, Dict, List, Literal, TypedDict, Optional
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from src.config.logger_interface import get_logger
from src.agents.load_context_agent import load_context_node
from src.agents.intent_analysis_agent import analyze_intent_node
from src.agents.sql_generation_agent import generate_sql_node
from src.agents.sql_validation_agent import validate_sql_node
from src.agents.execute_sql_agent import execute_sql_node
from src.agents.result_review_agent import review_result_node
from src.agents.refine_answer_agent import refine_answer_node
from src.agents.visualization_agent import visualization_node

logger = get_logger("graph")


class AgentState(TypedDict):
    """Agent State"""
    trace_id: Annotated[Optional[str], lambda x, y: y]
    messages: Annotated[List[BaseMessage], add_messages]
    intent_analysis: Annotated[Any, lambda x, y: y]
    user_query: Annotated[Optional[str], lambda x, y: y]
    sql_query: Annotated[Optional[str], lambda x, y: y]
    sql_valid: Annotated[bool, lambda x, y: y]
    execution_result: Annotated[Optional[str], lambda x, y: y]
    execution_data: Annotated[Optional[List[Dict[str, Any]]], lambda x, y: y]  # Added for chart data
    review_passed: Annotated[Optional[bool], lambda x, y: y]
    review_message: Annotated[Optional[str], lambda x, y: y]
    table_names: Annotated[Optional[List[str]], lambda x, y: y]
    data_source_type: Annotated[Optional[str], lambda x, y: y]
    error_message: Annotated[Optional[str], lambda x, y: y]
    retry_count: Annotated[Optional[int], lambda x, y: y]
    chart_config: Annotated[Optional[Dict[str, Any]], lambda x, y: y] # Added for chart config


class GraphWorkflow:
    def __init__(self):
        self.graph = None

    def build_graph(self) -> StateGraph:
        """Build workflow graph"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("load_context", load_context_node)
        workflow.add_node("analyze_intent", analyze_intent_node)
        workflow.add_node("generate_sql", generate_sql_node)
        workflow.add_node("validate_sql", validate_sql_node)
        workflow.add_node("execute_sql", execute_sql_node)
        workflow.add_node("review_result", review_result_node)
        workflow.add_node("refine_answer", refine_answer_node)
        workflow.add_node("visualization", visualization_node)

        # Set entry point
        workflow.set_entry_point("analyze_intent")

        # Add edges
        workflow.add_edge("analyze_intent", "load_context")
        workflow.add_edge("load_context", "generate_sql")
        workflow.add_edge("generate_sql", "validate_sql")
        
        # Conditional edges
        workflow.add_conditional_edges(
            "validate_sql",
            self._route_after_validation,
            {
                "execute_sql": "execute_sql",
                "generate_sql": "generate_sql",
                "refine_answer": "refine_answer",
            },
        )
        workflow.add_conditional_edges(
            "execute_sql",
            self._route_after_execution,
            {
                "review_result": "review_result",
                "generate_sql": "generate_sql",
                "analyze_intent": "analyze_intent",
            },
        )
        workflow.add_conditional_edges(
            "review_result",
            self._route_after_review,
            {
                "refine_answer": "refine_answer",
                "generate_sql": "generate_sql",
                "analyze_intent": "analyze_intent",
            },
        )

        workflow.add_edge("refine_answer", "visualization")
        workflow.add_edge("visualization", END)

        return workflow.compile()

    def _route_after_validation(self, state: AgentState) -> Literal["execute_sql", "generate_sql", "refine_answer"]:
        if state.get("sql_valid"):
            return "execute_sql"
        if state.get("retry_count", 0) >= 5:
            return "refine_answer"
        return "generate_sql"

    def _route_after_execution(self, state: AgentState) -> Literal["review_result", "analyze_intent", "generate_sql"]:
        error = state.get("error_message", "")
        if not error:
            return "review_result"
        if state.get("retry_count", 0) >= 5:
            return "review_result"
        if state.get("retry_count", 0) > 2:
            state["intent_analysis"] = None
            return "analyze_intent"
        return "generate_sql"

    def _route_after_review(self, state: AgentState) -> Literal["refine_answer", "generate_sql", "analyze_intent"]:
        if state.get("review_passed"):
            return "refine_answer"
        if state.get("retry_count", 0) >= 5:
            return "refine_answer"
        if state.get("retry_count", 0) > 2:
            state["intent_analysis"] = None
            return "analyze_intent"
        return "generate_sql"

    def get_graph(self):
        if self.graph is None:
            self.graph = self.build_graph()
        return self.graph
