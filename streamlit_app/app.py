"""
All In 2025 Analytics Dashboard
Enhanced with PostgreSQL database for real-time data and historical tracking
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
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
    search_attendees,
    get_growth_metrics,
    get_new_attendees_summary,
    get_comparison_data
)
from utils.visualizations import (
    create_bar_chart,
    create_pie_chart,
    create_donut_chart,
    create_completeness_chart,
    create_interests_wordcloud_data,
    create_metric_card
)
from utils.db_connection import (
    test_connection,
    get_statistics,
    add_refresh_button,
    clear_all_caches
)
from utils.db_queries import (
    get_dashboard_summary,
    get_top_companies,
    get_geographic_distribution,
    get_industry_trends,
    get_interests_analysis,
    get_recent_activity,
    get_growth_timeline,
    get_ai_maturity_analysis
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
    .growth-positive {
        color: #28a745;
        font-weight: bold;
    }
    .growth-negative {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<h1 class="main-header">🎯 All In 2025 Analytics Dashboard</h1>', unsafe_allow_html=True)

# Test database connection on first load
if 'db_connected' not in st.session_state:
    with st.spinner("Connecting to database..."):
        if test_connection():
            st.session_state.db_connected = True
        else:
            st.error("Failed to connect to database. Please check your configuration.")
            st.stop()

# Get dashboard summary
summary = get_dashboard_summary()

# Display key metrics at the top
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Attendees", 
        f"{summary.get('total_attendees', 0):,}",
        f"+{summary.get('today_new', 0)} today"
    )

with col2:
    st.metric(
        "Organizations", 
        f"{summary.get('unique_orgs', 0):,}",
        f"+{summary.get('week_new', 0) if summary.get('week_new', 0) > 0 else 0} this week"
    )

with col3:
    st.metric(
        "Countries", 
        f"{summary.get('unique_countries', 0):,}"
    )

with col4:
    st.metric(
        "Industries", 
        f"{summary.get('unique_industries', 0):,}"
    )

with col5:
    growth_pct = summary.get('daily_growth_pct', 0)
    st.metric(
        "Daily Growth", 
        f"{growth_pct:+.1f}%",
        "vs yesterday"
    )

st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("🔍 Data Selection")
    
    # Data source selector
    data_source = st.radio(
        "Data Source:",
        ["Live Database", "Historical Runs"],
        index=0
    )
    
    if data_source == "Live Database":
        st.success("📡 Connected to live database")
        st.markdown("Data updates automatically when new attendees sign up")
        
        # Refresh button
        add_refresh_button()
        
        # Load current data
        df = load_run_data()
        
    else:
        # Get available runs from database
        runs = get_available_runs()
        
        if not runs:
            st.error("No historical runs found")
            st.stop()
        
        # Run selector
        selected_run = st.selectbox(
            "Choose a run to analyze:",
            options=runs,
            format_func=lambda x: f"{x['display_name']} ({x['attendee_count']} attendees, +{x.get('new_attendees', 0)} new)",
            index=0
        )
        
        # Run info
        st.subheader("ℹ️ Run Information")
        st.write(f"**Date:** {selected_run['timestamp'].strftime('%B %d, %Y')}")
        st.write(f"**Time:** {selected_run['timestamp'].strftime('%I:%M %p')}")
        st.write(f"**Total:** {selected_run['attendee_count']:,}")
        st.write(f"**New:** {selected_run.get('new_attendees', 0):,}")
        st.write(f"**Updated:** {selected_run.get('updated_attendees', 0):,}")
        
        # Load selected run data
        df = load_run_data(selected_run['id'])
    
    st.markdown("---")
    
    # Search
    st.subheader("🔍 Search Attendees")
    search_term = st.text_input("Search by name, email, or organization")
    
    if search_term:
        search_results = search_attendees(search_term, df)
        st.write(f"Found {len(search_results)} matches")

# Main content area with tabs
tabs = st.tabs([
    "📊 Overview", 
    "📈 Growth Analytics",
    "🌍 Geographic Distribution", 
    "🏢 Industries & Organizations", 
    "👥 Roles & Positions",
    "🎯 Interests & AI Maturity",
    "🆕 New Attendees",
    "📋 Data Quality"
])

# Tab 1: Overview
with tabs[0]:
    st.header("📊 Overview Statistics")
    
    # Get statistics
    stats = get_run_statistics(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Key Metrics")
        st.write(f"**Total Attendees:** {stats['total_attendees']:,}")
        st.write(f"**Unique Organizations:** {stats['unique_companies']:,}")
        st.write(f"**Countries Represented:** {stats['unique_countries']:,}")
        st.write(f"**Industries:** {stats['unique_industries']:,}")
        
        # New attendees summary
        new_summary = get_new_attendees_summary()
        st.subheader("🆕 Recent Signups")
        st.write(f"**Today:** {new_summary.get('today', 0):,}")
        st.write(f"**Yesterday:** {new_summary.get('yesterday', 0):,}")
        st.write(f"**This Week:** {new_summary.get('this_week', 0):,}")
        st.write(f"**This Month:** {new_summary.get('this_month', 0):,}")
    
    with col2:
        # Top companies chart
        st.subheader("🏢 Top Organizations")
        top_companies = get_top_companies(15)
        if not top_companies.empty:
            fig = px.bar(
                top_companies.head(10), 
                x='attendee_count', 
                y='organization',
                orientation='h',
                title="Organizations with Most Attendees",
                labels={'attendee_count': 'Number of Attendees', 'organization': 'Organization'}
            )
            fig.update_layout(height=400, yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)

# Tab 2: Growth Analytics (NEW!)
with tabs[1]:
    st.header("📈 Growth Analytics")
    
    # Date range selector
    col1, col2 = st.columns([2, 3])
    with col1:
        days_back = st.slider("Days to analyze:", 7, 90, 30)
    
    # Get growth data
    growth_data = get_growth_timeline(days_back)
    
    if not growth_data.empty:
        # Growth chart
        fig = go.Figure()
        
        # Add bar chart for daily signups
        fig.add_trace(go.Bar(
            x=growth_data['date'],
            y=growth_data['new_signups'],
            name='Daily Signups',
            marker_color='lightblue',
            yaxis='y'
        ))
        
        # Add line chart for cumulative
        fig.add_trace(go.Scatter(
            x=growth_data['date'],
            y=growth_data['cumulative_attendees'],
            name='Cumulative Total',
            line=dict(color='darkblue', width=3),
            yaxis='y2'
        ))
        
        # Add moving average
        if 'moving_avg_7d' in growth_data.columns:
            fig.add_trace(go.Scatter(
                x=growth_data['date'],
                y=growth_data['moving_avg_7d'],
                name='7-Day Moving Avg',
                line=dict(color='orange', dash='dash'),
                yaxis='y'
            ))
        
        fig.update_layout(
            title="Attendee Growth Over Time",
            xaxis_title="Date",
            yaxis=dict(title="Daily Signups", side="left"),
            yaxis2=dict(title="Cumulative Total", overlaying="y", side="right"),
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Growth statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_daily = growth_data['new_signups'].mean()
            st.metric("Average Daily Signups", f"{avg_daily:.1f}")
        
        with col2:
            max_day = growth_data.loc[growth_data['new_signups'].idxmax()]
            st.metric("Best Day", f"{max_day['new_signups']:,}", f"{max_day['date'].strftime('%b %d')}")
        
        with col3:
            total_growth = growth_data['new_signups'].sum()
            st.metric(f"Total in {days_back} Days", f"{total_growth:,}")

# Tab 3: Geographic Distribution
with tabs[2]:
    st.header("🌍 Geographic Distribution")
    
    geo_data = get_geographic_distribution()
    
    if not geo_data.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Country map
            country_summary = geo_data.groupby('country').agg({
                'attendee_count': 'sum',
                'unique_orgs': 'sum',
                'new_this_week': 'sum'
            }).reset_index()
            
            fig = px.choropleth(
                country_summary,
                locations='country',
                locationmode='country names',
                color='attendee_count',
                hover_data=['unique_orgs', 'new_this_week'],
                title='Attendees by Country',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Top countries list
            st.subheader("Top Countries")
            top_countries = country_summary.nlargest(10, 'attendee_count')
            for _, row in top_countries.iterrows():
                st.write(f"**{row['country']}**: {row['attendee_count']:,} attendees")
                if row['new_this_week'] > 0:
                    st.caption(f"↗️ +{row['new_this_week']} this week")
    
    # Province breakdown for top countries
    st.subheader("Provincial/State Breakdown")
    top_country = st.selectbox(
        "Select Country:",
        geo_data['country'].unique()
    )
    
    province_data = geo_data[geo_data['country'] == top_country]
    if not province_data.empty and province_data['province'].notna().any():
        fig = px.bar(
            province_data[province_data['province'].notna()],
            x='attendee_count',
            y='province',
            orientation='h',
            title=f"Distribution in {top_country}"
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)

# Tab 4: Industries & Organizations
with tabs[3]:
    st.header("🏢 Industries & Organizations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Industry distribution
        industry_data = get_industry_trends()
        if not industry_data.empty:
            fig = px.pie(
                industry_data.head(10),
                values='total',
                names='industry',
                title="Top 10 Industries"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Growth rates
            st.subheader("📈 Fastest Growing Industries")
            growing = industry_data[industry_data['growth_rate_pct'] > 0].nlargest(5, 'growth_rate_pct')
            for _, row in growing.iterrows():
                st.write(f"**{row['industry']}**: +{row['growth_rate_pct']:.1f}% growth")
    
    with col2:
        # Organization types
        org_type_dist = get_field_distribution('detail_org_type', 10)
        if not org_type_dist.empty:
            fig = create_bar_chart(org_type_dist, "Organization Types", color_scale="Oranges")
            st.plotly_chart(fig, use_container_width=True)

# Tab 5: Roles & Positions
with tabs[4]:
    st.header("👥 Roles & Positions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Position types
        position_dist = get_field_distribution('detail_position_type', 15)
        if not position_dist.empty:
            fig = create_bar_chart(position_dist, "Position Types", color_scale="Greens")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Job titles word cloud
        st.subheader("Common Job Titles")
        job_titles = df['jobTitle'].value_counts().head(20) if 'jobTitle' in df.columns else pd.Series()
        if not job_titles.empty:
            fig = px.treemap(
                names=job_titles.index,
                parents=[""] * len(job_titles),
                values=job_titles.values,
                title="Job Title Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

# Tab 6: Interests & AI Maturity
with tabs[5]:
    st.header("🎯 Interests & AI Maturity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Interests analysis
        interests_data = get_interests_analysis()
        if not interests_data.empty:
            fig = px.bar(
                interests_data.head(15),
                x='count',
                y='interest',
                orientation='h',
                title="Top 15 Interests",
                labels={'count': 'Number of Attendees', 'interest': 'Interest'}
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # AI Maturity
        ai_maturity = get_ai_maturity_analysis()
        if not ai_maturity.empty:
            # Order the maturity levels
            maturity_order = ['Not started', 'Exploring', 'Implementing', 'Scaling', 'Advanced']
            ai_maturity['maturity_level'] = pd.Categorical(
                ai_maturity['maturity_level'], 
                categories=maturity_order, 
                ordered=True
            )
            ai_maturity = ai_maturity.sort_values('maturity_level')
            
            fig = px.funnel(
                ai_maturity,
                y='maturity_level',
                x='count',
                title="AI Maturity Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

# Tab 7: New Attendees
with tabs[6]:
    st.header("🆕 New Attendees")
    
    # Time range selector
    hours_back = st.slider("Show new attendees from last N hours:", 24, 168, 48)
    
    # Get recent activity
    recent_activity = get_recent_activity(hours_back)
    
    if not recent_activity.empty:
        # Split by activity type
        new_signups = recent_activity[recent_activity['activity_type'] == 'New Signup']
        updates = recent_activity[recent_activity['activity_type'] == 'Profile Update']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"🆕 New Signups ({len(new_signups)})")
            if not new_signups.empty:
                st.dataframe(
                    new_signups[['name', 'organization', 'country', 'timestamp']].head(50),
                    use_container_width=True
                )
        
        with col2:
            st.subheader(f"📝 Profile Updates ({len(updates)})")
            if not updates.empty:
                st.dataframe(
                    updates[['name', 'organization', 'country', 'timestamp']].head(50),
                    use_container_width=True
                )
        
        # Timeline chart
        st.subheader("Activity Timeline")
        activity_by_hour = recent_activity.set_index('timestamp').resample('1H').size()
        
        fig = px.line(
            x=activity_by_hour.index,
            y=activity_by_hour.values,
            title=f"Activity in Last {hours_back} Hours",
            labels={'x': 'Time', 'y': 'Number of Activities'}
        )
        st.plotly_chart(fig, use_container_width=True)

# Tab 8: Data Quality
with tabs[7]:
    st.header("📋 Data Quality Metrics")
    
    if 'data_completeness' in stats:
        completeness_fig = create_completeness_chart(stats['data_completeness'])
        st.plotly_chart(completeness_fig, use_container_width=True)
        
        # Detailed completeness metrics
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
        
        if not completeness_df.empty:
            completeness_df = completeness_df.sort_values('Filled', ascending=False)
            st.dataframe(completeness_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}* | "
    f"*Data source: {'Live Database' if data_source == 'Live Database' else 'Historical Run'}*"
)