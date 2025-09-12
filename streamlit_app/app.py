"""
All In 2025 Analytics Dashboard
Phase 1: Basic run analysis with statistics and visualizations
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pathlib import Path
import sys
import os

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from utils.data_loader import (
    get_available_runs, 
    load_run_data, 
    get_run_statistics,
    get_field_distribution,
    search_attendees
)
from utils.visualizations import (
    create_bar_chart,
    create_pie_chart,
    create_donut_chart,
    create_completeness_chart,
    create_interests_wordcloud_data,
    create_metric_card
)

# Page configuration
st.set_page_config(
    page_title="All In 2025 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        display: flex;
        justify-content: space-around;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">🎯 All In 2025 Analytics Dashboard</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📅 Select Data Run")
    
    # Get available runs
    runs = get_available_runs()
    
    if not runs:
        st.error("No data runs found in data/runs/")
        st.stop()
    
    # Run selector
    selected_run = st.selectbox(
        "Choose a run to analyze:",
        options=runs,
        format_func=lambda x: f"{x['display_name']} ({x['attendee_count']} attendees)",
        index=0
    )
    
    st.markdown("---")
    
    # Run info
    st.subheader("ℹ️ Run Information")
    st.write(f"**Date:** {selected_run['timestamp'].strftime('%B %d, %Y')}")
    st.write(f"**Time:** {selected_run['timestamp'].strftime('%I:%M %p')}")
    st.write(f"**Total Attendees:** {selected_run['attendee_count']:,}")
    st.write(f"**Has Details:** {'✅' if selected_run['has_details'] else '❌'}")
    
    st.markdown("---")
    
    # Refresh button
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# Load data for selected run
with st.spinner(f"Loading data from {selected_run['display_name']}..."):
    df = load_run_data(selected_run['path'], with_details=True)
    stats = get_run_statistics(df)

# Main content area
# Key Metrics
st.header("📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Attendees",
        value=f"{stats['total_attendees']:,}"
    )

with col2:
    st.metric(
        label="Unique Companies",
        value=f"{stats['unique_companies']:,}"
    )

with col3:
    st.metric(
        label="Countries Represented",
        value=f"{stats['unique_countries']:,}"
    )

with col4:
    st.metric(
        label="Industries",
        value=f"{stats['unique_industries']:,}"
    )

st.markdown("---")

# Create tabs for different analyses
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🌍 Geographic Distribution",
    "🏢 Industry & Organization",
    "👥 Roles & Positions",
    "🎯 Interests & Motivations",
    "📋 Data Quality"
])

with tab1:
    st.header("Geographic Distribution")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Country distribution
        if 'detail_country' in df.columns:
            country_dist = get_field_distribution(df, 'detail_country', top_n=20)
            if not country_dist.empty:
                fig = create_bar_chart(
                    country_dist,
                    title="Top 20 Countries",
                    y_label="Country"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Language distribution
        if 'detail_language' in df.columns:
            lang_dist = get_field_distribution(df, 'detail_language', top_n=10)
            if not lang_dist.empty:
                fig = create_pie_chart(
                    lang_dist,
                    title="Language Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Province distribution for specific countries
    if 'detail_province' in df.columns:
        st.subheader("Provincial Distribution")
        province_dist = get_field_distribution(df, 'detail_province', top_n=15)
        if not province_dist.empty:
            fig = create_bar_chart(
                province_dist,
                title="Top Provinces/States",
                y_label="Province/State",
                color_scale="Greens"
            )
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Industry & Organization Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Industry distribution
        if 'detail_industry' in df.columns:
            industry_dist = get_field_distribution(df, 'detail_industry', top_n=15)
            if not industry_dist.empty:
                fig = create_bar_chart(
                    industry_dist,
                    title="Top Industries",
                    y_label="Industry",
                    color_scale="Oranges"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Organization type
        if 'detail_org_type' in df.columns:
            org_dist = get_field_distribution(df, 'detail_org_type', top_n=10)
            if not org_dist.empty:
                fig = create_pie_chart(
                    org_dist,
                    title="Organization Types"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # AI Maturity
    if 'detail_ai_maturity' in df.columns:
        st.subheader("AI Maturity Distribution")
        ai_dist = get_field_distribution(df, 'detail_ai_maturity', top_n=10)
        if not ai_dist.empty:
            fig = create_bar_chart(
                ai_dist,
                title="Organization AI Maturity Levels",
                y_label="Maturity Level",
                color_scale="Purples"
            )
            st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Roles & Positions")
    
    # Position type distribution
    if 'detail_position_type' in df.columns:
        position_dist = get_field_distribution(df, 'detail_position_type', top_n=15)
        if not position_dist.empty:
            fig = create_bar_chart(
                position_dist,
                title="Position Types",
                y_label="Position",
                color_scale="Reds"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Top job titles
    if 'jobTitle' in df.columns:
        st.subheader("Top Job Titles")
        job_dist = get_field_distribution(df, 'jobTitle', top_n=20)
        if not job_dist.empty:
            fig = create_bar_chart(
                job_dist,
                title="Most Common Job Titles",
                y_label="Job Title",
                color_scale="Viridis"
            )
            st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.header("Interests & Motivations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Interests
        if 'detail_interests' in df.columns:
            interests_data = create_interests_wordcloud_data(df)
            if not interests_data.empty:
                fig = create_bar_chart(
                    interests_data.head(15),
                    title="Top 15 Interests",
                    y_label="Interest",
                    color_scale="Teal"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Motivation
        if 'detail_motivation' in df.columns:
            motivation_dist = get_field_distribution(df, 'detail_motivation', top_n=10)
            if not motivation_dist.empty:
                fig = create_pie_chart(
                    motivation_dist,
                    title="Attendee Motivations"
                )
                st.plotly_chart(fig, use_container_width=True)
    
    # Category distribution
    if 'detail_category' in df.columns:
        st.subheader("Attendee Categories")
        category_dist = get_field_distribution(df, 'detail_category', top_n=10)
        if not category_dist.empty:
            fig = create_bar_chart(
                category_dist,
                title="Attendee Categories",
                y_label="Category",
                color_scale="Rainbow"
            )
            st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.header("Data Quality & Completeness")
    
    # Data completeness chart
    fig = create_completeness_chart(stats['data_completeness'])
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed completeness table
    st.subheader("Field Completeness Details")
    
    completeness_df = pd.DataFrame([
        {
            'Field': field.replace('detail_', '').replace('_', ' ').title(),
            'Filled': data['count'],
            'Missing': stats['total_attendees'] - data['count'],
            'Completeness': f"{data['percentage']:.1f}%"
        }
        for field, data in stats['data_completeness'].items()
    ])
    
    completeness_df = completeness_df.sort_values('Filled', ascending=False)
    
    st.dataframe(
        completeness_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Filled": st.column_config.NumberColumn(format="%d"),
            "Missing": st.column_config.NumberColumn(format="%d"),
            "Completeness": st.column_config.ProgressColumn(
                min_value=0,
                max_value=100,
                format="%s"
            )
        }
    )

st.markdown("---")

# Search and Filter Section
st.header("🔍 Search Attendees")

col1, col2 = st.columns([3, 1])

with col1:
    search_term = st.text_input(
        "Search by name, email, organization, or job title:",
        placeholder="Enter search term..."
    )

with col2:
    search_button = st.button("🔍 Search", use_container_width=True)

if search_term and search_button:
    filtered_df = search_attendees(df, search_term)
    
    st.subheader(f"Search Results ({len(filtered_df)} found)")
    
    if len(filtered_df) > 0:
        # Display columns
        display_columns = [
            'firstName', 'lastName', 'email', 'organization', 
            'jobTitle', 'detail_country', 'detail_industry'
        ]
        display_columns = [col for col in display_columns if col in filtered_df.columns]
        
        st.dataframe(
            filtered_df[display_columns],
            use_container_width=True,
            hide_index=True
        )
        
        # Download button for search results
        csv = filtered_df[display_columns].to_csv(index=False)
        st.download_button(
            label="📥 Download Search Results (CSV)",
            data=csv,
            file_name=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No attendees found matching your search criteria.")

# Footer
st.markdown("---")
st.markdown(
    f"""
    <div style='text-align: center; color: #666; padding: 20px;'>
        📊 All In 2025 Analytics Dashboard | 
        Data from: {selected_run['display_name']} | 
        Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """,
    unsafe_allow_html=True
)