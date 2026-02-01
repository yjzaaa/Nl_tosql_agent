"""NL to SQL Agent Main Entry Point - Graph-based Version"""

import argparse
import logging
from typing import Optional
from pathlib import Path

from src.config.logger_interface import get_logger
from src.skills.loader import SkillLoader, Skill
from src.graph.graph import GraphWorkflow, AgentState

logger = get_logger("main")


class NLToSQLAgent:
    def __init__(
        self, skill_path: Optional[str] = None, skill_name: Optional[str] = None
    ):
        self.skill_path = Path(skill_path) if skill_path else Path.cwd() / "skills"
        self.skill_name = skill_name or "nl-to-sql-agent"
        self.skill: Optional[GraphWorkflow] = None
        self.workflow: Optional[GraphWorkflow] = None

        self._initialize()

    def _initialize(self):
        loader = SkillLoader(str(self.skill_path))
        self.skill = loader.load_skill(self.skill_name)

        if self.skill:
            logger.info(f"Loaded skill: {self.skill.name} v{self.skill.version}")
            self.workflow = GraphWorkflow()
        else:
            logger.warning(f"Skill {self.skill_name} not found, using default workflow")
            self.workflow = GraphWorkflow()

    def query(self, user_query: str, **kwargs) -> dict:
        """Execute a natural language query"""

        initial_state: AgentState = {
            "trace_id": kwargs.get("trace_id"),
            "messages": [],
            "user_query": user_query,
            "intent_analysis": None,
            "sql_query": None,
            "sql_valid": False,
            "execution_result": None,
            "review_passed": None,
            "review_message": None,
            "table_names": None,
            "data_source_type": kwargs.get("data_source_type", "excel"),
            "error_message": None,
            "retry_count": 0,
            "skill": self.skill,
            "skill_name": self.skill_name,
            **kwargs,
        }

        try:
            graph = self.workflow.get_graph()

            # Extract config parameters from kwargs if present
            config = {}
            if "recursion_limit" in kwargs:
                config["recursion_limit"] = kwargs["recursion_limit"]

            final_state = graph.invoke(initial_state, config=config)

            return {
                "success": final_state.get("review_passed", False)
                or final_state.get("sql_valid", False),
                "query": user_query,
                "sql": final_state.get("sql_query"),
                "result": final_state.get("execution_result"),
                "answer": final_state.get("review_message"),
                "error": final_state.get("error_message"),
                "trace_id": final_state.get("trace_id"),
                "skill": self.skill_name,
            }

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {
                "success": False,
                "query": user_query,
                "error": str(e),
                "skill": self.skill_name,
            }

    def reload_skill(self, skill_name: Optional[str] = None):
        """Reload skill configuration"""
        if skill_name:
            self.skill_name = skill_name

        loader = SkillLoader(str(self.skill_path))
        self.skill = loader.load_skill(self.skill_name)

        if self.skill:
            # GraphWorkflow does not have set_skill method, so we just log
            logger.info(f"Reloaded skill: {self.skill.name}")
            # Reinitialize workflow with new skill
            self.workflow = GraphWorkflow()
            logger.info(f"Reinitialized workflow with skill: {self.skill.name}")
        else:
            logger.warning(f"Skill {self.skill_name} not found during reload")

    def list_available_skills(self) -> list:
        """List available skills"""
        loader = SkillLoader(str(self.skill_path))
        return loader.list_available_skills()


def main():
    parser = argparse.ArgumentParser(
        description="NL to SQL Agent - Skill-Aware Version"
    )
    parser.add_argument("--skill-path", type=str, help="Path to skills directory")
    parser.add_argument(
        "--skill", type=str, default="nl-to-sql-agent", help="Skill name to use"
    )
    parser.add_argument("--query", type=str, help="Query to execute")
    parser.add_argument(
        "--list-skills", action="store_true", help="List available skills"
    )

    args = parser.parse_args()

    agent = NLToSQLAgent(skill_path=args.skill_path, skill_name=args.skill)

    if args.list_skills:
        skills = agent.list_available_skills()
        print("Available skills:")
        for skill in skills:
            print(f"  - {skill}")
        return

    if args.query:
        result = agent.query(args.query)
        print(f"\nQuery: {result['query']}")
        print(f"SQL: {result.get('sql', 'N/A')}")
        print(f"Result: {result.get('result', 'N/A')}")
        if result.get("error"):
            print(f"Error: {result['error']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
