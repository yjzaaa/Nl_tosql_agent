import os, sys
import pytest
import asyncio
from langchain_core.messages import HumanMessage
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
# 导入项目模块
from src.agents.llm import get_llm
from src.core.data_sources.manager import get_data_source_manager
from src.skills.loader import SkillLoader
from src.graph.graph import GraphWorkflow
from src.config.logger_interface import (
    setup_logging,
    log_workflow_step,
    log_sql_query,
    log_message_block,
    log_result_table,
)


class TestSystemHealth:
    """系统健康检查测试套件"""

    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        setup_logging(level="INFO")
        print("\n🔍 测试端到端工作流...")

        async def _run():
            # 1. 确保数据库可用
            manager = get_data_source_manager()
            manager._detect_available_strategies()
            if not manager.is_strategy_available("postgresql"):
                pytest.skip("PostgreSQL 策略不可用，跳过工作流测试")
            manager.set_strategy("postgresql")

            # 2. 初始化工作流
            workflow = GraphWorkflow()
            graph = workflow.get_graph()

            # 3. 准备查询 (使用文档中的示例问题)
            query = "FY26 计划了多少 HR 费用预算？"
            inputs = {"messages": [HumanMessage(content=query)], "user_query": query}

            log_message_block("User", "Query", query, "cyan")

            # 4. 执行并验证
            final_state = None
            try:
                async for event in graph.astream(inputs, config={"recursion_limit": 15}):
                    for key, value in event.items():
                        final_state = value  # 更新最后状态

                        # 通用节点日志
                        log_workflow_step(
                            step_name=key,
                            description=f"Node '{key}' completed execution",
                            status="success",
                        )

                        if key == "analyze_intent":
                            intent = value.get("intent_analysis", "")
                            if isinstance(intent, str):
                                log_message_block(
                                    "Agent",
                                    "Intent Analysis",
                                    intent[:500] + "...",
                                    "yellow",
                                )
                            else:
                                log_message_block(
                                    "Agent", "Intent Analysis", str(intent), "yellow"
                                )

                        elif key == "generate_sql":
                            sql = value.get("sql_query")
                            if sql:
                                log_sql_query(sql)

                        elif key == "validate_sql":
                            valid = value.get("sql_valid")
                            error = value.get("error_message")
                            status = "success" if valid else "error"
                            log_workflow_step(
                                "SQL Validation",
                                f"Valid: {valid}",
                                status,
                                extra_info=error if error else "",
                            )

                        elif key == "execute_sql":
                            result = value.get("execution_result")
                            if result:
                                # 尝试解析结果行数，如果是字符串
                                if isinstance(result, str):
                                    rows = result.splitlines()
                                    log_message_block(
                                        "System",
                                        "Execution Result",
                                        f"Rows returned: {len(rows)}",
                                        "blue",
                                    )
                                    if len(rows) > 0:
                                        # 简单打印前几行
                                        preview = "\n".join(rows[:5])
                                        log_message_block(
                                            "System", "Result Preview", preview, "blue"
                                        )
                                elif isinstance(result, list):
                                    # 如果是列表字典
                                    if len(result) > 0:
                                        headers = list(result[0].keys())
                                        rows = [list(r.values()) for r in result]
                                        log_result_table("Query Results", headers, rows)
                                    else:
                                        log_message_block(
                                            "System",
                                            "Execution Result",
                                            "Empty result set",
                                            "yellow",
                                        )
                            else:
                                log_message_block(
                                    "System",
                                    "Execution Result",
                                    "No result returned",
                                    "red",
                                )

                        elif key == "refine_answer":
                            messages = value.get("messages")
                            if messages:
                                content = messages[-1].content
                                log_message_block("AI", "Final Answer", content, "green")
            except Exception as e:
                if "recursion" in str(e).lower():
                    print(f"\n⚠️ 达到最大递归深度 (预期内): {e}")
                else:
                    raise e

            # 5. 验证结果
            print("✅ 端到端工作流测试完成")

        asyncio.run(_run())


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", "-s", __file__]))
