"""
Data loading utilities for All In 2025 Analytics Dashboard
Handles both live database connections and historical CSV/JSON files
"""

import json
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Dict, List, Optional
import os
from datetime import datetime, timedelta

# Import database functions
from .db_queries import (
    get_attendees_df,
    get_statistics,
    get_recent_activity,
    get_field_distribution as db_get_field_distribution,
    get_growth_metrics as db_get_growth_metrics,
    get_new_attendees_summary as db_get_new_attendees_summary,
    search_attendees as db_search_attendees,
    get_ai_maturity_analysis as db_get_ai_maturity_analysis
)
from .db_connection import run_query

# Data directory configuration - use absolute path
BASE_DIR = Path(__file__).parent.parent.parent  # Go up to project root
DATA_DIR = BASE_DIR / "data" / "runs"

@st.cache_data(ttl=600)
def get_available_runs() -> List[str]:
    """
    Get list of available historical runs from the runs directory
    """
    runs = []
    
    if DATA_DIR.exists():
        for run_dir in DATA_DIR.iterdir():
            if run_dir.is_dir() and run_dir.name.startswith('202'):
                # Parse directory name to get date
                run_name = run_dir.name
                runs.append(run_name)
    
    # Sort runs by date (newest first)
    runs.sort(reverse=True)
    
    # Add "Latest" option for live database
    runs = ['Latest'] + runs
    
    return runs

@st.cache_data(ttl=600)
def load_run_data(run_id: Optional[str] = None, with_details: bool = True) -> pd.DataFrame:
    """
    Load data for a specific run or latest from database
    """
    if run_id is None or run_id == 'Latest':
        # Load from database
        return get_attendees_df()
    
    # Load from historical run directory
    run_dir = DATA_DIR / run_id
    
    if not run_dir.exists():
        st.error(f"Run directory not found: {run_id}")
        return pd.DataFrame()
    
    # Determine which file to load
    if with_details:
        # Try to load detailed CSV first
        csv_file = run_dir / "all_attendees_with_details.csv"
        if not csv_file.exists():
            csv_file = run_dir / "all_attendees_organized.csv"
        if not csv_file.exists():
            csv_file = run_dir / "all_attendees.csv"
    else:
        csv_file = run_dir / "all_attendees.csv"
    
    if not csv_file.exists():
        st.error(f"No data file found in {run_id}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(csv_file)
        
        # Ensure column name consistency (some files might have different naming)
        column_mapping = {
            'first_name': 'firstName',
            'last_name': 'lastName', 
            'email': 'email',
            'job_title': 'jobTitle',
            'photo_url': 'photoUrl',
            'user_id': 'userId'
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]
        
        return df
    except Exception as e:
        st.error(f"Error loading data from {run_id}: {str(e)}")
        return pd.DataFrame()

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
        return get_statistics()

def get_field_distribution(field: str, top_n: int = 20, df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Get distribution of values for a specific field
    Can work with provided DataFrame or fetch from database
    """
    if df is not None and not df.empty:
        # Calculate from DataFrame
        if field not in df.columns:
            return pd.DataFrame()
        
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
    return db_get_growth_metrics(days)

@st.cache_data(ttl=300)
def get_ai_maturity_analysis() -> pd.DataFrame:
    """Get AI maturity analysis from database"""
    return db_get_ai_maturity_analysis()

@st.cache_data(ttl=600)
def get_new_attendees_summary() -> Dict:
    """Get summary of new attendees over different periods"""
    return db_get_new_attendees_summary()

# Period comparison function
def compare_periods(period1_start: str, period1_end: str, 
                   period2_start: str, period2_end: str) -> Dict:
    """
    Compare two time periods for growth analysis
    """
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
            p2.count as period2_count,
            p2.count - p1.count as new_signups,
            p1.orgs as period1_orgs,
            p2.orgs as period2_orgs,
            p1.countries as period1_countries,
            p2.countries as period2_countries,
            CASE 
                WHEN p1.count > 0 
                THEN ROUND(100.0 * (p2.count - p1.count) / p1.count, 1)
                ELSE 0 
            END as growth_rate
        FROM period1 p1, period2 p2
    """
    
    df = run_query(query, (period1_start, period1_end, period2_start, period2_end))
    return df.to_dict('records')[0] if not df.empty else {}

def get_new_attendees_for_historical_run(current_run_df: pd.DataFrame, run_id: str) -> pd.DataFrame:
    """
    For historical runs, compare with previous run to find new attendees
    """
    # Get list of all runs
    runs = get_available_runs()
    
    # Find the current run and previous run
    run_dates = sorted([r for r in runs if r != 'Latest'])
    
    try:
        current_idx = run_dates.index(run_id)
        if current_idx == 0:
            # This is the first run, all attendees are new
            new_attendees = current_run_df.copy()
            new_attendees['activity_type'] = 'New Signup'
            new_attendees['name'] = new_attendees['firstName'] + ' ' + new_attendees['lastName']
            new_attendees['country'] = new_attendees.get('detail_country', '')
            new_attendees['timestamp'] = pd.Timestamp.now()  # Use current time as placeholder
            return new_attendees[['activity_type', 'name', 'organization', 'country', 'timestamp']].head(100)
        
        # Load previous run
        prev_run_id = run_dates[current_idx - 1]
        prev_run_df = load_run_data(prev_run_id)
        
        # Find new attendees (in current but not in previous)
        if 'id' in current_run_df.columns and 'id' in prev_run_df.columns:
            prev_ids = set(prev_run_df['id'].dropna())
            current_ids = set(current_run_df['id'].dropna())
            new_ids = current_ids - prev_ids
            
            new_attendees = current_run_df[current_run_df['id'].isin(new_ids)].copy()
        elif 'email' in current_run_df.columns and 'email' in prev_run_df.columns:
            # Fallback to email comparison
            prev_emails = set(prev_run_df['email'].dropna())
            current_emails = set(current_run_df['email'].dropna())
            new_emails = current_emails - prev_emails
            
            new_attendees = current_run_df[current_run_df['email'].isin(new_emails)].copy()
        else:
            # Can't determine new attendees
            return pd.DataFrame()
        
        # Format the output
        if not new_attendees.empty:
            new_attendees['activity_type'] = 'New Signup'
            new_attendees['name'] = new_attendees['firstName'] + ' ' + new_attendees['lastName']
            new_attendees['country'] = new_attendees.get('detail_country', '')
            new_attendees['timestamp'] = pd.Timestamp(run_id.split('_')[0])  # Use run date
            
            return new_attendees[['activity_type', 'name', 'organization', 'country', 'timestamp']].head(100)
        
        return pd.DataFrame()
        
    except (ValueError, IndexError) as e:
        # Run not found in list or other error
        return pd.DataFrame()