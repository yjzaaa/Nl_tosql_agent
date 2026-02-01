"""Direct PostgreSQL connection test"""

import psycopg2

# Test connection with different configurations
configs = [
    {
        "host": "localhost",
        "port": 5432,
        "database": "cost_allocation",
        "user": "postgres",
        "password": "123456",
        "name": "Standard config"
    },
    {
        "host": "127.0.0.1",
        "port": 5432,
        "database": "cost_allocation",
        "user": "postgres",
        "password": "123456",
        "name": "Using 127.0.0.1"
    },
    {
        "host": "localhost",
        "port": 5433,
        "database": "cost_allocation",
        "user": "postgres",
        "password": "123456",
        "name": "Port 5433"
    }
]

print("=" * 60)
print("Testing PostgreSQL Connection")
print("=" * 60)
print()

for config in configs:
    print(f"Testing: {config['name']}")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  Database: {config['database']}")
    print(f"  User: {config['user']}")
    print()

    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password']
        )

        print(f"  Status: SUCCESS")

        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"  PostgreSQL Version: {version[:50]}...")
        print()

        # List databases
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = [row[0] for row in cursor.fetchall()]
        print(f"  Available databases: {', '.join(databases)}")
        print()

        # Check if cost_allocation exists
        if config['database'] in databases:
            print(f"  Database '{config['database']}' EXISTS")
            cursor.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_catalog = '{config['database']}'")
            table_count = cursor.fetchone()[0]
            print(f"  Tables in database: {table_count}")

            if table_count > 0:
                cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_catalog = '{config['database']}' ORDER BY table_name")
                tables = [row[0] for row in cursor.fetchall()]
                print(f"  Table names: {', '.join(tables)}")
        else:
            print(f"  Database '{config['database']}' NOT FOUND")
        print()

        conn.close()

    except psycopg2.OperationalError as e:
        print(f"  Status: FAILED")
        print(f"  Error: {str(e)}")
        print()
    except Exception as e:
        print(f"  Status: FAILED")
        print(f"  Error: {str(e)}")
        print()

print("=" * 60)
