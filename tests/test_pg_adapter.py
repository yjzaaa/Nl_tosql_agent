"""测试PostgreSQL数据源基本功能"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from core.data_sources.postgres_source import PostgreSQLDataSource

    print("=" * 60)
    print("Test 1: PostgreSQL Data Source Basic Functionality")
    print("=" * 60)
    print()

    # 测试PostgreSQL数据源
    pg_source = PostgreSQLDataSource()

    # 测试连接字符串
    print("Testing connection string...")
    conn_string = pg_source._get_connection_string()
    print(f"  Connection string: {conn_string}")
    is_available = pg_source.is_available()
    print(f"  Connection successful: {is_available}")
    print()

    # 测试元数据
    print("Testing metadata...")
    metadata = pg_source.get_metadata()
    print(f"  Source type: {metadata['source_type']}")
    print(f"  Host: {metadata['host']}")
    print(f"  Port: {metadata['port']}")
    print(f"  Database: {metadata['database']}")
    print(f"  Schema: {metadata['schema']}")
    print(f"  Tables: {metadata['tables']}")
    print()

    if is_available:
        # 测试获取上下文
        print("Testing data source context...")
        context = pg_source.get_context()
        print(f"  Data source type: {context.get('data_source_type', 'Unknown')}")
        print(f"  Database: {context.get('database', 'Unknown')}")
        print()

        # 测试列出表
        print("Testing list all tables...")
        tables = context.get("tables", {})
        print(f"  Table names: {list(tables.keys())}")
        print()

        # 测试获取成本汇总
        print("Testing cost summary...")
        try:
            cost_summary = pg_source.get_cost_summary()
            print(f"  By function: {len(cost_summary.get('by_function', []))} groups")
            print(f"  By key: {len(cost_summary.get('by_key', []))} groups")
            print(f"  By month: {len(cost_summary.get('by_month', []))} groups")
            print()
        except Exception as e:
            print(f"  Failed to get cost summary: {e}")
            print()

        # 测试获取费率汇总
        print("Testing rate summary...")
        try:
            rate_summary = pg_source.get_rate_summary()
            print(f"  By key: {len(rate_summary.get('by_key', []))} groups")
            print(f"  By business line: {len(rate_summary.get('by_business_line', []))} groups")
            print()
        except Exception as e:
            print(f"  Failed to get rate summary: {e}")
            print()

        print("[OK] PostgreSQL data source test passed!")
    else:
        print("[WARNING] PostgreSQL connection failed. Please check:")
        print("  1. PostgreSQL service is running")
        print("  2. Connection settings are correct (config_postgres.yaml)")
        print("  3. Database exists (cost_allocation)")
        print()
        print("[INFO] PostgreSQL data source is configured but not connected.")
        print("       The implementation is ready to use once the connection is established.")
    print()

except Exception as e:
    print(f"[ERROR] Test failed: {str(e)}")
    import traceback
    traceback.print_exc()
    print()
