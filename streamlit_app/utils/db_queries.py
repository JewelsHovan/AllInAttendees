"""
Specialized database queries for Streamlit dashboard
Contains complex analytics queries and aggregations
"""

import streamlit as st
import pandas as pd
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from .db_connection import run_query

@st.cache_data(ttl=600)
def get_attendees_df() -> pd.DataFrame:
    """
    Get all attendees as a DataFrame
    """
    query = """
        SELECT * FROM attendees
        ORDER BY first_seen_at DESC
    """
    return run_query(query)

def get_statistics() -> dict:
    """
    Get overall statistics from the database
    """
    query = """
        SELECT 
            COUNT(*) as total_attendees,
            COUNT(DISTINCT organization) as unique_companies,
            COUNT(DISTINCT detail_country) as unique_countries,
            COUNT(DISTINCT detail_industry) as unique_industries
        FROM attendees
    """
    result = run_query(query)
    
    if not result.empty:
        row = result.iloc[0]
        stats = {
            'total_attendees': int(row['total_attendees']),
            'unique_companies': int(row['unique_companies']),
            'unique_countries': int(row['unique_countries']),
            'unique_industries': int(row['unique_industries']),
            'data_completeness': {},
            'top_values': {}
        }
        
        # Get data completeness
        completeness_query = """
            SELECT 
                'firstName' as field, COUNT(first_name) as count, COUNT(*) as total FROM attendees
            UNION ALL
            SELECT 'lastName', COUNT(last_name), COUNT(*) FROM attendees
            UNION ALL
            SELECT 'email', COUNT(email), COUNT(*) FROM attendees
            UNION ALL
            SELECT 'organization', COUNT(organization), COUNT(*) FROM attendees
            UNION ALL
            SELECT 'jobTitle', COUNT(job_title), COUNT(*) FROM attendees
            UNION ALL
            SELECT 'detail_country', COUNT(detail_country), COUNT(*) FROM attendees
            UNION ALL
            SELECT 'detail_industry', COUNT(detail_industry), COUNT(*) FROM attendees
            UNION ALL
            SELECT 'detail_interests', COUNT(detail_interests), COUNT(*) FROM attendees
            UNION ALL
            SELECT 'detail_motivation', COUNT(detail_motivation), COUNT(*) FROM attendees
        """
        comp_result = run_query(completeness_query)
        
        for _, row in comp_result.iterrows():
            stats['data_completeness'][row['field']] = {
                'count': int(row['count']),
                'percentage': (row['count'] / row['total'] * 100) if row['total'] > 0 else 0
            }
        
        return stats
    
    return {}

def get_field_distribution(field: str, top_n: int = 20) -> pd.DataFrame:
    """
    Get distribution of values for a specific field
    """
    # Map field names to database columns
    field_mapping = {
        'organization': 'organization',
        'detail_country': 'detail_country',
        'detail_industry': 'detail_industry',
        'detail_position_type': 'detail_position_type',
        'detail_org_type': 'detail_org_type',
        'detail_ai_maturity': 'detail_ai_maturity'
    }
    
    db_field = field_mapping.get(field, field)
    
    query = f"""
        SELECT 
            {db_field} as Value,
            COUNT(*) as Count,
            ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM attendees), 2) as Percentage
        FROM attendees
        WHERE {db_field} IS NOT NULL
        GROUP BY {db_field}
        ORDER BY Count DESC
        LIMIT %s
    """
    
    return run_query(query, (top_n,))

def get_growth_metrics(days: int = 30) -> pd.DataFrame:
    """
    Get growth metrics over time
    """
    query = """
        SELECT 
            DATE(first_seen_at) as date,
            COUNT(*) as new_signups,
            SUM(COUNT(*)) OVER (ORDER BY DATE(first_seen_at)) as cumulative_total
        FROM attendees
        WHERE first_seen_at >= CURRENT_DATE - INTERVAL '%s days'
        GROUP BY DATE(first_seen_at)
        ORDER BY date
    """
    
    return run_query(query, (days,))

def get_new_attendees_summary() -> dict:
    """
    Get summary of new attendees over different periods
    """
    query = """
        SELECT 
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE THEN 1 END) as today,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '1 day' THEN 1 END) as last_24h,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as last_week,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as last_month
        FROM attendees
    """
    
    result = run_query(query)
    if not result.empty:
        row = result.iloc[0]
        return {
            'today': int(row['today']),
            'last_24h': int(row['last_24h']),
            'last_week': int(row['last_week']),
            'last_month': int(row['last_month'])
        }
    
    return {'today': 0, 'last_24h': 0, 'last_week': 0, 'last_month': 0}

def get_dashboard_summary() -> dict:
    """
    Get summary statistics for dashboard header
    """
    query = """
        WITH current_stats AS (
            SELECT 
                COUNT(*) as total_attendees,
                COUNT(DISTINCT organization) as unique_orgs,
                COUNT(DISTINCT detail_country) as unique_countries,
                COUNT(DISTINCT detail_industry) as unique_industries
            FROM attendees
        ),
        growth_stats AS (
            SELECT 
                COUNT(CASE WHEN first_seen_at >= CURRENT_DATE THEN 1 END) as today_new,
                COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '1 day' 
                      AND first_seen_at < CURRENT_DATE THEN 1 END) as yesterday_new,
                COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as week_new,
                COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as month_new
            FROM attendees
        )
        SELECT 
            c.*,
            g.*,
            CASE 
                WHEN g.yesterday_new > 0 
                THEN ROUND(100.0 * (g.today_new - g.yesterday_new) / g.yesterday_new, 1)
                ELSE 0 
            END as daily_growth_pct
        FROM current_stats c, growth_stats g
    """
    
    df = run_query(query)
    return df.iloc[0].to_dict() if not df.empty else {}

@st.cache_data(ttl=900)
def get_top_companies(limit: int = 20) -> pd.DataFrame:
    """
    Get companies with most attendees
    """
    query = """
        SELECT 
            organization,
            COUNT(*) as attendee_count,
            COUNT(DISTINCT detail_country) as countries,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as new_this_week,
            STRING_AGG(DISTINCT detail_industry, ', ' ORDER BY detail_industry) as industries
        FROM attendees
        WHERE organization IS NOT NULL 
        AND organization != ''
        GROUP BY organization
        HAVING COUNT(*) > 1
        ORDER BY attendee_count DESC
        LIMIT %s
    """
    
    return run_query(query, (limit,))

@st.cache_data(ttl=900)
def get_geographic_distribution() -> pd.DataFrame:
    """
    Get attendee distribution by country and province
    """
    query = """
        SELECT 
            detail_country as country,
            detail_province as province,
            COUNT(*) as attendee_count,
            COUNT(DISTINCT organization) as unique_orgs,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as new_this_week,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
        FROM attendees
        WHERE detail_country IS NOT NULL
        GROUP BY detail_country, detail_province
        ORDER BY attendee_count DESC
    """
    
    return run_query(query)

@st.cache_data(ttl=1800)
def get_growth_timeline(days: int = 30) -> pd.DataFrame:
    """
    Get daily growth timeline with cumulative totals
    """
    query = """
        WITH daily_data AS (
            SELECT 
                DATE(first_seen_at) as date,
                COUNT(*) as new_signups,
                COUNT(DISTINCT organization) as new_orgs,
                COUNT(DISTINCT detail_country) as new_countries
            FROM attendees
            WHERE first_seen_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(first_seen_at)
        ),
        cumulative AS (
            SELECT 
                date,
                new_signups,
                new_orgs,
                new_countries,
                SUM(new_signups) OVER (ORDER BY date) as cumulative_attendees,
                SUM(new_orgs) OVER (ORDER BY date) as cumulative_orgs,
                AVG(new_signups) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma7_signups
            FROM daily_data
        )
        SELECT 
            date,
            new_signups,
            cumulative_attendees,
            new_orgs,
            cumulative_orgs,
            new_countries,
            ROUND(ma7_signups, 1) as moving_avg_7d
        FROM cumulative
        ORDER BY date
    """
    
    return run_query(query, (days,))

@st.cache_data(ttl=900)
def get_industry_trends() -> pd.DataFrame:
    """
    Get industry distribution and trends
    """
    query = """
        WITH industry_stats AS (
            SELECT 
                detail_industry as industry,
                COUNT(*) as total,
                COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as new_this_week,
                COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '30 days' 
                      AND first_seen_at < CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as last_month,
                AVG(CASE WHEN detail_ai_maturity IS NOT NULL THEN 
                    CASE detail_ai_maturity
                        WHEN 'Not started' THEN 1
                        WHEN 'Exploring' THEN 2
                        WHEN 'Implementing' THEN 3
                        WHEN 'Scaling' THEN 4
                        WHEN 'Advanced' THEN 5
                        ELSE 0
                    END
                END) as avg_ai_maturity
            FROM attendees
            WHERE detail_industry IS NOT NULL
            GROUP BY detail_industry
        )
        SELECT 
            industry,
            total,
            new_this_week,
            CASE 
                WHEN last_month > 0 
                THEN ROUND(100.0 * new_this_week / last_month, 1)
                ELSE 0 
            END as growth_rate_pct,
            ROUND(avg_ai_maturity, 2) as avg_ai_maturity,
            ROUND(100.0 * total / SUM(total) OVER (), 2) as market_share_pct
        FROM industry_stats
        WHERE total > 5
        ORDER BY total DESC
    """
    
    return run_query(query)

@st.cache_data(ttl=900)
def get_interests_analysis() -> pd.DataFrame:
    """
    Analyze attendee interests
    """
    query = """
        WITH interest_data AS (
            SELECT 
                TRIM(interest) as interest,
                COUNT(*) as count
            FROM attendees,
            LATERAL unnest(string_to_array(detail_interests, '|')) as interest
            WHERE detail_interests IS NOT NULL
            GROUP BY TRIM(interest)
        )
        SELECT 
            interest,
            count,
            ROUND(100.0 * count / (SELECT COUNT(*) FROM attendees WHERE detail_interests IS NOT NULL), 2) as percentage
        FROM interest_data
        WHERE interest != ''
        ORDER BY count DESC
        LIMIT 30
    """
    
    return run_query(query)

@st.cache_data(ttl=600)
def get_recent_activity(hours: int = 24) -> pd.DataFrame:
    """
    Get recent signup and update activity
    """
    query = """
        WITH recent_signups AS (
            SELECT 
                'New Signup' as activity_type,
                first_name || ' ' || last_name as name,
                organization,
                detail_country as country,
                first_seen_at as timestamp
            FROM attendees
            WHERE first_seen_at >= CURRENT_TIMESTAMP - INTERVAL '%s hours'
        ),
        recent_updates AS (
            SELECT 
                'Profile Update' as activity_type,
                first_name || ' ' || last_name as name,
                organization,
                detail_country as country,
                last_updated_at as timestamp
            FROM attendees
            WHERE last_updated_at >= CURRENT_TIMESTAMP - INTERVAL '%s hours'
            AND last_updated_at > first_seen_at
        )
        SELECT * FROM (
            SELECT * FROM recent_signups
            UNION ALL
            SELECT * FROM recent_updates
        ) combined
        ORDER BY timestamp DESC
        LIMIT 100
    """
    
    return run_query(query, (hours, hours))

@st.cache_data(ttl=1800)
def get_cohort_analysis() -> pd.DataFrame:
    """
    Analyze attendee cohorts by signup week
    """
    query = """
        WITH cohorts AS (
            SELECT 
                DATE_TRUNC('week', first_seen_at) as cohort_week,
                COUNT(*) as cohort_size,
                COUNT(DISTINCT organization) as unique_orgs,
                COUNT(DISTINCT detail_country) as unique_countries,
                COUNT(CASE WHEN detail_interests IS NOT NULL THEN 1 END) as with_interests,
                COUNT(CASE WHEN biography IS NOT NULL THEN 1 END) as with_bio
            FROM attendees
            WHERE first_seen_at >= CURRENT_DATE - INTERVAL '12 weeks'
            GROUP BY DATE_TRUNC('week', first_seen_at)
        )
        SELECT 
            cohort_week,
            cohort_size,
            unique_orgs,
            unique_countries,
            ROUND(100.0 * with_interests / cohort_size, 1) as pct_with_interests,
            ROUND(100.0 * with_bio / cohort_size, 1) as pct_with_bio
        FROM cohorts
        ORDER BY cohort_week DESC
    """
    
    return run_query(query)

@st.cache_data(ttl=900)
def search_attendees(search_term: str, limit: int = 100) -> pd.DataFrame:
    """
    Search attendees by name, email, or organization
    """
    query = """
        SELECT 
            first_name,
            last_name,
            email,
            organization,
            job_title,
            detail_country,
            detail_industry,
            first_seen_at
        FROM attendees
        WHERE 
            LOWER(first_name || ' ' || last_name) LIKE LOWER(%s)
            OR LOWER(email) LIKE LOWER(%s)
            OR LOWER(organization) LIKE LOWER(%s)
            OR LOWER(job_title) LIKE LOWER(%s)
        ORDER BY last_updated_at DESC
        LIMIT %s
    """
    
    search_pattern = f"%{search_term}%"
    return run_query(query, (search_pattern, search_pattern, search_pattern, search_pattern, limit))

@st.cache_data(ttl=900)
def get_ai_maturity_analysis() -> pd.DataFrame:
    """
    Analyze AI maturity levels across industries
    """
    query = """
        SELECT 
            detail_ai_maturity as maturity_level,
            COUNT(*) as count,
            COUNT(DISTINCT organization) as unique_orgs,
            STRING_AGG(DISTINCT detail_industry, ', ' ORDER BY detail_industry) 
                FILTER (WHERE detail_industry IS NOT NULL) as top_industries,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
        FROM attendees
        WHERE detail_ai_maturity IS NOT NULL
        GROUP BY detail_ai_maturity
        ORDER BY 
            CASE detail_ai_maturity
                WHEN 'Not started' THEN 1
                WHEN 'Exploring' THEN 2
                WHEN 'Implementing' THEN 3
                WHEN 'Scaling' THEN 4
                WHEN 'Advanced' THEN 5
                ELSE 6
            END
    """
    
    return run_query(query)

def get_data_quality_metrics() -> pd.DataFrame:
    """
    Assess data completeness and quality
    """
    query = """
        SELECT 
            'Basic Information' as category,
            COUNT(*) as total,
            COUNT(first_name) as first_name_filled,
            COUNT(last_name) as last_name_filled,
            COUNT(email) as email_filled,
            COUNT(organization) as organization_filled,
            COUNT(job_title) as job_title_filled
        FROM attendees
        UNION ALL
        SELECT 
            'Profile Details' as category,
            COUNT(*) as total,
            COUNT(biography) as biography_filled,
            COUNT(detail_country) as country_filled,
            COUNT(detail_industry) as industry_filled,
            COUNT(detail_interests) as interests_filled,
            COUNT(detail_motivation) as motivation_filled
        FROM attendees
        UNION ALL
        SELECT 
            'Professional Info' as category,
            COUNT(*) as total,
            COUNT(detail_position_type) as position_filled,
            COUNT(detail_org_type) as org_type_filled,
            COUNT(detail_ai_maturity) as ai_maturity_filled,
            COUNT(website_url) as website_filled,
            COUNT(social_linkedin) as linkedin_filled
        FROM attendees
    """
    
    return run_query(query)

def get_filtered_attendees(filters: dict, limit: int = 500) -> pd.DataFrame:
    """
    Get attendees based on filter criteria
    Filters can include:
    - executives: bool - filter for executive positions
    - ai_seekers: bool - filter for AI solution seekers  
    - canada: bool - filter for Canadian attendees
    - industry: str - specific industry filter
    - org_type: str - organization type filter
    """
    
    where_clauses = []
    params = []
    
    if filters.get('executives'):
        where_clauses.append("""
            detail_position_type = 'Executive & VP'
        """)
    
    if filters.get('ai_seekers'):
        where_clauses.append("""
            detail_ai_maturity IN ('Interest, but no project', 'Pilot project underway')
        """)
    
    if filters.get('canada'):
        where_clauses.append("detail_country = 'Canada'")
    
    if filters.get('industry'):
        where_clauses.append("detail_industry = %s")
        params.append(filters['industry'])
    
    if filters.get('org_type'):
        where_clauses.append("detail_org_type = %s")
        params.append(filters['org_type'])
    
    # Build the query
    query = f"""
        SELECT 
            id,
            first_name || ' ' || last_name as name,
            email,
            organization,
            job_title,
            detail_country as country,
            detail_industry as industry,
            detail_position_type as position_type,
            detail_ai_maturity as ai_maturity,
            detail_interests as interests,
            detail_motivation as motivation,
            first_seen_at
        FROM attendees
        {'WHERE ' + ' AND '.join(where_clauses) if where_clauses else ''}
        ORDER BY first_seen_at DESC
        LIMIT %s
    """
    
    params.append(limit)
    return run_query(query, tuple(params))

def get_filter_counts(filters: dict) -> dict:
    """
    Get counts for each filter option
    """
    counts = {}
    
    # Executives count
    exec_query = """
        SELECT COUNT(*) FROM attendees
        WHERE detail_position_type IN ('Executive & VP', 'Senior Manager & Director')
           OR UPPER(job_title) LIKE '%%CEO%%'
           OR UPPER(job_title) LIKE '%%CTO%%'
           OR UPPER(job_title) LIKE '%%PRESIDENT%%'
           OR UPPER(job_title) LIKE '%%DIRECTOR%%'
           OR UPPER(job_title) LIKE '%%FOUNDER%%'
    """
    result = run_query(exec_query)
    counts['executives'] = result.iloc[0, 0] if not result.empty else 0
    
    # AI Seekers count
    ai_query = """
        SELECT COUNT(*) FROM attendees
        WHERE detail_ai_maturity IN ('Interest, but no project', 'Pilot project underway', 'Partial deployment')
           OR detail_category = 'AI Adopter'
           OR LOWER(detail_interests) LIKE '%%ai%%'
           OR LOWER(detail_motivation) LIKE '%%ai%%'
    """
    result = run_query(ai_query)
    counts['ai_seekers'] = result.iloc[0, 0] if not result.empty else 0
    
    # Canada count
    canada_query = "SELECT COUNT(*) FROM attendees WHERE detail_country = 'Canada'"
    result = run_query(canada_query)
    counts['canada'] = result.iloc[0, 0] if not result.empty else 0
    
    return counts