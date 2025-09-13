"""
Database connection manager for Streamlit app
Handles PostgreSQL connections with caching and error handling
"""

import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_resource
def init_connection():
    """
    Initialize database connection
    Uses Streamlit secrets for credentials
    Cached as a resource to reuse connection
    """
    try:
        # Use connection pooler by default
        connection = psycopg2.connect(**st.secrets["postgres"])
        logger.info("Database connection established successfully")
        return connection
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        logger.error(f"Database connection failed: {e}")
        return None

def get_connection():
    """
    Get or create database connection
    Handles reconnection if needed
    """
    try:
        conn = init_connection()
        # Test if connection is alive
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return conn
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        # Connection lost, clear cache and reconnect
        st.cache_resource.clear()
        return init_connection()

@st.cache_data(ttl=600)  # Default 10 minute cache
def run_query(query: str, params: Optional[tuple] = None, ttl: Optional[int] = None) -> pd.DataFrame:
    """
    Execute a query and return results as DataFrame
    
    Args:
        query: SQL query to execute
        params: Query parameters for safe parameterized queries
        ttl: Cache time-to-live in seconds (overrides default)
    
    Returns:
        DataFrame with query results
    """
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        # Use different cache TTL if specified
        if ttl is not None:
            run_query.clear()  # Clear cache for this specific query
            
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Query failed: {str(e)}")
        logger.error(f"Query execution failed: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)  # 5 minute cache for stats
def get_statistics() -> Dict[str, Any]:
    """
    Get overall database statistics
    Cached for 5 minutes
    """
    query = """
        SELECT 
            COUNT(*) as total_attendees,
            COUNT(DISTINCT organization) as unique_organizations,
            COUNT(DISTINCT detail_country) as unique_countries,
            COUNT(DISTINCT detail_industry) as unique_industries,
            COUNT(CASE WHEN detail_interests IS NOT NULL THEN 1 END) as with_interests,
            COUNT(CASE WHEN biography IS NOT NULL THEN 1 END) as with_biography,
            MIN(first_seen_at) as earliest_signup,
            MAX(last_updated_at) as latest_update,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE THEN 1 END) as today_signups,
            COUNT(CASE WHEN first_seen_at >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as week_signups
        FROM attendees
    """
    
    df = run_query(query)
    if not df.empty:
        return df.iloc[0].to_dict()
    return {}

@st.cache_data(ttl=900)  # 15 minute cache
def get_attendees(limit: Optional[int] = None, 
                  offset: int = 0,
                  filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Get attendees with optional filtering
    
    Args:
        limit: Maximum number of results
        offset: Skip this many results (for pagination)
        filters: Dictionary of column:value filters
    
    Returns:
        DataFrame of attendees
    """
    query = """
        SELECT 
            id,
            first_name,
            last_name,
            email,
            organization,
            job_title,
            detail_country,
            detail_industry,
            detail_interests,
            first_seen_at,
            last_updated_at
        FROM attendees
        WHERE 1=1
    """
    
    params = []
    
    # Add filters if provided
    if filters:
        for column, value in filters.items():
            if value:
                query += f" AND {column} = %s"
                params.append(value)
    
    query += " ORDER BY last_updated_at DESC"
    
    if limit:
        query += f" LIMIT {limit}"
    if offset:
        query += f" OFFSET {offset}"
    
    return run_query(query, tuple(params) if params else None)

@st.cache_data(ttl=1800)  # 30 minute cache for historical data
def get_growth_metrics(days: int = 30) -> pd.DataFrame:
    """
    Get growth metrics for the specified number of days
    
    Args:
        days: Number of days to look back
    
    Returns:
        DataFrame with daily growth metrics
    """
    query = """
        WITH daily_signups AS (
            SELECT 
                DATE(first_seen_at) as signup_date,
                COUNT(*) as new_signups
            FROM attendees
            WHERE first_seen_at >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY DATE(first_seen_at)
        ),
        cumulative AS (
            SELECT 
                signup_date,
                new_signups,
                SUM(new_signups) OVER (ORDER BY signup_date) as cumulative_total,
                LAG(new_signups) OVER (ORDER BY signup_date) as prev_day_signups
            FROM daily_signups
        )
        SELECT 
            signup_date,
            new_signups,
            cumulative_total,
            CASE 
                WHEN prev_day_signups > 0 
                THEN ROUND(100.0 * (new_signups - prev_day_signups) / prev_day_signups, 2)
                ELSE NULL 
            END as growth_rate_pct
        FROM cumulative
        ORDER BY signup_date DESC
    """
    
    return run_query(query, (days,))

@st.cache_data(ttl=600)  # 10 minute cache
def get_new_attendees(hours: int = 24, limit: int = 100) -> pd.DataFrame:
    """
    Get recently signed up attendees
    
    Args:
        hours: Look back this many hours
        limit: Maximum results to return
    
    Returns:
        DataFrame of new attendees
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
        WHERE first_seen_at >= CURRENT_TIMESTAMP - INTERVAL '%s hours'
        ORDER BY first_seen_at DESC
        LIMIT %s
    """
    
    return run_query(query, (hours, limit))

@st.cache_data(ttl=900)  # 15 minute cache
def get_field_distribution(field: str, top_n: int = 20) -> pd.DataFrame:
    """
    Get distribution of values for a specific field
    
    Args:
        field: Column name to analyze
        top_n: Number of top values to return
    
    Returns:
        DataFrame with value counts and percentages
    """
    # Validate field name to prevent SQL injection
    allowed_fields = [
        'detail_country', 'detail_industry', 'detail_language',
        'detail_org_type', 'detail_position_type', 'detail_ai_maturity',
        'organization', 'detail_province'
    ]
    
    if field not in allowed_fields:
        st.error(f"Invalid field: {field}")
        return pd.DataFrame()
    
    query = f"""
        WITH counts AS (
            SELECT 
                {field} as value,
                COUNT(*) as count
            FROM attendees
            WHERE {field} IS NOT NULL
            GROUP BY {field}
            ORDER BY count DESC
            LIMIT %s
        ),
        total AS (
            SELECT COUNT(*) as total FROM attendees WHERE {field} IS NOT NULL
        )
        SELECT 
            c.value,
            c.count,
            ROUND(100.0 * c.count / t.total, 2) as percentage
        FROM counts c, total t
        ORDER BY c.count DESC
    """
    
    return run_query(query, (top_n,))

def clear_all_caches():
    """
    Clear all cached data
    Useful for forcing refresh
    """
    st.cache_data.clear()
    st.success("All caches cleared!")

def test_connection() -> bool:
    """
    Test database connection
    
    Returns:
        True if connection successful, False otherwise
    """
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM attendees")
                count = cur.fetchone()[0]
                st.success(f"✅ Database connected! {count:,} attendees found.")
                return True
        except Exception as e:
            st.error(f"❌ Connection test failed: {e}")
            return False
    return False

# Utility function for manual refresh
def add_refresh_button():
    """
    Add a refresh button to the sidebar
    """
    if st.sidebar.button("🔄 Refresh All Data"):
        clear_all_caches()
        st.rerun()