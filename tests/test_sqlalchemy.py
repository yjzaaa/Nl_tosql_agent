"""Test SQLAlchemy PostgreSQL connection"""

from sqlalchemy import create_engine, text
import pandas as pd

# Test configuration
config = {
    "host": "localhost",
    "port": 5432,
    "database": "cost_allocation",
    "user": "postgres",
    "password": "123456",
    "schema": "public"
}

print("=" * 60)
print("Testing SQLAlchemy PostgreSQL Connection")
print("=" * 60)
print()

# Test 1: Simple connection string
print("Test 1: Simple connection string")
conn_string1 = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
print(f"  Connection string: {conn_string1}")

try:
    engine1 = create_engine(conn_string1)

    with engine1.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"  Status: SUCCESS")
        print(f"  Version: {version[:50]}...")

        # List tables
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"  Tables: {', '.join(tables)}")
        print()

except Exception as e:
    print(f"  Status: FAILED")
    print(f"  Error: {str(e)}")
    print()

# Test 2: Connection string with schema
print("Test 2: Connection string with schema")
conn_string2 = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?schema={config['schema']}"
print(f"  Connection string: {conn_string2}")

try:
    engine2 = create_engine(conn_string2)

    with engine2.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        version = result.fetchone()[0]
        print(f"  Status: SUCCESS")
        print(f"  Version: {version[:50]}...")
        print()

except Exception as e:
    print(f"  Status: FAILED")
    print(f"  Error: {str(e)}")
    print()

# Test 3: Connection using psycopg2
print("Test 3: Load data using pandas + psycopg2")

try:
    import psycopg2

    conn = psycopg2.connect(
        host=config['host'],
        port=config['port'],
        database=config['database'],
        user=config['user'],
        password=config['password']
    )

    query = f'SELECT * FROM {config["schema"]}.cost_database LIMIT 5'
    df = pd.read_sql(query, conn)
    print(f"  Status: SUCCESS")
    print(f"  Loaded {len(df)} rows")
    print(f"  Columns: {', '.join(df.columns.tolist())}")
    print()

    conn.close()
except Exception as e:
    print(f"  Status: FAILED")
    print(f"  Error: {str(e)}")
    print()

# Test 4: Using SQLAlchemy read_sql
print("Test 4: Using SQLAlchemy read_sql")

try:
    from sqlalchemy import create_engine, text

    engine = create_engine(conn_string1)

    df = pd.read_sql(
        text(f"SELECT * FROM {config['schema']}.cost_database LIMIT 5"),
        engine
    )
    print(f"  Status: SUCCESS")
    print(f"  Loaded {len(df)} rows")
    print(f"  Columns: {', '.join(df.columns.tolist())}")
    print()

except Exception as e:
    print(f"  Status: FAILED")
    print(f"  Error: {str(e)}")
    print()

print("=" * 60)
print("Test Completed")
print("=" * 60)
