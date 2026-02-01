import asyncio
import os
import sys
# 强制禁用本地代理，解决 Ollama 502 错误
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langchain_core.messages import HumanMessage

from src.graph.graph import GraphWorkflow
from excel_agent.logger import setup_logging, get_logger
from sqlserver import get_schema_context, execute_sql_query
from excel_agent.business_metadata import resolve_table_names
from dotenv import load_dotenv

from langgraph.errors import GraphRecursionError

# 配置日志
setup_logging()
logger = get_logger("analysis_runner")


async def run_analysis():
    load_dotenv()

    # 1. 准备查询
    query = "26财年IT的预算费用和25财年实际数比，变化是什么？"
    logger.info(f"\n🔍 用户问题: {query}")
    logger.info("-" * 50)

    # 2. 打印 SQL Server 表结构摘要（用于确认连接）
    try:
        tables = resolve_table_names(query)
        schema_summary = get_schema_context(tables)
        logger.info("📚 SQL Server Schema Summary:\n" + schema_summary)
    except Exception as e:
        logger.error(f"❌ SQL Server 连接失败: {e}")
        return

    # 3. 可选：执行一个简单的连通性查询
    try:
        ping_df = execute_sql_query("SELECT 1 AS ok")
        logger.info(f"✅ SQL Server 连接成功，测试查询结果: {ping_df.to_dict(orient='records')}")
    except Exception as e:
        logger.error(f"❌ SQL Server 测试查询失败: {e}")
        return

    # 4. 运行工作流
    workflow = GraphWorkflow()
    inputs = {"messages": [HumanMessage(content=query)]}

    logger.info("🚀 开始执行工作流...")
    try:
        async for event in workflow.get_graph().astream(inputs, config={"recursion_limit": 15}):
            for key, value in event.items():
                logger.info("-" * 50 + key + "-" * 50)
                if key == "analyze_intent":
                    if value.get("error_message"):
                        logger.error(
                            f" analyze_intent  执行错误: {value.get('error_message')}"
                        )
                    else:
                        logger.info(f"意图分析: {value.get('intent_analysis')}...")

                elif key == "generate_sql":
                    if value.get("retry_count", 0) > 0:
                        logger.info(f"   (重试次数: {value.get('retry_count')})")
                    if value.get("error_message"):
                        logger.error(
                            f" generate_sql  执行错误: {value.get('error_message')}"
                        )
                    if value.get("sql_query"):
                        logger.info(f"   生成 SQL: {value.get('sql_query')}")

                elif key == "validate_sql":
                    valid = value.get("sql_valid")
                    if not valid:
                        logger.warning(
                            f" validate_sql  错误信息: {value.get('error_message')}"
                        )

                elif key == "execute_sql":
                    if value.get("error_message"):
                        logger.error(
                            f"  execute_sql 执行错误: {value.get('error_message')}"
                        )
                    else:
                        logger.info("  execute_sql 执行成功")

                elif key == "refine_answer":
                    messages = value.get("messages", [])
                    if messages:
                        logger.info(f"最终回答: {messages[0].content}")

    except GraphRecursionError:
        logger.error("❌ 递归次数过多，工作流停止。")
    except Exception as e:
        logger.error(f"❌ 工作流执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(run_analysis())
