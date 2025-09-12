"""
Data loader utilities for All In 2025 Analytics Dashboard
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import streamlit as st
from typing import List, Dict, Optional

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_available_runs() -> List[Dict]:
    """Get all available run directories with metadata"""
    # Get the project root directory (parent of streamlit_app)
    project_root = Path(__file__).parent.parent.parent
    runs_dir = project_root / "data" / "runs"
    runs = []
    
    # Check if directory exists
    if not runs_dir.exists():
        st.error(f"Data directory not found: {runs_dir}")
        return []
    
    for run_dir in runs_dir.iterdir():
        if run_dir.is_dir() and run_dir.name != "latest":
            # Parse timestamp from directory name
            try:
                timestamp_str = run_dir.name
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H%M%S")
                
                # Check if the run has the main data files
                json_file = run_dir / "all_attendees.json"
                csv_file = run_dir / "all_attendees_with_details.csv"
                
                if json_file.exists() and csv_file.exists():
                    # Get file sizes and counts
                    with open(json_file, 'r') as f:
                        attendee_count = len(json.load(f))
                    
                    runs.append({
                        'timestamp': timestamp,
                        'timestamp_str': timestamp_str,
                        'path': str(run_dir),
                        'attendee_count': attendee_count,
                        'has_details': csv_file.exists(),
                        'display_name': timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    })
            except (ValueError, json.JSONDecodeError):
                continue
    
    # Sort by timestamp, newest first
    runs.sort(key=lambda x: x['timestamp'], reverse=True)
    return runs

@st.cache_data
def load_run_data(run_path: str, with_details: bool = True) -> pd.DataFrame:
    """Load data for a specific run"""
    run_dir = Path(run_path)
    
    if with_details:
        csv_file = run_dir / "all_attendees_with_details.csv"
        if csv_file.exists():
            df = pd.read_csv(csv_file)
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Convert empty strings to None for better handling
            df = df.replace('', None)
            
            return df
    
    # Fallback to basic JSON data
    json_file = run_dir / "all_attendees.json"
    if json_file.exists():
        with open(json_file, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    
    return pd.DataFrame()

@st.cache_data
def get_run_statistics(df: pd.DataFrame) -> Dict:
    """Calculate statistics for a run"""
    stats = {
        'total_attendees': len(df),
        'unique_companies': df['organization'].nunique() if 'organization' in df.columns else 0,
        'unique_countries': df['detail_country'].nunique() if 'detail_country' in df.columns else 0,
        'unique_industries': df['detail_industry'].nunique() if 'detail_industry' in df.columns else 0,
        'data_completeness': {},
        'top_values': {}
    }
    
    # Calculate data completeness for key fields
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
    
    # Get top values for categorical fields
    categorical_fields = [
        'detail_country', 'detail_language', 'detail_industry',
        'detail_org_type', 'detail_position_type', 'detail_ai_maturity'
    ]
    
    for field in categorical_fields:
        if field in df.columns:
            top_values = df[field].value_counts().head(10)
            stats['top_values'][field] = top_values.to_dict()
    
    return stats

@st.cache_data
def get_field_distribution(df: pd.DataFrame, field: str, top_n: int = 20) -> pd.DataFrame:
    """Get distribution of values for a specific field"""
    if field not in df.columns:
        return pd.DataFrame()
    
    value_counts = df[field].value_counts().head(top_n)
    
    # Calculate percentages
    total = len(df)
    distribution = pd.DataFrame({
        'Value': value_counts.index,
        'Count': value_counts.values,
        'Percentage': (value_counts.values / total * 100).round(2)
    })
    
    return distribution

def search_attendees(df: pd.DataFrame, search_term: str) -> pd.DataFrame:
    """Search attendees by name, email, or organization"""
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