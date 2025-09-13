"""
Test database connection from Streamlit app
Run this to verify your database connection is working
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from utils.db_connection import test_connection, get_statistics, get_new_attendees
from utils.db_queries import get_dashboard_summary, get_top_companies

def main():
    st.set_page_config(page_title="Database Connection Test", page_icon="🔌")
    
    st.title("🔌 Database Connection Test")
    st.markdown("---")
    
    # Test basic connection
    st.header("1. Connection Test")
    if test_connection():
        st.balloons()
    
    # Test statistics query
    st.header("2. Statistics Query Test")
    try:
        stats = get_statistics()
        if stats:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Attendees", f"{stats.get('total_attendees', 0):,}")
            with col2:
                st.metric("Organizations", f"{stats.get('unique_organizations', 0):,}")
            with col3:
                st.metric("Countries", f"{stats.get('unique_countries', 0):,}")
            with col4:
                st.metric("Today's Signups", f"{stats.get('today_signups', 0):,}")
            st.success("✅ Statistics query successful!")
    except Exception as e:
        st.error(f"Statistics query failed: {e}")
    
    # Test dashboard summary
    st.header("3. Dashboard Summary Test")
    try:
        summary = get_dashboard_summary()
        if summary:
            st.json(summary)
            st.success("✅ Dashboard summary query successful!")
    except Exception as e:
        st.error(f"Dashboard summary failed: {e}")
    
    # Test new attendees query
    st.header("4. New Attendees Test")
    try:
        new_attendees = get_new_attendees(hours=48, limit=5)
        if not new_attendees.empty:
            st.dataframe(new_attendees)
            st.success(f"✅ Found {len(new_attendees)} new attendees in last 48 hours!")
        else:
            st.info("No new attendees in last 48 hours")
    except Exception as e:
        st.error(f"New attendees query failed: {e}")
    
    # Test top companies
    st.header("5. Top Companies Test")
    try:
        companies = get_top_companies(limit=10)
        if not companies.empty:
            st.dataframe(companies)
            st.success("✅ Top companies query successful!")
    except Exception as e:
        st.error(f"Top companies query failed: {e}")
    
    st.markdown("---")
    st.success("🎉 All tests completed! Your database connection is working properly.")
    st.info("You can now update the main app.py to use the database instead of CSV files.")

if __name__ == "__main__":
    main()