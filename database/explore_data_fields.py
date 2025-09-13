#!/usr/bin/env python3
"""
Explore database fields and their categories to understand the data structure
"""

import psycopg2
import pandas as pd
from db_config import DB_CONFIG_POOLER
from collections import Counter
import json

def explore_field_values(conn, field_name, limit=50):
    """Get unique values and their counts for a field"""
    query = f"""
        SELECT {field_name}, COUNT(*) as count
        FROM attendees
        WHERE {field_name} IS NOT NULL
        GROUP BY {field_name}
        ORDER BY count DESC
        LIMIT %s
    """
    
    with conn.cursor() as cursor:
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        return [(val, count) for val, count in results]

def get_sample_records(conn, limit=5):
    """Get sample records to understand the data"""
    query = """
        SELECT 
            first_name, last_name, email, organization, job_title,
            detail_country, detail_industry, detail_interests, 
            detail_motivation, detail_ai_maturity, detail_position_type,
            detail_org_type, detail_category
        FROM attendees
        WHERE detail_interests IS NOT NULL 
            AND detail_motivation IS NOT NULL
        ORDER BY first_seen_at DESC
        LIMIT %s
    """
    
    df = pd.read_sql(query, conn, params=(limit,))
    return df

def main():
    print("\n" + "="*80)
    print("EXPLORING DATABASE FIELDS AND CATEGORIES")
    print("="*80)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG_POOLER)
        print("✅ Connected to database\n")
        
        # Fields to explore
        fields_to_explore = [
            'detail_position_type',
            'detail_org_type',
            'detail_industry',
            'detail_ai_maturity',
            'detail_category',
            'detail_country',
            'detail_language'
        ]
        
        # Explore each categorical field
        for field in fields_to_explore:
            print(f"\n{'='*60}")
            print(f"Field: {field.upper()}")
            print('='*60)
            values = explore_field_values(conn, field, limit=30)
            
            if values:
                print(f"Top {len(values)} values:")
                for val, count in values[:15]:  # Show top 15
                    print(f"  • {val}: {count} attendees")
                if len(values) > 15:
                    print(f"  ... and {len(values)-15} more values")
            else:
                print("  No data available")
        
        # Explore job titles to understand executive positions
        print(f"\n{'='*60}")
        print("JOB TITLES (for executive filtering)")
        print('='*60)
        
        # Get executive-related titles
        exec_query = """
            SELECT job_title, COUNT(*) as count
            FROM attendees
            WHERE job_title IS NOT NULL
            AND (
                UPPER(job_title) LIKE '%CEO%' OR
                UPPER(job_title) LIKE '%CTO%' OR
                UPPER(job_title) LIKE '%CFO%' OR
                UPPER(job_title) LIKE '%COO%' OR
                UPPER(job_title) LIKE '%CMO%' OR
                UPPER(job_title) LIKE '%VP%' OR
                UPPER(job_title) LIKE '%VICE PRESIDENT%' OR
                UPPER(job_title) LIKE '%PRESIDENT%' OR
                UPPER(job_title) LIKE '%DIRECTOR%' OR
                UPPER(job_title) LIKE '%HEAD OF%' OR
                UPPER(job_title) LIKE '%FOUNDER%' OR
                UPPER(job_title) LIKE '%PARTNER%' OR
                UPPER(job_title) LIKE '%PRINCIPAL%' OR
                UPPER(job_title) LIKE '%EXECUTIVE%'
            )
            GROUP BY job_title
            ORDER BY count DESC
            LIMIT 30
        """
        
        with conn.cursor() as cursor:
            cursor.execute(exec_query)
            exec_titles = cursor.fetchall()
            
        print(f"Found {len(exec_titles)} executive titles:")
        for title, count in exec_titles[:20]:
            print(f"  • {title}: {count}")
        
        # Explore interests field for AI-related topics
        print(f"\n{'='*60}")
        print("INTERESTS FIELD (for AI solution seekers)")
        print('='*60)
        
        interests_query = """
            SELECT detail_interests
            FROM attendees
            WHERE detail_interests IS NOT NULL
            LIMIT 500
        """
        
        with conn.cursor() as cursor:
            cursor.execute(interests_query)
            interests_data = cursor.fetchall()
        
        # Parse interests (assuming they're pipe-separated)
        all_interests = []
        for (interests,) in interests_data:
            if interests:
                all_interests.extend([i.strip() for i in interests.split('|')])
        
        interest_counts = Counter(all_interests)
        ai_related_interests = {k: v for k, v in interest_counts.items() 
                               if any(term in k.lower() for term in 
                                     ['ai', 'artificial', 'machine', 'learning', 'ml', 
                                      'deep', 'neural', 'nlp', 'computer vision', 
                                      'automation', 'data science', 'analytics'])}
        
        print(f"\nAI-related interests found:")
        for interest, count in sorted(ai_related_interests.items(), 
                                     key=lambda x: x[1], reverse=True)[:20]:
            print(f"  • {interest}: {count}")
        
        # Explore motivation field
        print(f"\n{'='*60}")
        print("MOTIVATION FIELD (for AI solution seekers)")
        print('='*60)
        
        motivation_query = """
            SELECT detail_motivation
            FROM attendees
            WHERE detail_motivation IS NOT NULL
            AND (
                LOWER(detail_motivation) LIKE '%ai%' OR
                LOWER(detail_motivation) LIKE '%artificial%' OR
                LOWER(detail_motivation) LIKE '%machine learning%' OR
                LOWER(detail_motivation) LIKE '%automation%' OR
                LOWER(detail_motivation) LIKE '%solution%' OR
                LOWER(detail_motivation) LIKE '%implement%' OR
                LOWER(detail_motivation) LIKE '%technology%'
            )
            LIMIT 10
        """
        
        with conn.cursor() as cursor:
            cursor.execute(motivation_query)
            motivations = cursor.fetchall()
        
        print(f"\nSample AI-related motivations:")
        for i, (motivation,) in enumerate(motivations[:5], 1):
            # Truncate long motivations
            if len(motivation) > 100:
                motivation = motivation[:97] + "..."
            print(f"  {i}. {motivation}")
        
        # Get statistics
        print(f"\n{'='*60}")
        print("OVERALL STATISTICS")
        print('='*60)
        
        stats_query = """
            SELECT 
                COUNT(*) as total_attendees,
                COUNT(DISTINCT organization) as unique_orgs,
                COUNT(DISTINCT detail_country) as unique_countries,
                COUNT(CASE WHEN detail_country = 'Canada' THEN 1 END) as canadian_attendees,
                COUNT(CASE WHEN detail_position_type = 'Executive' THEN 1 END) as executives,
                COUNT(CASE WHEN detail_ai_maturity IN ('Exploring', 'Implementing') THEN 1 END) as ai_explorers,
                COUNT(CASE WHEN detail_interests IS NOT NULL THEN 1 END) as with_interests,
                COUNT(CASE WHEN detail_motivation IS NOT NULL THEN 1 END) as with_motivation
            FROM attendees
        """
        
        with conn.cursor() as cursor:
            cursor.execute(stats_query)
            stats = cursor.fetchone()
        
        print(f"\n  • Total Attendees: {stats[0]:,}")
        print(f"  • Unique Organizations: {stats[1]:,}")
        print(f"  • Unique Countries: {stats[2]:,}")
        print(f"  • Canadian Attendees: {stats[3]:,} ({stats[3]/stats[0]*100:.1f}%)")
        print(f"  • Executives: {stats[4]:,} ({stats[4]/stats[0]*100:.1f}%)")
        print(f"  • AI Explorers/Implementers: {stats[5]:,} ({stats[5]/stats[0]*100:.1f}%)")
        print(f"  • With Interests: {stats[6]:,} ({stats[6]/stats[0]*100:.1f}%)")
        print(f"  • With Motivation: {stats[7]:,} ({stats[7]/stats[0]*100:.1f}%)")
        
        # Get sample data
        print(f"\n{'='*60}")
        print("SAMPLE RECORDS")
        print('='*60)
        
        sample_df = get_sample_records(conn, 3)
        for idx, row in sample_df.iterrows():
            print(f"\nRecord {idx + 1}:")
            print(f"  Name: {row['first_name']} {row['last_name']}")
            print(f"  Organization: {row['organization']}")
            print(f"  Job Title: {row['job_title']}")
            print(f"  Country: {row['detail_country']}")
            print(f"  Industry: {row['detail_industry']}")
            print(f"  Position Type: {row['detail_position_type']}")
            print(f"  Org Type: {row['detail_org_type']}")
            print(f"  AI Maturity: {row['detail_ai_maturity']}")
            print(f"  Category: {row['detail_category']}")
            if row['detail_interests']:
                interests_list = row['detail_interests'].split('|')[:3]
                print(f"  Interests: {', '.join(interests_list)}...")
            if row['detail_motivation']:
                motivation = row['detail_motivation'][:100]
                if len(row['detail_motivation']) > 100:
                    motivation += "..."
                print(f"  Motivation: {motivation}")
        
        conn.close()
        print(f"\n{'='*80}")
        print("EXPLORATION COMPLETE")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()