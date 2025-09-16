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
    get_new_attendees_summary
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

# Title with LIVE indicator
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

# Add LIVE indicator
st.markdown("""
<div style="text-align: center; margin-bottom: 1rem;">
    <span style="background-color: #28a745; color: white; padding: 0.25rem 0.75rem; border-radius: 20px; font-weight: bold;">
        🔴 LIVE DATA
    </span>
</div>
""", unsafe_allow_html=True)

# Display key metrics at the top
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Attendees", 
        f"{summary.get('total_attendees', 0):,}",
        f"+{summary.get('week_new', 0)} this week"
    )

with col2:
    st.metric(
        "Organizations", 
        f"{summary.get('unique_orgs', 0):,}",
        f"+{summary.get('new_orgs_week', 0) if summary.get('new_orgs_week', 0) > 0 else 0} this week"
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
        
        # Set selected_run to 'Latest' for live database mode
        selected_run = 'Latest'
        
        # Load current data
        df = load_run_data()
        
        # Download section
        st.markdown("---")
        st.subheader("📥 Download Data")
        
        if not df.empty:
            # Show record count
            st.info(f"📊 {len(df):,} attendees available for download")
            
            # Prepare CSV data
            csv_data = df.to_csv(index=False).encode('utf-8-sig')  # utf-8-sig adds BOM for Excel
            
            # Generate filename with current date
            current_date = datetime.now().strftime('%Y-%m-%d')
            csv_filename = f"all_attendees_{current_date}.csv"
            
            # CSV Download button
            st.download_button(
                label="⬇️ Download as CSV",
                data=csv_data,
                file_name=csv_filename,
                mime="text/csv",
                help="Download complete attendee data as CSV file"
            )
            
            # Prepare JSON data
            json_data = df.to_json(orient='records', indent=2)
            json_filename = f"all_attendees_{current_date}.json"
            
            # JSON Download button
            st.download_button(
                label="⬇️ Download as JSON",
                data=json_data,
                file_name=json_filename,
                mime="application/json",
                help="Download complete attendee data as JSON file"
            )
            
            # Info about fields
            with st.expander("ℹ️ Download Info"):
                st.write(f"**Total Records:** {len(df):,}")
                st.write(f"**Total Columns:** {len(df.columns)}")
                st.write("**Key Fields Include:**")
                st.write("• Basic: Name, Email, Organization, Job Title")
                st.write("• Details: Country, Industry, Interests, AI Maturity")
                st.write("• Metadata: First Seen, Last Updated")
        else:
            st.warning("No data available to download")
        
    else:
        # Get available runs from the runs directory
        runs = get_available_runs()
        
        # Remove 'Latest' from the list for historical runs
        if 'Latest' in runs:
            runs.remove('Latest')
        
        if not runs:
            st.error("No historical runs found")
            st.stop()
        
        # Run selector
        selected_run = st.selectbox(
            "Choose a run to analyze:",
            options=runs,
            format_func=lambda x: f"{x}" if x else "Unknown",
            index=0
        )
        
        # Parse run date from the directory name (format: YYYY-MM-DD_HHMMSS)
        if selected_run and selected_run != 'Latest':
            try:
                from datetime import datetime
                date_parts = selected_run.split('_')[0].split('-')
                if len(date_parts) == 3:
                    run_date = f"{date_parts[0]}-{date_parts[1]}-{date_parts[2]}"
                    st.write(f"**Run Date:** {run_date}")
            except:
                pass
        
        # Load selected run data
        df = load_run_data(selected_run)
    
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
    "🆕 New Attendees",
    "🎯 AI Interest List",
    "📈 Growth Analytics",
    "🌍 Geographic Distribution", 
    "🏢 Industries & Organizations", 
    "👥 Roles & Positions",
    "🎯 Interests & AI Maturity",
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
        st.write(f"**Total Attendees:** {stats.get('total_attendees', 0):,}")
        st.write(f"**Unique Organizations:** {stats.get('unique_companies', 0):,}")
        st.write(f"**Countries Represented:** {stats.get('unique_countries', 0):,}")
        st.write(f"**Industries:** {stats.get('unique_industries', 0):,}")
        
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

# Tab 4: Growth Analytics
with tabs[3]:
    st.header("📈 Growth Analytics")
    
    # Date range selector
    col1, col2 = st.columns([2, 3])
    with col1:
        days_back = st.slider("Days to analyze:", 7, 90, 30)
    
    # Get growth data
    growth_data = get_growth_timeline(days_back)
    
    if not growth_data.empty:
        # Simple approach: Set the first data point (Sept 11) to 0 if it's the initial import
        # Store original value for display
        original_first_day_signups = None
        if len(growth_data) > 0:
            first_date = growth_data.iloc[0]['date']
            # Check if this is Sept 11, 2024 (or Sept 10, depending on data)
            if pd.to_datetime(first_date).date() <= pd.Timestamp('2025-09-11').date():
                original_first_day_signups = growth_data.iloc[0]['new_signups']
                # Set first day to 0 for visualization
                growth_data.iloc[0, growth_data.columns.get_loc('new_signups')] = 0
                
                # Add a note about the baseline
                st.info(f"📌 Initial data import of {original_first_day_signups:,} attendees on {pd.to_datetime(first_date).strftime('%B %d, %Y')} (excluded from daily averages)")
        
        # For statistics, we'll use the index to exclude the first day
        sept_11 = pd.to_datetime(growth_data.iloc[0]['date']).date() if len(growth_data) > 0 else None
        
        # Growth statistics FIRST
        st.subheader("📊 Growth Statistics")
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate stats excluding first day (baseline)
        # Skip first row if it's the initial import
        if original_first_day_signups is not None:
            signups_excl_baseline = growth_data.iloc[1:]['new_signups']
        else:
            signups_excl_baseline = growth_data['new_signups']
        
        with col1:
            avg_daily = signups_excl_baseline.mean() if len(signups_excl_baseline) > 0 else 0
            st.metric("Average Daily Signups", f"{avg_daily:.1f}")
        
        with col2:
            # Best day excluding first day if it's baseline
            if original_first_day_signups is not None:
                best_days = growth_data.iloc[1:]
            else:
                best_days = growth_data
            
            if not best_days.empty:
                max_day = best_days.loc[best_days['new_signups'].idxmax()]
                st.metric("Best Day", f"{max_day['new_signups']:,}", f"{pd.to_datetime(max_day['date']).strftime('%b %d')}")
        
        with col3:
            total_growth = signups_excl_baseline.sum()
            st.metric(f"New in {days_back} Days", f"{total_growth:,}")
        
        with col4:
            # Growth rate
            if len(growth_data) > 1:
                first_val = growth_data.iloc[0]['cumulative_attendees']
                last_val = growth_data.iloc[-1]['cumulative_attendees']
                growth_rate = ((last_val - first_val) / first_val * 100) if first_val > 0 else 0
                st.metric("Growth Rate", f"{growth_rate:.1f}%")
        
        st.divider()
        
        # Daily Signups Chart (SECOND)
        st.subheader("📈 Daily New Signups")
        fig_daily = go.Figure()
        
        # Bar chart for daily signups
        fig_daily.add_trace(go.Bar(
            x=growth_data['date'],
            y=growth_data['new_signups'],
            name='Daily Signups',
            marker_color='lightblue',
            text=growth_data['new_signups'],
            textposition='outside'
        ))
        
        # Add moving average (recalculate excluding Sept 11)
        if 'moving_avg_7d' in growth_data.columns:
            # Recalculate moving average without Sept 11
            growth_data_copy = growth_data.copy()
            # Calculate rolling average excluding the baseline day
            growth_data_copy['recalc_ma'] = growth_data_copy['new_signups'].rolling(
                window=7, min_periods=1, center=False
            ).mean()
            
            fig_daily.add_trace(go.Scatter(
                x=growth_data_copy['date'],
                y=growth_data_copy['recalc_ma'],
                name='7-Day Moving Avg',
                line=dict(color='orange', dash='dash', width=2)
            ))
        
        fig_daily.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Signups",
            hovermode='x unified',
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig_daily, use_container_width=True)
        
        # Cumulative Total Chart (THIRD)
        st.subheader("📊 Cumulative Total Attendees")
        fig_cumulative = go.Figure()
        
        # Line chart for cumulative total
        fig_cumulative.add_trace(go.Scatter(
            x=growth_data['date'],
            y=growth_data['cumulative_attendees'],
            name='Total Attendees',
            line=dict(color='darkblue', width=3),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.2)'
        ))
        
        # Add markers for milestones
        milestones = [1000, 2000, 2500, 3000]
        for milestone in milestones:
            milestone_data = growth_data[growth_data['cumulative_attendees'] >= milestone]
            if not milestone_data.empty:
                first_day = milestone_data.iloc[0]
                fig_cumulative.add_annotation(
                    x=first_day['date'],
                    y=milestone,
                    text=f"{milestone:,}",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1,
                    arrowcolor="green",
                    ax=-30,
                    ay=-30
                )
        
        fig_cumulative.update_layout(
            xaxis_title="Date",
            yaxis_title="Total Attendees",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig_cumulative, use_container_width=True)

# Tab 5: Geographic Distribution
with tabs[4]:
    st.header("🌍 Geographic Distribution")
    
    geo_data = get_geographic_distribution()
    
    if not geo_data.empty:
        # Clean up Quebec encoding issue
        geo_data['province'] = geo_data['province'].replace('QuÃ©bec', 'Quebec')
        
        # Country summary
        country_summary = geo_data.groupby('country').agg({
            'attendee_count': 'sum',
            'unique_orgs': 'sum',
            'new_this_week': 'sum'
        }).reset_index().sort_values('attendee_count', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # International attendees (excluding Canada)
            st.subheader("🌎 International Attendees")
            international = country_summary[country_summary['country'] != 'Canada'].head(20)
            
            if not international.empty:
                fig = px.bar(
                    international,
                    x='attendee_count',
                    y='country',
                    orientation='h',
                    title='Top Countries (Excluding Canada)',
                    text='attendee_count',
                    color='attendee_count',
                    color_continuous_scale='Teal'
                )
                fig.update_traces(texttemplate='%{text}', textposition='outside')
                fig.update_layout(
                    yaxis={'categoryorder':'total ascending'}, 
                    height=500,
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Country statistics
            st.subheader("📊 Geographic Stats")
            canada_count = country_summary[country_summary['country'] == 'Canada']['attendee_count'].sum() if 'Canada' in country_summary['country'].values else 0
            intl_count = country_summary[country_summary['country'] != 'Canada']['attendee_count'].sum()
            total_countries = len(country_summary)
            
            st.metric("Canadian Attendees", f"{canada_count:,}")
            st.metric("International Attendees", f"{intl_count:,}")
            st.metric("Countries Represented", f"{total_countries}")
            
            if canada_count > 0:
                intl_percentage = (intl_count / (canada_count + intl_count) * 100)
                st.metric("International %", f"{intl_percentage:.1f}%")
    
    # Province breakdown for Canada
    if 'Canada' in geo_data['country'].values:
        st.subheader("🇨🇦 Canadian Provincial Distribution")
        
        canada_data = geo_data[geo_data['country'] == 'Canada']
        province_data = canada_data[canada_data['province'].notna()].copy()
        
        if not province_data.empty:
            # Clean up province names
            province_data['province'] = province_data['province'].replace({
                'QuÃ©bec': 'Quebec',
                'Québec': 'Quebec',
                'Ile-du-Prince-Édouard / Prince Edward Island': 'Prince Edward Island',
                'Île-du-Prince-Édouard / Prince Edward Island': 'Prince Edward Island'
            })
            
            # Aggregate by province after cleaning
            province_summary = province_data.groupby('province').agg({
                'attendee_count': 'sum',
                'unique_orgs': 'sum'
            }).reset_index().sort_values('attendee_count', ascending=False)
            
            fig = px.bar(
                province_summary,
                x='attendee_count',
                y='province',
                orientation='h',
                title='Attendees by Canadian Province',
                text='attendee_count',
                color='attendee_count',
                color_continuous_scale='Blues'
            )
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            fig.update_layout(
                yaxis={'categoryorder':'total ascending'},
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

# Tab 6: Industries & Organizations
with tabs[5]:
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
            # Convert growth_rate_pct to numeric, handling any non-numeric values
            industry_data['growth_rate_pct'] = pd.to_numeric(industry_data['growth_rate_pct'], errors='coerce').fillna(0)
            growing = industry_data[industry_data['growth_rate_pct'] > 0].nlargest(5, 'growth_rate_pct')
            for _, row in growing.iterrows():
                st.write(f"**{row['industry']}**: +{row['growth_rate_pct']:.1f}% growth")
    
    with col2:
        # Organization types
        org_type_dist = get_field_distribution('detail_org_type', 10)
        if not org_type_dist.empty:
            fig = create_bar_chart(org_type_dist, "Organization Types", color_scale="Oranges")
            st.plotly_chart(fig, use_container_width=True)

# Tab 7: Roles & Positions
with tabs[6]:
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
        
        # Handle both camelCase (CSV) and snake_case (database) column names
        if 'jobTitle' in df.columns:
            job_titles = df['jobTitle'].value_counts().head(20)
        elif 'job_title' in df.columns:
            job_titles = df['job_title'].value_counts().head(20)
        else:
            job_titles = pd.Series()
            
        if not job_titles.empty:
            fig = px.treemap(
                names=job_titles.index,
                parents=[""] * len(job_titles),
                values=job_titles.values,
                title="Job Title Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)

# Tab 8: Interests & AI Maturity
with tabs[7]:
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
            # Order the maturity levels based on actual database values
            maturity_order = [
                'No initiative planned',
                'Interest, but no project', 
                'Pilot project underway',
                'Partial deployment',
                'Strategic adoption'
            ]
            
            # Only include categories that exist in the data
            existing_categories = ai_maturity['maturity_level'].unique()
            ordered_categories = [cat for cat in maturity_order if cat in existing_categories]
            
            # Handle any unexpected categories
            for cat in existing_categories:
                if cat not in ordered_categories:
                    ordered_categories.append(cat)
            
            ai_maturity['maturity_level'] = pd.Categorical(
                ai_maturity['maturity_level'], 
                categories=ordered_categories, 
                ordered=True
            )
            ai_maturity = ai_maturity.sort_values('maturity_level')
            
            # Use a bar chart instead of funnel for better visualization
            fig = px.bar(
                ai_maturity,
                x='count',
                y='maturity_level',
                orientation='h',
                title="AI Maturity Distribution",
                text='count',
                color='count',
                color_continuous_scale='Blues'
            )
            fig.update_traces(texttemplate='%{text}', textposition='outside')
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)

# Tab 2: New Attendees  
with tabs[1]:
    st.header("🆕 New Attendees (Today)")
    
    # Check if we're viewing historical or live data
    if selected_run != 'Latest':
        # Historical run - compare with previous run
        from utils.data_loader import get_new_attendees_for_historical_run
        recent_activity = get_new_attendees_for_historical_run(df, selected_run)
        
        if not recent_activity.empty:
            st.info(f"Showing new attendees compared to previous run")
            new_signups = recent_activity
        else:
            new_signups = pd.DataFrame()
    else:
        # Live database - get today's new signups
        from utils.db_queries import get_todays_new_attendees
        new_signups = get_todays_new_attendees()
    
    if not new_signups.empty:
        # Show metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("New Signups", f"{len(new_signups)}")
        with col2:
            unique_orgs = new_signups['organization'].nunique() if 'organization' in new_signups.columns else 0
            st.metric("Organizations", f"{unique_orgs}")
        with col3:
            unique_countries = new_signups['country'].nunique() if 'country' in new_signups.columns else 0
            st.metric("Countries", f"{unique_countries}")
        
        # Show the data
        display_cols = ['name', 'organization', 'job_title', 'country', 'timestamp']
        available_cols = [col for col in display_cols if col in new_signups.columns]
        
        st.dataframe(
            new_signups[available_cols].head(200),
            use_container_width=True,
            height=600
        )
    else:
        st.info("No new signups today")

# Tab 3: AI Interest List
with tabs[2]:
    st.header("🎯 AI Interest List")
    st.caption("Canadian executives who are exploring or implementing AI solutions")
    
    # Only available for live database
    if selected_run == 'Latest':
        from utils.db_queries import get_filtered_attendees
        
        # Apply all three filters together (AND condition)
        combined_filters = {
            'ai_seekers': True,
            'executives': True,
            'canada': True
        }
        
        # Get combined filtered list
        filtered_df = get_filtered_attendees(combined_filters, limit=5000)
        
        if not filtered_df.empty:
            # Show metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Matches", f"{len(filtered_df):,}")
            with col2:
                unique_orgs = filtered_df['organization'].nunique() if 'organization' in filtered_df.columns else 0
                st.metric("Organizations", f"{unique_orgs:,}")
            with col3:
                unique_provinces = filtered_df['province'].nunique() if 'province' in filtered_df.columns else 0
                st.metric("Provinces", f"{unique_provinces}")
            with col4:
                # Count AI maturity types
                if 'ai_maturity' in filtered_df.columns:
                    interest_count = (filtered_df['ai_maturity'] == 'Interest, but no project').sum()
                    pilot_count = (filtered_df['ai_maturity'] == 'Pilot project underway').sum()
                    st.metric("Interest/Pilot", f"{interest_count}/{pilot_count}")
            
            # Display the data with LinkedIn field
            display_cols = ['name', 'organization', 'job_title', 'province', 'ai_maturity', 'social_linkedin', 'email']
            available_cols = [col for col in display_cols if col in filtered_df.columns]
            
            # Make sure we have the columns we need
            if available_cols:
                st.dataframe(
                    filtered_df[available_cols],
                    use_container_width=True,
                    height=600
                )
                
                # Export button
                csv = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Export AI Interest List (CSV)",
                    data=csv,
                    file_name=f"ai_interest_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.error("No columns available to display")
        else:
            st.info("No attendees match all criteria (Canadian + Executive + AI Interest)")
    else:
        st.info("AI Interest List is only available for live database view")

# Tab 9: Data Quality
with tabs[8]:
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
                'Missing': stats.get('total_attendees', 0) - data['count'],
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
