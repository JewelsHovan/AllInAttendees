"""
Migrate existing CSV data to PostgreSQL database
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from datetime import datetime
from pathlib import Path
import json
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_config import DB_CONFIG, TABLE_ATTENDEES, TABLE_SCRAPER_RUNS, BATCH_SIZE

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataMigrator:
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            logger.info("Connected to database successfully")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def create_tables(self):
        """Execute schema SQL to create tables"""
        schema_file = Path(__file__).parent / 'schema.sql'
        
        try:
            # Check if tables already exist
            self.cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'attendees'
            """)
            
            if self.cursor.fetchone()['count'] > 0:
                logger.info("Database schema already exists")
                return True
            
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            # Execute the schema
            self.cursor.execute(schema_sql)
            self.conn.commit()
            logger.info("Database schema created successfully")
            return True
        except Exception as e:
            if "already exists" in str(e):
                logger.info("Database schema already exists")
                self.conn.rollback()
                return True
            logger.error(f"Failed to create schema: {e}")
            self.conn.rollback()
            return False
    
    def get_or_create_run(self, run_timestamp, total_attendees):
        """Get or create a scraper run record"""
        try:
            # Check if run exists
            self.cursor.execute(
                f"SELECT id FROM {TABLE_SCRAPER_RUNS} WHERE run_timestamp = %s",
                (run_timestamp,)
            )
            result = self.cursor.fetchone()
            
            if result:
                return result['id']
            
            # Create new run
            self.cursor.execute(
                f"""
                INSERT INTO {TABLE_SCRAPER_RUNS} 
                (run_timestamp, run_date, total_attendees, status)
                VALUES (%s, %s, %s, 'migrated')
                RETURNING id
                """,
                (run_timestamp, run_timestamp.date(), total_attendees)
            )
            
            run_id = self.cursor.fetchone()['id']
            self.conn.commit()
            return run_id
            
        except Exception as e:
            logger.error(f"Failed to create run record: {e}")
            self.conn.rollback()
            return None
    
    def prepare_attendee_data(self, row, run_timestamp):
        """Prepare attendee data for insertion"""
        # Helper function to clean values
        def clean_value(value):
            """Clean NaN and empty values"""
            if pd.isna(value) or value == '' or value == 'nan' or value == 'NaN':
                return None
            return str(value)
        
        # Clean the row dict for JSON serialization
        row_dict = {}
        for key, value in row.to_dict().items():
            if pd.isna(value):
                row_dict[key] = None
            elif isinstance(value, (int, float)) and pd.notna(value):
                row_dict[key] = value
            else:
                row_dict[key] = str(value) if value else None
        
        # Clean and prepare data
        data = {
            'id': clean_value(row.get('id')),
            'user_id': clean_value(row.get('userId')),
            'email': clean_value(row.get('email')) or f"noemail_{row.get('id', 'unknown')}@placeholder.com",  # Email is required, make unique
            'first_name': clean_value(row.get('firstName')),
            'last_name': clean_value(row.get('lastName')),
            'job_title': clean_value(row.get('jobTitle')),
            'organization': clean_value(row.get('organization')),
            'biography': clean_value(row.get('biography')),
            'mobile_phone': clean_value(row.get('mobilePhone')),
            'landline_phone': clean_value(row.get('landlinePhone')),
            'website_url': clean_value(row.get('websiteUrl')),
            'photo_url': clean_value(row.get('photoUrl')),
            'detail_country': clean_value(row.get('detail_country')),
            'detail_province': clean_value(row.get('detail_province')),
            'detail_language': clean_value(row.get('detail_language')),
            'detail_industry': clean_value(row.get('detail_industry')),
            'detail_org_type': clean_value(row.get('detail_org_type')),
            'detail_position_type': clean_value(row.get('detail_position_type')),
            'detail_ai_maturity': clean_value(row.get('detail_ai_maturity')),
            'detail_category': clean_value(row.get('detail_category')),
            'detail_interests': clean_value(row.get('detail_interests')),
            'detail_motivation': clean_value(row.get('detail_motivation')),
            'social_linkedin': clean_value(row.get('social_linkedin')),
            'social_twitter': clean_value(row.get('social_twitter')),
            'social_facebook': clean_value(row.get('social_facebook')),
            'social_instagram': clean_value(row.get('social_instagram')),
            'social_github': clean_value(row.get('social_github')),
            'social_dribbble': clean_value(row.get('social_dribbble')),
            'social_pinterest': clean_value(row.get('social_pinterest')),
            'social_skype': clean_value(row.get('social_skype')),
            'social_googleplus': clean_value(row.get('social_googleplus')),
            'social_vimeo': clean_value(row.get('social_vimeo')),
            'social_youtube': clean_value(row.get('social_youtube')),
            'first_seen_at': run_timestamp,
            'last_updated_at': run_timestamp,
            'raw_data': json.dumps(row_dict, default=str)
        }
        
        return data
    
    def upsert_attendees(self, df, run_id, run_timestamp):
        """Upsert attendees data to database"""
        total = len(df)
        inserted = 0
        updated = 0
        errors = 0
        
        for i in range(0, total, BATCH_SIZE):
            batch = df.iloc[i:i+BATCH_SIZE]
            batch_inserted = 0
            batch_updated = 0
            batch_errors = 0
            
            for _, row in batch.iterrows():
                try:
                    data = self.prepare_attendee_data(row, run_timestamp)
                    
                    # Skip if no ID
                    if not data['id']:
                        logger.warning(f"Skipping row with no ID: {row.get('email')}")
                        batch_errors += 1
                        continue
                    
                    data['last_seen_run_id'] = run_id
                    
                    # Try to insert, on conflict update
                    self.cursor.execute(f"""
                        INSERT INTO {TABLE_ATTENDEES} (
                            id, user_id, email, first_name, last_name, job_title, 
                            organization, biography, mobile_phone, landline_phone, 
                            website_url, photo_url, detail_country, detail_province, 
                            detail_language, detail_industry, detail_org_type, 
                            detail_position_type, detail_ai_maturity, detail_category, 
                            detail_interests, detail_motivation, social_linkedin, 
                            social_twitter, social_facebook, social_instagram, 
                            social_github, social_dribbble, social_pinterest, 
                            social_skype, social_googleplus, social_vimeo, 
                            social_youtube, first_seen_at, last_updated_at, 
                            last_seen_run_id, raw_data
                        ) VALUES (
                            %(id)s, %(user_id)s, %(email)s, %(first_name)s, %(last_name)s, 
                            %(job_title)s, %(organization)s, %(biography)s, %(mobile_phone)s, 
                            %(landline_phone)s, %(website_url)s, %(photo_url)s, %(detail_country)s, 
                            %(detail_province)s, %(detail_language)s, %(detail_industry)s, 
                            %(detail_org_type)s, %(detail_position_type)s, %(detail_ai_maturity)s, 
                            %(detail_category)s, %(detail_interests)s, %(detail_motivation)s, 
                            %(social_linkedin)s, %(social_twitter)s, %(social_facebook)s, 
                            %(social_instagram)s, %(social_github)s, %(social_dribbble)s, 
                            %(social_pinterest)s, %(social_skype)s, %(social_googleplus)s, 
                            %(social_vimeo)s, %(social_youtube)s, %(first_seen_at)s, 
                            %(last_updated_at)s, %(last_seen_run_id)s, %(raw_data)s
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            user_id = EXCLUDED.user_id,
                            email = EXCLUDED.email,
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            job_title = EXCLUDED.job_title,
                            organization = EXCLUDED.organization,
                            biography = EXCLUDED.biography,
                            mobile_phone = EXCLUDED.mobile_phone,
                            landline_phone = EXCLUDED.landline_phone,
                            website_url = EXCLUDED.website_url,
                            photo_url = EXCLUDED.photo_url,
                            detail_country = EXCLUDED.detail_country,
                            detail_province = EXCLUDED.detail_province,
                            detail_language = EXCLUDED.detail_language,
                            detail_industry = EXCLUDED.detail_industry,
                            detail_org_type = EXCLUDED.detail_org_type,
                            detail_position_type = EXCLUDED.detail_position_type,
                            detail_ai_maturity = EXCLUDED.detail_ai_maturity,
                            detail_category = EXCLUDED.detail_category,
                            detail_interests = EXCLUDED.detail_interests,
                            detail_motivation = EXCLUDED.detail_motivation,
                            social_linkedin = EXCLUDED.social_linkedin,
                            social_twitter = EXCLUDED.social_twitter,
                            social_facebook = EXCLUDED.social_facebook,
                            social_instagram = EXCLUDED.social_instagram,
                            social_github = EXCLUDED.social_github,
                            social_dribbble = EXCLUDED.social_dribbble,
                            social_pinterest = EXCLUDED.social_pinterest,
                            social_skype = EXCLUDED.social_skype,
                            social_googleplus = EXCLUDED.social_googleplus,
                            social_vimeo = EXCLUDED.social_vimeo,
                            social_youtube = EXCLUDED.social_youtube,
                            last_seen_run_id = EXCLUDED.last_seen_run_id,
                            raw_data = EXCLUDED.raw_data
                        RETURNING (xmax = 0) AS inserted
                    """, data)
                    
                    result = self.cursor.fetchone()
                    if result['inserted']:
                        batch_inserted += 1
                    else:
                        batch_updated += 1
                        
                except Exception as e:
                    logger.error(f"Failed to upsert attendee {row.get('id')}: {e}")
                    batch_errors += 1
                    # Rollback on error to reset transaction
                    self.conn.rollback()
            
            # Commit after each batch if no errors
            if batch_errors == 0:
                self.conn.commit()
                inserted += batch_inserted
                updated += batch_updated
            else:
                # Try to commit successful records
                try:
                    self.conn.commit()
                    inserted += batch_inserted
                    updated += batch_updated
                    errors += batch_errors
                except:
                    self.conn.rollback()
                    errors += len(batch)
            
            logger.info(f"Processed {min(i+BATCH_SIZE, total)}/{total} attendees (Inserted: {batch_inserted}, Updated: {batch_updated}, Errors: {batch_errors})")
        
        # Update run statistics
        self.cursor.execute(f"""
            UPDATE {TABLE_SCRAPER_RUNS} 
            SET new_attendees = %s, updated_attendees = %s
            WHERE id = %s
        """, (inserted, updated, run_id))
        self.conn.commit()
        
        return inserted, updated, errors
    
    def migrate_run(self, run_dir):
        """Migrate a single run directory"""
        run_path = Path(run_dir)
        csv_file = run_path / 'all_attendees_with_details.csv'
        
        if not csv_file.exists():
            logger.warning(f"No CSV file found in {run_dir}")
            return False
        
        # Parse timestamp from directory name
        try:
            timestamp_str = run_path.name
            run_timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H%M%S")
        except ValueError:
            logger.error(f"Invalid timestamp format in directory name: {run_path.name}")
            return False
        
        logger.info(f"Migrating run from {timestamp_str}")
        
        # Load CSV data
        df = pd.read_csv(csv_file)
        total_attendees = len(df)
        
        # Create run record
        run_id = self.get_or_create_run(run_timestamp, total_attendees)
        if not run_id:
            return False
        
        # Upsert attendees
        inserted, updated, errors = self.upsert_attendees(df, run_id, run_timestamp)
        
        logger.info(f"Migration complete for {timestamp_str}:")
        logger.info(f"  - Inserted: {inserted}")
        logger.info(f"  - Updated: {updated}")
        logger.info(f"  - Errors: {errors}")
        
        return errors == 0
    
    def migrate_all_runs(self):
        """Migrate all runs in the data directory"""
        data_dir = Path(__file__).parent.parent / 'data' / 'runs'
        
        if not data_dir.exists():
            logger.error(f"Data directory not found: {data_dir}")
            return
        
        # Get all run directories
        run_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir() and d.name != 'latest'])
        
        logger.info(f"Found {len(run_dirs)} runs to migrate")
        
        success_count = 0
        for run_dir in run_dirs:
            if self.migrate_run(run_dir):
                success_count += 1
        
        logger.info(f"Migration complete: {success_count}/{len(run_dirs)} runs migrated successfully")

def main():
    """Main migration function"""
    migrator = DataMigrator()
    
    if not migrator.connect():
        logger.error("Failed to connect to database")
        return
    
    try:
        # Create tables if they don't exist
        logger.info("Creating database schema...")
        if not migrator.create_tables():
            logger.error("Failed to create database schema")
            return
        
        # Migrate all runs
        logger.info("Starting data migration...")
        migrator.migrate_all_runs()
        
        # Show statistics
        migrator.cursor.execute("SELECT * FROM attendee_statistics")
        stats = migrator.cursor.fetchone()
        
        logger.info("Database statistics:")
        logger.info(f"  Total attendees: {stats['total_attendees']}")
        logger.info(f"  Unique organizations: {stats['unique_organizations']}")
        logger.info(f"  Unique countries: {stats['unique_countries']}")
        logger.info(f"  Unique industries: {stats['unique_industries']}")
        
    finally:
        migrator.close()

if __name__ == "__main__":
    main()