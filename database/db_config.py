"""
Database configuration for Supabase PostgreSQL
"""

import os
from urllib.parse import urlparse

# Database connection settings
# Direct connection (may have connection limits)
DATABASE_URL_DIRECT = "postgresql://postgres:Minettejasmine@13@db.aatxokeqklkkgxkufxbl.supabase.co:5432/postgres"

# Transaction pooler connection (recommended for applications)
DATABASE_URL_POOLER = "postgresql://postgres.aatxokeqklkkgxkufxbl:Minettejasmine@13@aws-1-us-east-2.pooler.supabase.com:6543/postgres"

# Use pooler by default for better connection management
DATABASE_URL = DATABASE_URL_POOLER

# Direct connection config
DB_CONFIG_DIRECT = {
    'host': 'db.aatxokeqklkkgxkufxbl.supabase.co',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'Minettejasmine@13',
    'sslmode': 'require'  # Supabase requires SSL
}

# Pooler connection config (recommended)
DB_CONFIG_POOLER = {
    'host': 'aws-1-us-east-2.pooler.supabase.com',
    'port': 6543,
    'database': 'postgres',
    'user': 'postgres.aatxokeqklkkgxkufxbl',
    'password': 'Minettejasmine@13',
    'sslmode': 'require'
}

# Use pooler by default
DB_CONFIG = DB_CONFIG_POOLER

# Connection pool settings
POOL_MIN_CONN = 1
POOL_MAX_CONN = 10

# Batch processing settings
BATCH_SIZE = 100
UPSERT_BATCH_SIZE = 50

# Table names
TABLE_ATTENDEES = 'attendees'
TABLE_SCRAPER_RUNS = 'scraper_runs'
TABLE_ATTENDEE_CHANGES = 'attendee_changes'