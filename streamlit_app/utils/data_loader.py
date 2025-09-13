"""
Data loader utilities for All In 2025 Analytics Dashboard
Now uses PostgreSQL database instead of CSV files
"""

import pandas as pd
from datetime import datetime
import streamlit as st
from typing import List, Dict, Optional
from .db_connection import run_query, get_statistics, get_attendees, get_field_distribution as db_get_field_distribution
from .db_queries import (
    get_dashboard_summary, 
    get_top_companies,
    get_geographic_distribution,
    get_industry_trends,
    get_interests_analysis,
    search_attendees as db_search_attendees,
    get_recent_activity,
    get_ai_maturity_analysis
)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_available_runs() -> List[Dict]:
    """Get all available runs from database"""
    query = """
        SELECT 
            id,
            run_timestamp,
            run_date,
            total_attendees,
            new_attendees,
            updated_attendees,
            status
        FROM scraper_runs
        ORDER BY run_timestamp DESC
        LIMIT 30
    """
    
    df = run_query(query)
    
    if df.empty:
        return []
    
    runs = []
    for _, row in df.iterrows():
        runs.append({
            'id': row['id'],
            'timestamp': row['run_timestamp'],
            'timestamp_str': row['run_timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
            'attendee_count': row['total_attendees'],
            'new_attendees': row.get('new_attendees', 0),
            'updated_attendees': row.get('updated_attendees', 0),
            'status': row.get('status', 'completed'),
            'display_name': row['run_timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        })
    
    return runs

@st.cache_data(ttl=600)
def load_run_data(run_id: Optional[int] = None, with_details: bool = True) -> pd.DataFrame:
    """
    Load attendee data from database
    If run_id is None, loads all current attendees
    If run_id is specified, loads attendees from that specific run
    """
    if run_id:
        # Load specific run
        query = """
            SELECT 
                a.*,
                sr.run_timestamp as run_date
            FROM attendees a
            JOIN scraper_runs sr ON a.last_seen_run_id = sr.id
            WHERE a.last_seen_run_id = %s
            ORDER BY a.last_updated_at DESC
        """
        df = run_query(query, (run_id,))
    else:
        # Load all current attendees
        query = """
            SELECT 
                *,
                CASE 
                    WHEN first_seen_at >= CURRENT_DATE THEN 'New Today'
                    WHEN first_seen_at >= CURRENT_DATE - INTERVAL '7 days' THEN 'New This Week'
                    ELSE 'Existing'
                END as signup_status
            FROM attendees
            ORDER BY last_updated_at DESC
        """
        df = run_query(query)
    
    # Rename columns to match old format for compatibility
    if not df.empty:
        column_mapping = {
            'first_name': 'firstName',
            'last_name': 'lastName',
            'job_title': 'jobTitle',
            'website_url': 'websiteUrl',
            'photo_url': 'photoUrl',
            'user_id': 'userId'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]
    
    return df

@st.cache_data(ttl=300)
def get_run_statistics(df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Calculate statistics for current data
    If df is provided, calculates from DataFrame
    Otherwise fetches from database
    """
    if df is not None and not df.empty:
        # Calculate from DataFrame (backward compatibility)
        stats = {
            'total_attendees': len(df),
            'unique_companies': df['organization'].nunique() if 'organization' in df.columns else 0,
            'unique_countries': df['detail_country'].nunique() if 'detail_country' in df.columns else 0,
            'unique_industries': df['detail_industry'].nunique() if 'detail_industry' in df.columns else 0,
            'data_completeness': {},
            'top_values': {}
        }
        
        # Calculate data completeness
        key_fields = [
            'firstName', 'lastName', 'email', 'organization', 'jobTitle',
            'detail_country', 'detail_industry', 'detail_language', 
            'detail_interests', 'detail_motivation'
        ]
        
        for field in key_fields:
            if field in df.columns:
                non_null_count = df[field].notna().sum()
                stats['data_completeness'][field] = {
                    'count': non_null_count,
                    'percentage': (non_null_count / len(df) * 100) if len(df) > 0 else 0
                }
        
        return stats
    else:
        # Fetch from database
        return get_dashboard_summary()

@st.cache_data(ttl=600)
def get_field_distribution(field: str, top_n: int = 20, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Get distribution of values for a specific field
    Can work with provided DataFrame or fetch from database
    """
    if df is not None and not df.empty and field in df.columns:
        # Calculate from DataFrame
        value_counts = df[field].value_counts().head(top_n)
        
        total = len(df)
        distribution = pd.DataFrame({
            'Value': value_counts.index,
            'Count': value_counts.values,
            'Percentage': (value_counts.values / total * 100).round(2)
        })
        
        return distribution
    else:
        # Fetch from database
        return db_get_field_distribution(field, top_n)

def search_attendees(search_term: str, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Search attendees by name, email, or organization
    Can work with provided DataFrame or fetch from database
    """
    if df is not None and not df.empty:
        # Search in DataFrame
        if not search_term:
            return df
        
        search_term = search_term.lower()
        
        # Define searchable columns
        search_columns = ['firstName', 'lastName', 'email', 'organization', 'jobTitle']
        
        # Create a mask for matching rows
        mask = pd.Series([False] * len(df))
        
        for col in search_columns:
            if col in df.columns:
                mask |= df[col].astype(str).str.lower().str.contains(search_term, na=False)
        
        return df[mask]
    else:
        # Search in database
        return db_search_attendees(search_term)

# New database-specific functions
@st.cache_data(ttl=600)
def get_growth_metrics(days: int = 30) -> pd.DataFrame:
    """Get growth metrics from database"""
    query = """
        WITH daily_signups AS (
            SELECT 
                DATE(first_seen_at) as date,
                COUNT(*) as new_signups
            FROM attendees
            WHERE first_seen_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(first_seen_at)
        ),
        cumulative AS (
            SELECT 
                date,
                new_signups,
                SUM(new_signups) OVER (ORDER BY date) as cumulative_total
            FROM daily_signups
        )
        SELECT * FROM cumulative ORDER BY date
    """
    return run_query(query, (days,))

@st.cache_data(ttl=300)
def get_new_attendees_summary() -> Dict:
    """Get summary of new attendees"""
    query = """
        SELECT 
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE THEN 1 END) as today,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '1 day' 
                  AND first_seen_at < CURRENT_DATE THEN 1 END) as yesterday,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as this_week,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as this_month
        FROM attendees
    """
    df = run_query(query)
    return df.iloc[0].to_dict() if not df.empty else {}

@st.cache_data(ttl=600)
def get_comparison_data(period1_start: str, period1_end: str, 
                        period2_start: str, period2_end: str) -> Dict:
    """Compare two time periods"""
    query = """
        WITH period1 AS (
            SELECT 
                COUNT(*) as count,
                COUNT(DISTINCT organization) as orgs,
                COUNT(DISTINCT detail_country) as countries
            FROM attendees
            WHERE first_seen_at >= %s::date AND first_seen_at < %s::date
        ),
        period2 AS (
            SELECT 
                COUNT(*) as count,
                COUNT(DISTINCT organization) as orgs,
                COUNT(DISTINCT detail_country) as countries
            FROM attendees
            WHERE first_seen_at >= %s::date AND first_seen_at < %s::date
        )
        SELECT 
            p1.count as period1_count,
            p1.orgs as period1_orgs,
            p1.countries as period1_countries,
            p2.count as period2_count,
            p2.orgs as period2_orgs,
            p2.countries as period2_countries,
            CASE WHEN p1.count > 0 
                THEN ROUND(100.0 * (p2.count - p1.count) / p1.count, 1)
                ELSE 0 
            END as growth_rate
        FROM period1 p1, period2 p2
    """
    
    df = run_query(query, (period1_start, period1_end, period2_start, period2_end))
    return df.iloc[0].to_dict() if not df.empty else {}