import asyncio
import os
import pandas as pd
import pytest
import pyodbc
from langchain_core.messages import HumanMessage
from src.graph.graph import GraphWorkflow
from src.core.loader.excel_loader import get_loader
from src.core.data_sources.context_provider import get_data_source_context_provider


# 模拟数据
def setup_mock_data():
    # Reset loader state
    from src.core.loader.excel_loader import reset_loader

    reset_loader()

    loader = get_loader()

    # 1. 模拟主数据 CostDataBase
    data = {
        "Year": ["FY26", "FY26", "FY25", "FY26"],
        "Scenario": ["Budget1", "Budget1", "Actual", "Budget1"],
        "Function": ["HR", "IT", "IT", "Finance"],
        "Amount": [1000, 2000, 1500, 3000],
        "Month": ["Oct", "Nov", "Oct", "Dec"],
        "cost text": ["Training", "Server Maintenance", "Laptop", "Audit"],
        "Allocation Key": ["Headcount", "Usage", "Usage", "Revenue"],
    }
    df = pd.DataFrame(data)

    # 使用 src.core.loader.excel_loader 中的 ExcelLoader
    from src.core.loader.excel_loader import ExcelLoader

    mock_loader = ExcelLoader()
    # Mock internal properties
    mock_loader._df = df
    mock_loader._file_path = "mock_data.xlsx"
    mock_loader._sheet_name = "CostDataBase"

    # 注入上下文
    mock_loader.business_logic_context = """
    ## 业务解释和逻辑
    - FY26 代表 2026 财年
    - Budget1 代表第一次预算
    - Cost text 代表具体的费用项描述
    - Allocation Key 代表分摊给业务部门的依据
    """

    # 注册到 MultiExcelLoader
    loader._tables["mock_id"] = mock_loader
    loader._active_table_id = "mock_id"

    # Mock table info
    from src.core.loader.excel_loader import TableInfo

    loader._table_infos["mock_id"] = TableInfo(
        id="mock_id",
        filename="mock_data.xlsx",
        file_path="mock_data.xlsx",
        sheet_name="CostDataBase",
        total_rows=len(df),
        total_columns=len(df.columns),
    )

    # Ensure context provider is initialized
    provider = get_data_source_context_provider()
    provider._ensure_initialized()

    print("✅ 模拟数据加载完成")


def _has_sqlserver_config() -> bool:
    return bool(
        os.getenv("SQLSERVER_CONNECTION_STRING")
        or (
            (os.getenv("SQLSERVER_HOST") or os.getenv("database_url"))
            and (os.getenv("SQLSERVER_DATABASE") or os.getenv("database_name"))
        )
    )


def test_workflow():
    # Use environment variable to skip if needed, but default to running
    if os.environ.get("SKIP_WORKFLOW_TEST"):
        pytest.skip("Skipping workflow test via env var")

    async def _run():
        # Ensure manager is using postgresql
        from src.core.data_sources.manager import get_data_source_manager

        manager = get_data_source_manager()

        # Force re-detection to ensure env vars are picked up
        manager._detect_available_strategies()

        if not manager.is_strategy_available("postgresql"):
            print(
                "⚠️ PostgreSQL strategy not available. Available:",
                manager.list_available_strategies(),
            )
            pytest.skip("PostgreSQL strategy not available")

        manager.set_strategy("postgresql")
        print(f"✅ Using Data Source: {manager.get_strategy_name()}")

        # Initialize workflow
        workflow = GraphWorkflow()
        graph = workflow.get_graph()

        # 测试问题：包含业务术语和字段查询
        query = "Show me the top 5 records from SSME_FI_InsightBot_CostDataBase"
        print(f"\n🔍 测试问题: {query}")
        print("-" * 50)

        inputs = {"messages": [HumanMessage(content=query)], "user_query": query}

        print("🚀 开始执行工作流...")
        async for event in graph.astream(inputs):
            for key, value in event.items():
                print(f"\n📍 节点: {key}")
                if key == "analyze_intent":
                    intent = value.get("intent_analysis")
                    intent_preview = (
                        intent[:100] if isinstance(intent, str) else str(intent)
                    )
                    print(f"   意图分析: {intent_preview}...")
                elif key == "generate_sql":
                    print(f"   生成 SQL: {value.get('sql_query')}")
                elif key == "validate_sql":
                    valid = value.get("sql_valid")
                    print(f"   验证结果: {'✅ 通过' if valid else '❌ 失败'}")
                    if not valid:
                        print(f"   错误信息: {value.get('error_message')}")
                elif key == "execute_sql":
                    result = value.get("execution_result")
                    if result:
                        preview = str(result)[:200]
                        print(f"   执行结果预览: {preview}...")
                    else:
                        print("   执行结果: None")
                elif key == "refine_answer":
                    messages = value.get("messages", [])
                    if messages:
                        print(f"   最终回答: {messages[-1].content}")

        print("-" * 50)
        print("✅ 测试完成")

    # Run the async test
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(_run())


if __name__ == "__main__":
    test_workflow()
