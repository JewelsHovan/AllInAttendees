"""
Check for new attendees from the latest run
"""

import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from pathlib import Path
from tabulate import tabulate

sys.path.insert(0, str(Path(__file__).parent.parent))
from database.db_config import DB_CONFIG

def get_latest_run_stats():
    """Get statistics from the latest run"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get latest run info
    cursor.execute("""
        SELECT 
            id,
            run_timestamp,
            total_attendees,
            new_attendees,
            updated_attendees
        FROM scraper_runs
        ORDER BY run_timestamp DESC
        LIMIT 1
    """)
    
    latest_run = cursor.fetchone()
    
    if not latest_run:
        print("No runs found in database")
        return
    
    print("=" * 60)
    print("LATEST RUN STATISTICS")
    print("=" * 60)
    print(f"Run Time: {latest_run['run_timestamp']}")
    print(f"Total Attendees: {latest_run['total_attendees']:,}")
    print(f"New Attendees: {latest_run['new_attendees']:,}")
    print(f"Updated Profiles: {latest_run['updated_attendees']:,}")
    print()
    
    # Get new attendees details
    if latest_run['new_attendees'] > 0:
        cursor.execute("""
            SELECT 
                first_name,
                last_name,
                organization,
                job_title,
                detail_country,
                detail_industry
            FROM attendees
            WHERE first_seen_at = %s
            ORDER BY organization, last_name, first_name
            LIMIT 50
        """, (latest_run['run_timestamp'],))
        
        new_attendees = cursor.fetchall()
        
        if new_attendees:
            print("=" * 60)
            print(f"NEW ATTENDEES (showing up to 50 of {latest_run['new_attendees']})")
            print("=" * 60)
            
            table_data = []
            for a in new_attendees:
                table_data.append([
                    f"{a['first_name']} {a['last_name']}",
                    a['organization'] or 'N/A',
                    a['job_title'] or 'N/A',
                    a['detail_country'] or 'N/A'
                ])
            
            print(tabulate(
                table_data,
                headers=['Name', 'Organization', 'Title', 'Country'],
                tablefmt='simple'
            ))
    
    # Get growth trend
    cursor.execute("""
        SELECT 
            DATE(first_seen_at) as signup_date,
            COUNT(*) as new_signups
        FROM attendees
        WHERE first_seen_at >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY DATE(first_seen_at)
        ORDER BY signup_date DESC
    """)
    
    growth_data = cursor.fetchall()
    
    if growth_data:
        print()
        print("=" * 60)
        print("7-DAY GROWTH TREND")
        print("=" * 60)
        
        table_data = []
        for row in growth_data:
            table_data.append([
                row['signup_date'].strftime('%Y-%m-%d'),
                row['new_signups']
            ])
        
        print(tabulate(
            table_data,
            headers=['Date', 'New Signups'],
            tablefmt='simple'
        ))
    
    # Get top new organizations
    cursor.execute("""
        SELECT 
            organization,
            COUNT(*) as count
        FROM attendees
        WHERE first_seen_at = %s
        AND organization IS NOT NULL
        GROUP BY organization
        HAVING COUNT(*) > 1
        ORDER BY count DESC
        LIMIT 10
    """, (latest_run['run_timestamp'],))
    
    new_orgs = cursor.fetchall()
    
    if new_orgs:
        print()
        print("=" * 60)
        print("TOP NEW ORGANIZATIONS")
        print("=" * 60)
        
        table_data = []
        for org in new_orgs:
            table_data.append([
                org['organization'],
                org['count']
            ])
        
        print(tabulate(
            table_data,
            headers=['Organization', 'New Attendees'],
            tablefmt='simple'
        ))
    
    cursor.close()
    conn.close()

def get_growth_summary():
    """Get overall growth summary"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_attendees,
            COUNT(DISTINCT organization) as unique_orgs,
            COUNT(DISTINCT detail_country) as unique_countries,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '24 hours' THEN 1 END) as last_24h,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as last_7d,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_30d
        FROM attendees
    """)
    
    stats = cursor.fetchone()
    
    print()
    print("=" * 60)
    print("OVERALL DATABASE STATISTICS")
    print("=" * 60)
    print(f"Total Attendees: {stats['total_attendees']:,}")
    print(f"Unique Organizations: {stats['unique_orgs']:,}")
    print(f"Unique Countries: {stats['unique_countries']:,}")
    print()
    print("Growth:")
    print(f"  Last 24 hours: +{stats['last_24h']:,} attendees")
    print(f"  Last 7 days: +{stats['last_7d']:,} attendees")
    print(f"  Last 30 days: +{stats['last_30d']:,} attendees")
    
    cursor.close()
    conn.close()

def main():
    """Main function"""
    try:
        get_latest_run_stats()
        get_growth_summary()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()