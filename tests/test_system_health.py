import os, sys
import pytest
import asyncio
import sys
import asyncio
import time
from pathlib import Path

import pytest
from langchain_core.messages import HumanMessage

sys.path.append(str(Path(__file__).parent.parent))

from src.core.data_sources.manager import get_data_source_manager
from src.workflow.skill_aware import get_skill_workflow
from src.config.settings import get_config
from src.config.logger_interface import get_logger, setup_logging
setup_logging(level="INFO")
logger = get_logger("test_system_health")


class TestSystemHealth:
    """系统健康检查测试套件"""
    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        logger.info("\n🔍 测试端到端工作流...")

        async def _run():
            config = get_config()
            data_source_type = config.data_source.type

            try:
                manager = get_data_source_manager()
                manager._detect_available_strategies()
            except ValueError as e:
                pytest.skip(f"数据源策略不可用，跳过工作流测试: {e}")

            if data_source_type == "auto":
                manager.set_strategy("auto")
            else:
                if not manager.is_strategy_available(data_source_type):
                    pytest.skip(f"{data_source_type} 策略不可用，跳过工作流测试")
                manager.set_strategy(data_source_type)

            workflow = get_skill_workflow("cost_allocation")
            graph = workflow.get_graph()

            # query = "FY26 计划了多少 HR 费用预算？"
            # query ="25财年实际分摊给CT的IT费用是多少？"
            # query = "预算 vs 实际对比，IT Allocation 近3个月趋势分析"
            query = "26财年采购的预算费用和25财年实际数比，变化是什么？"
            inputs = {
                "messages": [HumanMessage(content=query)],
                "user_query": query,
                "skill_name": "cost_allocation",
            }

            logger.info(f"User Query: {query}")

            final_state = None
            node_timings = {}
            try:
                async for event in graph.astream(inputs, config={"recursion_limit": 15}):
                    for key, value in event.items():
                        start_ts = time.perf_counter()
                        final_state = value

                        if value.get("error_message"):
                            logger.info(f"System Error: {value['error_message']}")

                        logger.info(f"Node '{key}' completed execution: success")

                        if key == "analyze_intent":
                            intent = value.get("intent_analysis", "")
                            if isinstance(intent, str):
                                logger.info(f"Agent Intent Analysis: {intent[:500]}...")

                        elif key == "generate_sql":
                            sql = value.get("sql_query")
                            if sql:
                                logger.info(f"SQL Query:\n{sql}")

                        elif key == "validate_sql":
                            valid = value.get("sql_valid")
                            error = value.get("error_message")
                            status = "success" if valid else "error"
                            logger.info(
                                f"SQL Validation: Valid: {valid}, Status: {status}, Error: {error if error else ''}"
                            )

                        elif key == "execute_sql":
                            result = value.get("execution_result")
                            if result:
                                if isinstance(result, str):
                                    rows = result.splitlines()
                                    logger.info(
                                        f"System Execution Result: Rows returned: {len(rows)}"
                                    )
                                    if rows:
                                        preview = "\n".join(rows[:5])
                                        logger.info(
                                            f"System Result Preview: {preview}"
                                        )
                                elif isinstance(result, list):
                                    if result:
                                        headers = list(result[0].keys())
                                        logger.info(
                                            f"Query Results (rows={len(result)}): {headers}"
                                        )
                                    else:
                                        logger.info(
                                            "System Execution Result: Empty result set"
                                        )
                            else:
                                logger.info("System Execution Result: No result returned")

                        elif key == "refine_answer":
                            messages = value.get("messages")
                            if messages:
                                content = messages[-1].content
                                logger.info(f"AI Final Answer: {content}")

                        elapsed = time.perf_counter() - start_ts
                        node_timings.setdefault(key, 0.0)
                        node_timings[key] += elapsed
            except Exception as e:
                if "recursion" in str(e).lower():
                    print(f"\n⚠️ 达到最大递归深度 (预期内): {e}")
                else:
                    raise e

        asyncio.run(_run())


if __name__ == "__main__":
    test_suite = TestSystemHealth()
    test_suite.test_end_to_end_workflow()
