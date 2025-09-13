"""
Sync scraped data to PostgreSQL database
This script is called after each scraping run to update the database
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from pathlib import Path
import json
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_config import DB_CONFIG, TABLE_ATTENDEES, TABLE_SCRAPER_RUNS, BATCH_SIZE
from database.migrate_data import DataMigrator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def sync_latest_run():
    """Sync the latest run data to the database"""
    
    # Get the latest run directory
    data_dir = Path(__file__).parent.parent / 'data' / 'runs'
    
    # Check if we have a RUN_TIMESTAMP environment variable (set by run_daily_scrape.sh)
    run_timestamp = os.environ.get('RUN_TIMESTAMP')
    
    if run_timestamp:
        run_dir = data_dir / run_timestamp
        logger.info(f"Syncing specific run: {run_timestamp}")
    else:
        # Find the latest run
        run_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir() and d.name != 'latest'])
        if not run_dirs:
            logger.error("No run directories found")
            return False
        
        run_dir = run_dirs[-1]  # Get the latest
        run_timestamp = run_dir.name
        logger.info(f"Syncing latest run: {run_timestamp}")
    
    # Check if CSV exists
    csv_file = run_dir / 'all_attendees_with_details.csv'
    if not csv_file.exists():
        logger.error(f"CSV file not found: {csv_file}")
        return False
    
    # Initialize migrator
    migrator = DataMigrator()
    
    if not migrator.connect():
        logger.error("Failed to connect to database")
        return False
    
    try:
        # Convert timestamp string to datetime
        run_datetime = datetime.strptime(run_timestamp, "%Y-%m-%d_%H%M%S")
        
        # Load CSV data
        df = pd.read_csv(csv_file)
        total_attendees = len(df)
        
        logger.info(f"Loaded {total_attendees} attendees from CSV")
        
        # Create or get run record
        run_id = migrator.get_or_create_run(run_datetime, total_attendees)
        
        if not run_id:
            logger.error("Failed to create run record")
            return False
        
        # Sync attendees
        inserted, updated, errors = migrator.upsert_attendees(df, run_id, run_datetime)
        
        logger.info(f"Sync complete:")
        logger.info(f"  - Inserted: {inserted}")
        logger.info(f"  - Updated: {updated}")
        logger.info(f"  - Errors: {errors}")
        
        # Get database statistics
        migrator.cursor.execute("SELECT * FROM attendee_statistics")
        stats = migrator.cursor.fetchone()
        
        logger.info("Current database statistics:")
        logger.info(f"  Total attendees: {stats['total_attendees']}")
        logger.info(f"  Unique organizations: {stats['unique_organizations']}")
        logger.info(f"  Unique countries: {stats['unique_countries']}")
        logger.info(f"  Unique industries: {stats['unique_industries']}")
        
        return errors == 0
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        return False
        
    finally:
        migrator.close()

def main():
    """Main sync function"""
    logger.info("=" * 50)
    logger.info("Database Sync Starting")
    logger.info("=" * 50)
    
    success = sync_latest_run()
    
    if success:
        logger.info("✓ Database sync completed successfully")
        sys.exit(0)
    else:
        logger.error("✗ Database sync failed")
        sys.exit(1)

if __name__ == "__main__":
    main()