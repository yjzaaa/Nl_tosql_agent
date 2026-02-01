"""Test NL to SQL Workflow"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nl_to_sql_agent import NLToSQLAgent

def test_nl_to_sql_workflow():
    """Test NL to SQL workflow with various queries"""

    print("=" * 80)
    print("NL to SQL Workflow Test")
    print("=" * 80)
    print()

    # Create agent with default skill path and skill name
    agent = NLToSQLAgent(
        skill_path=str(Path(__file__).parent / "skills"),
        skill_name="nl-to-sql-agent"
    )

    # Test queries
    test_queries = [
        "显示所有数据",
        "查询成本最高的前10条记录",
        "按功能类型分组统计总成本",
        "查询IT相关的所有成本",
        "查询2024年1月的成本"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Test Query {i}: {query}")
        print(f"{'=' * 80}")
        print()

        try:
            result = agent.query(query, data_source_type="excel")

            print(f"Success: {result.get('success')}")
            print()

            if result.get('sql'):
                print(f"Generated SQL:")
                print(f"  {result['sql']}")
                print()

            if result.get('result'):
                print(f"Execution Result:")
                result_lines = result['result'].split('\n')
                # Show first 20 lines
                for line in result_lines[:20]:
                    print(f"  {line}")
                if len(result_lines) > 20:
                    print(f"  ... ({len(result_lines) - 20} more lines)")
                print()

            if result.get('answer'):
                print(f"Refined Answer:")
                print(f"  {result['answer']}")
                print()

            if result.get('error'):
                print(f"Error:")
                print(f"  {result['error']}")
                print()

            if result.get('trace_id'):
                print(f"Trace ID: {result['trace_id']}")
                print()

        except Exception as e:
            print(f"Error executing query: {e}")
            import traceback
            traceback.print_exc()
            print()

    print("=" * 80)
    print("Test Completed")
    print("=" * 80)


def test_postgresql_data_source():
    """Test NL to SQL workflow with PostgreSQL data source"""

    print("=" * 80)
    print("NL to SQL Workflow Test - PostgreSQL Data Source")
    print("=" * 80)
    print()

    # Create agent
    agent = NLToSQLAgent(
        skill_path=str(Path(__file__).parent / "skills"),
        skill_name="nl-to-sql-agent"
    )

    # Test queries for PostgreSQL
    test_queries = [
        "显示所有成本数据库记录",
        "按功能类型统计总成本",
        "查询IT分配成本",
        "查询2024年1月的所有成本",
        "按月份统计成本总额"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 80}")
        print(f"Test Query {i}: {query}")
        print(f"{'=' * 80}")
        print()

        try:
            result = agent.query(query, data_source_type="postgresql")

            print(f"Success: {result.get('success')}")
            print()

            if result.get('sql'):
                print(f"Generated SQL:")
                print(f"  {result['sql']}")
                print()

            if result.get('result'):
                print(f"Execution Result:")
                result_lines = result['result'].split('\n')
                # Show first 20 lines
                for line in result_lines[:20]:
                    print(f"  {line}")
                if len(result_lines) > 20:
                    print(f"  ... ({len(result_lines) - 20} more lines)")
                print()

            if result.get('answer'):
                print(f"Refined Answer:")
                print(f"  {result['answer']}")
                print()

            if result.get('error'):
                print(f"Error:")
                print(f"  {result['error']}")
                print()

            if result.get('trace_id'):
                print(f"Trace ID: {result['trace_id']}")
                print()

        except Exception as e:
            print(f"Error executing query: {e}")
            import traceback
            traceback.print_exc()
            print()

    print("=" * 80)
    print("Test Completed")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test NL to SQL workflow")
    parser.add_argument(
        "--data-source",
        choices=["excel", "postgresql", "both"],
        default="excel",
        help="Data source to test"
    )

    args = parser.parse_args()

    if args.data_source == "excel" or args.data_source == "both":
        print("\n" + "=" * 80)
        print("Testing with Excel Data Source")
        print("=" * 80)
        test_nl_to_sql_workflow()

    if args.data_source == "postgresql" or args.data_source == "both":
        print("\n" + "=" * 80)
        print("Testing with PostgreSQL Data Source")
        print("=" * 80)
        test_postgresql_data_source()
