#!/usr/bin/env python3
"""
Execute SQL functions in Supabase database
"""

import psycopg2
from pathlib import Path

# Connection parameters
DB_HOST = "db.ptrmidlhfdbybxmyovtm.supabase.co"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "QWEpoi123987@"
DB_PORT = 5432

# SQL file path
SQL_FILE = Path(__file__).parent.parent / 'database' / 'finn_link_extractor_function.sql'

def execute_sql():
    """Execute SQL functions from file"""

    print(f"📄 Reading SQL from: {SQL_FILE}")

    if not SQL_FILE.exists():
        print(f"❌ SQL file not found: {SQL_FILE}")
        return False

    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    print(f"✅ Loaded {len(sql_content)} characters of SQL")

    try:
        # Connect to database
        print(f"🔌 Connecting to Supabase: {DB_HOST}")

        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            connect_timeout=10
        )

        print("✅ Connected to database!")

        # Create cursor
        cur = conn.cursor()

        # Execute SQL
        print("🚀 Executing SQL functions...")
        cur.execute(sql_content)

        # Commit changes
        conn.commit()

        print("✅ SQL functions created successfully!")

        # Verify functions exist
        print("\n🔍 Verifying created functions...")
        cur.execute("""
            SELECT routine_name, routine_type
            FROM information_schema.routines
            WHERE routine_schema = 'public'
              AND routine_name LIKE '%finn%'
            ORDER BY routine_name;
        """)

        functions = cur.fetchall()

        if functions:
            print(f"✅ Found {len(functions)} function(s):")
            for func_name, func_type in functions:
                print(f"   - {func_name} ({func_type})")
        else:
            print("⚠️ No functions found matching 'finn'")

        # Close cursor and connection
        cur.close()
        conn.close()

        print("\n🎉 All done!")
        return True

    except psycopg2.OperationalError as e:
        print(f"❌ Connection error: {e}")
        print("💡 Check network connectivity and credentials")
        return False
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = execute_sql()
    exit(0 if success else 1)
