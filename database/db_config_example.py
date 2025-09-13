"""
Example database configuration file
Copy this to db_config.py and fill in your actual credentials
DO NOT commit db_config.py to version control!
"""

# Direct connection (for migrations and admin tasks)
DB_CONFIG_DIRECT = {
    "host": "your-project.supabase.co",
    "database": "postgres",
    "user": "postgres.your-project-id",
    "password": "YOUR_PASSWORD_HERE",
    "port": 5432
}

# Pooler connection (for application use)
DB_CONFIG_POOLER = {
    "host": "your-region.pooler.supabase.com",
    "database": "postgres",
    "user": "postgres.your-project-id",
    "password": "YOUR_PASSWORD_HERE",
    "port": 6543
}