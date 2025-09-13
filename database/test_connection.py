"""
Test database connection and verify credentials
"""

import psycopg2
from psycopg2 import OperationalError
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_config import DB_CONFIG_POOLER, DB_CONFIG_DIRECT

def test_connection():
    """Test various connection configurations"""
    
    # Test different configurations
    configs_to_test = [
        {
            **DB_CONFIG_POOLER,
            'description': 'Transaction Pooler (Recommended)'
        },
        {
            **DB_CONFIG_DIRECT,
            'description': 'Direct Connection'
        }
    ]
    
    for config in configs_to_test:
        desc = config.pop('description')
        print(f"\nTrying: {desc}")
        print(f"  Host: {config['host']}")
        print(f"  Port: {config['port']}")
        print(f"  User: {config['user']}")
        try:
            conn = psycopg2.connect(**config)
            cursor = conn.cursor()
            
            # Test query
            cursor.execute("SELECT current_database(), current_user, version()")
            db_info = cursor.fetchone()
            
            print(f"✓ Connection successful!")
            print(f"  Database: {db_info[0]}")
            print(f"  User: {db_info[1]}")
            print(f"  Version: {db_info[2][:50]}...")
            
            # Check if our tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('attendees', 'scraper_runs')
            """)
            
            tables = cursor.fetchall()
            if tables:
                print(f"  Existing tables: {[t[0] for t in tables]}")
            else:
                print("  No tables created yet")
            
            cursor.close()
            conn.close()
            return True
            
        except OperationalError as e:
            print(f"✗ Connection failed: {e}")
            if "could not translate host name" in str(e):
                print("  → The hostname appears to be incorrect.")
                print("  → Please verify your Supabase project URL.")
                print("  → It should look like: db.[project-ref].supabase.co")
            elif "password authentication failed" in str(e):
                print("  → Authentication failed. Check your password.")
            elif "timeout" in str(e).lower():
                print("  → Connection timed out. Check if the database is accessible.")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
    
    return False

def main():
    """Main test function"""
    print("=" * 50)
    print("Supabase PostgreSQL Connection Test")
    print("=" * 50)
    
    if test_connection():
        print("\n✓ Database is ready for migration!")
        print("\nTo run the migration, execute:")
        print("  python3 database/migrate_data.py")
    else:
        print("\n✗ Could not establish database connection")
        print("\nPlease check:")
        print("1. Your Supabase project URL (host)")
        print("2. Database password")
        print("3. Network connectivity")
        print("\nYou can find these in your Supabase dashboard:")
        print("  Settings → Database → Connection string")

if __name__ == "__main__":
    main()