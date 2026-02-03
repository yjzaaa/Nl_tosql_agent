"""
系统健康检查测试套件

包含端到端工作流测试，支持交互式人在回路确认。
"""

import os
import sys
import pytest
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


class InteractiveInput:
    """
    交互式输入管理器

    用于在测试中处理用户在回路的确认操作。
    """

    def __init__(self, enabled: bool = True):
        """
        初始化交互式输入管理器

        参数:
            enabled: 是否启用交互模式
        """
        self.enabled = enabled
        self.auto_responses = {}  # 自动响应缓存

    def set_auto_response(self, node_name: str, response: str):
        """
        设置节点的自动响应

        参数:
            node_name: 节点名称
            response: 响应类型（accept/edit/respond）
        """
        self.auto_responses[node_name] = response

    def ask_confirmation(self, sql_query: str) -> dict:
        """
        询问用户确认

        参数:
            sql_query: 待确认的 SQL 查询

        返回:
            用户响应字典
        """
        if not self.enabled:
            # 非交互模式，返回 accept
            return {"action": "accept", "args": {"sql_query": sql_query}}

        print("\n" + "=" * 60)
        print("SQL 执行需要您的确认")
        print("=" * 60)
        print(f"\nSQL 查询:\n{sql_query}\n")
        print("请选择操作:")
        print("  [a] 接受 - 执行此 SQL")
        print("  [e] 编辑 - 修改后执行")
        print("  [r] 拒绝 - 不执行，直接返回")
        print("  [s] 跳过 - 对后续 SQL 全部接受")
        print("  [q] 退出测试")
        print("\n请输入选项 (a/e/r/s/q): ", end="")

        choice = input().strip().lower()

        if choice == "q":
            print("\n用户选择退出测试")
            sys.exit(0)

        if choice == "s":
            print("\n已切换到自动接受模式")
            self.enabled = False
            return {"action": "accept", "args": {"sql_query": sql_query}}

        if choice == "a":
            return {"action": "accept", "args": {"sql_query": sql_query}}

        if choice == "e":
            print("\n请输入修改后的 SQL (直接回车使用原SQL):")
            edited_sql = input().strip()
            if not edited_sql:
                edited_sql = sql_query
            return {"action": "edit", "args": {"sql_query": edited_sql}}

        if choice == "r":
            print("\n请输入拒绝原因或反馈:")
            feedback = input().strip()
            return {"action": "respond", "args": feedback}

        # 默认接受
        print("\n无效选项，默认接受")
        return {"action": "accept", "args": {"sql_query": sql_query}}


# 全局交互输入管理器
interactive_input = InteractiveInput(enabled=True)


def check_data_source_config():
    """
    检查数据源配置状态

    返回:
        配置状态信息字典
    """
    config = get_config()
    manager = get_data_source_manager()

    status = {
        "config_type": config.data_source.type if config and hasattr(config, 'data_source') else "unknown",
        "available_strategies": manager.list_available_strategies(),
        "current_strategy": manager.get_strategy_name(),
        "sql_server_available": manager.sql_server_available,
        "excel_file_paths": {},
    }

    # 检查 Excel 文件配置
    if config and hasattr(config, 'data_source') and hasattr(config.data_source, 'excel'):
        excel_config = config.data_source.excel
        excel_paths = getattr(excel_config, 'file_paths', {}) or {}
        status["excel_file_paths"] = excel_paths
        
        # 检查 Excel 文件是否存在
        valid_excel_files = []
        empty_excel_files = []

        for name, path in excel_paths.items():
            if path and os.path.exists(path):
                valid_excel_files.append(name)
            elif path:
                empty_excel_files.append((name, "文件不存在"))
            else:
                empty_excel_files.append((name, "路径为空"))

        status["valid_excel_files"] = valid_excel_files
        status["empty_excel_files"] = empty_excel_files
    else:
        status["valid_excel_files"] = []
        status["empty_excel_files"] = []

    return status


def print_config_status(status):
    """打印数据源配置状态"""
    print("\n" + "=" * 60)
    print("数据源配置状态检查")
    print("=" * 60)
    print(f"\n配置类型: {status['config_type']}")
    print(f"可用策略: {status['available_strategies']}")
    print(f"当前策略: {status['current_strategy']}")
    print(f"SQL Server 可用: {status['sql_server_available']}")

    print("\nExcel 文件配置:")
    if status["valid_excel_files"]:
        print("  ✓ 有效文件:")
        for name in status["valid_excel_files"]:
            print(f"    - {name}")
    if status["empty_excel_files"]:
        print("  ✗ 未配置/无效文件:")
        for name, reason in status["empty_excel_files"]:
            print(f"    - {name}: {reason}")

    print("\n" + "=" * 60)


class TestSystemHealth:
    """系统健康检查测试套件"""

    def test_end_to_end_workflow(self, interactive: bool = True):
        """
        测试端到端工作流

        参数:
            interactive: 是否启用交互模式（支持人在回路确认）
        """
        logger.info("\n🔍 测试端到端工作流...")

        # 设置交互模式
        interactive_input.enabled = interactive

        # 检查数据源配置
        status = check_data_source_config()
        print_config_status(status)

        # 警告：如果没有可用数据源
        if not status["available_strategies"]:
            print("\n⚠️ 错误: 没有可用的数据源策略！")
            print("请检查配置：")
            print("  1. 如果使用 SQL Server，请确保数据库连接配置正确")
            print("  2. 如果使用 Excel，请在 config.yaml 中填入正确的文件路径")
            return

        # 如果当前策略的 SQL Server 不可用，尝试切换
        if status["current_strategy"] == "sqlserver" and not status["sql_server_available"]:
            print("\n⚠️ SQL Server 不可用，尝试使用其他数据源...")

            # 尝试使用 Excel
            if status["valid_excel_files"]:
                print("  → 切换到 Excel 数据源")
                manager = get_data_source_manager()
                manager.set_strategy("excel")
            else:
                print("\n⚠️ 没有有效的 Excel 文件配置，测试可能失败")

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

            # 测试查询 - 可根据需要修改
            query = "26财年采购的预算费用和25财年实际数比，变化是什么？"

            inputs = {
                "messages": [HumanMessage(content=query)],
                "user_query": query,
                "skill_name": "cost_allocation",
            }

            logger.info(f"User Query: {query}")

            if interactive:
                print("\n" + "=" * 60)
                print("交互模式已启用 - 将在 SQL 执行前询问确认")
                print("=" * 60)

            final_state = None
            node_timings = {}
            human_confirmed = None

            try:
                async for event in graph.astream(inputs, config={"recursion_limit": 15}):
                    for key, value in event.items():
                        start_ts = time.perf_counter()
                        final_state = value

                        # 检查是否需要人在回路确认
                        if key == "sql_execution" or key == "execute_sql":
                            sql = value.get("sql_query", "")
                            if sql and not human_confirmed:
                                # 获取用户确认
                                if interactive_input.enabled:
                                    response = interactive_input.ask_confirmation(sql)
                                    human_confirmed = response

                                    if response["action"] == "accept":
                                        logger.info("用户接受执行 SQL")
                                        value["human_confirmed"] = True
                                        value["human_confirmation_action"] = "accept"
                                    elif response["action"] == "edit":
                                        logger.info(f"用户编辑 SQL: {response['args']}")
                                        value["human_confirmed"] = True
                                        value["human_confirmation_action"] = "edit"
                                        value["sql_query"] = response["args"]["sql_query"]
                                    elif response["action"] == "respond":
                                        logger.info("用户拒绝执行")
                                        value["human_confirmed"] = False
                                        value["human_confirmation_action"] = "respond"
                                        value["human_feedback"] = response["args"]
                                else:
                                    # 自动模式
                                    value["human_confirmed"] = True
                                    value["human_confirmation_action"] = "accept"

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

                        elif key == "sql_validation":
                            valid = value.get("sql_valid")
                            error = value.get("error_message")
                            status = "success" if valid else "error"
                            logger.info(
                                f"SQL Validation: Valid: {valid}, Status: {status}, Error: {error if error else ''}"
                            )

                        elif key == "execute_sql" or key == "sql_execution":
                            # 显示人在回路状态
                            if value.get("human_confirmation_action"):
                                action = value.get("human_confirmation_action")
                                logger.info(f"Human-in-the-loop Action: {action}")

                            # 检查执行结果
                            result = value.get("execution_result")
                            error_msg = value.get("error_message", "")

                            if error_msg and "不支持的文件格式" in error_msg:
                                print("\n" + "=" * 60)
                                print("⚠️ 数据源配置错误")
                                print("=" * 60)
                                print("\n错误: Excel 文件路径为空或文件不存在")
                                print("\n解决方案:")
                                print("  1. 如果使用 SQL Server，确保数据库连接配置正确")
                                print("  2. 如果使用 Excel，在 config.yaml 中配置 file_paths:")
                                print("     例如:")
                                print("     excel:")
                                print("       file_paths:")
                                print("         cost_database: 'data/cost_database.xlsx'")
                                print("=" * 60)
                                print()

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


def run_interactive_test():
    """
    运行交互式测试

    直接运行此函数可启动交互式测试，支持人在回路确认。
    """
    print("\n" + "=" * 60)
    print("NL to SQL 交互式测试")
    print("=" * 60)
    print("\n此测试将在 SQL 执行前询问您的确认。")
    print("您可以选择：")
    print("  a - 接受执行")
    print("  e - 编辑后执行")
    print("  r - 拒绝执行")
    print("  s - 切换到自动模式")
    print("  q - 退出测试")
    print("\n" + "=" * 60)

    test_suite = TestSystemHealth()
    test_suite.test_end_to_end_workflow(interactive=True)


if __name__ == "__main__":
    import sys

    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # 自动模式
        print("\n运行自动模式测试（不询问确认）...")
        test_suite = TestSystemHealth()
        test_suite.test_end_to_end_workflow(interactive=False)
    else:
        # 交互模式
        run_interactive_test()
                                                                               