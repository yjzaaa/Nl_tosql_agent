"""Simple PostgreSQL Query Test

Tests basic SQL query functionality without LangGraph workflow.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.data_sources.postgres_source import PostgreSQLDataSource


def test_simple_queries():
    """Test simple SQL queries"""

    print("=" * 80)
    print("PostgreSQL Simple Query Test")
    print("=" * 80)
    print()

    # Create PostgreSQL data source
    pg_source = PostgreSQLDataSource(
        host='localhost',
        port=5432,
        database='cost_allocation',
        user='postgres',
        password='123456'
    )

    # Check connection
    print("1. Testing Connection...")
    is_available = pg_source.is_available()
    print(f"   Connection Available: {is_available}")

    if not is_available:
        print("   X Cannot continue - connection failed")
        return

    print()

    # Test 1: Simple SELECT
    print("2. Test Simple SELECT Query...")
    try:
        df = pg_source.load_data('cost_database', limit=10)
        print(f"   OK Loaded {len(df)} rows")
        print(f"   Columns: {', '.join(df.columns.tolist())}")
        print()
    except Exception as e:
        print(f"   X Error: {e}")
        print()

    # Test 2: Aggregate query
    print("3. Test Aggregate Query...")
    try:
        summary = pg_source.get_cost_summary()
        by_func = summary.get('by_function', [])
        print(f"   OK Cost summary by function: {len(by_func)} groups")
        for func in by_func[:3]:
            print(f"      {func['function']}: {func['total_amount']:,.2f}")
        print()
    except Exception as e:
        print(f"   X Error: {e}")
        print()

    # Test 3: Filter query
    print("4. Test Filter Query...")
    try:
        df = pg_source.execute_query("""
            SELECT function, key, SUM(amount) as total
            FROM cost_database
            WHERE function = 'IT'
            GROUP BY function, key
            ORDER BY total DESC
            LIMIT 5
        """)
        print(f"   OK Filter query executed: {len(df)} rows")
        for _, row in df.head(3).iterrows():
            print(f"      Function: {row['function']}, Key: {row['key']}, Total: {row['total']:,.2f}")
        print()
    except Exception as e:
        print(f"   X Error: {e}")
        print()

    # Test 4: Join query
    print("5. Test JOIN Query...")
    try:
        df = pg_source.join_cost_and_rate(limit=5)
        print(f"   OK Join query executed: {len(df)} rows")
        for _, row in df.head(3).iterrows():
            print(f"      {row['function']}, Allocated: {row['allocated_amount']:,.2f}")
        print()
    except Exception as e:
        print(f"   X Error: {e}")
        print()

    print("=" * 80)
    print("Test Completed")
    print("=" * 80)


if __name__ == "__main__":
    test_simple_queries()
