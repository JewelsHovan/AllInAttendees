"""
Visualization utilities for All In 2025 Analytics Dashboard
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import Optional

def create_bar_chart(df: pd.DataFrame, title: str, 
                     x_label: str = "Count", y_label: str = "Category",
                     color_scale: str = "Blues") -> go.Figure:
    """Create a horizontal bar chart"""
    # Handle both uppercase and lowercase column names
    x_col = 'Count' if 'Count' in df.columns else 'count'
    y_col = 'Value' if 'Value' in df.columns else 'value'
    
    fig = px.bar(
        df, 
        x=x_col, 
        y=y_col,
        orientation='h',
        title=title,
        labels={x_col: x_label, y_col: y_label},
        text=x_col,
        color=x_col,
        color_continuous_scale=color_scale
    )
    
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(
        showlegend=False,
        height=max(400, len(df) * 30),  # Dynamic height based on items
        margin=dict(l=0, r=50, t=50, b=0),
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def create_pie_chart(df: pd.DataFrame, title: str) -> go.Figure:
    """Create a pie chart"""
    # Handle both uppercase and lowercase column names
    values_col = 'Count' if 'Count' in df.columns else 'count'
    names_col = 'Value' if 'Value' in df.columns else 'value'
    
    fig = px.pie(
        df, 
        values=values_col, 
        names=names_col,
        title=title
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        showlegend=True,
        height=400,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig

def create_donut_chart(values: list, labels: list, title: str) -> go.Figure:
    """Create a donut chart"""
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4
    )])
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        title=title,
        showlegend=True,
        height=400,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig

def create_treemap(df: pd.DataFrame, title: str) -> go.Figure:
    """Create a treemap visualization"""
    # Handle both uppercase and lowercase column names
    path_col = 'Value' if 'Value' in df.columns else 'value'
    values_col = 'Count' if 'Count' in df.columns else 'count'
    
    fig = px.treemap(
        df,
        path=[path_col],
        values=values_col,
        title=title
    )
    
    fig.update_traces(
        textinfo="label+value+percent root",
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percentRoot}<extra></extra>'
    )
    
    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    return fig

def create_completeness_chart(completeness_data: dict) -> go.Figure:
    """Create a data completeness chart"""
    fields = []
    percentages = []
    
    for field, data in completeness_data.items():
        # Clean field names for display
        display_name = field.replace('detail_', '').replace('_', ' ').title()
        fields.append(display_name)
        percentages.append(data['percentage'])
    
    # Sort by percentage
    sorted_data = sorted(zip(fields, percentages), key=lambda x: x[1], reverse=True)
    fields, percentages = zip(*sorted_data) if sorted_data else ([], [])
    
    # Create color scale - green for high completeness, red for low
    colors = ['green' if p > 80 else 'orange' if p > 50 else 'red' for p in percentages]
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(percentages),
            y=list(fields),
            orientation='h',
            marker=dict(color=colors),
            text=[f'{p:.1f}%' for p in percentages],
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="Data Completeness by Field",
        xaxis_title="Completeness (%)",
        yaxis_title="Field",
        height=max(400, len(fields) * 30),
        margin=dict(l=0, r=50, t=50, b=0),
        showlegend=False,
        xaxis=dict(range=[0, 105])
    )
    
    return fig

def create_interests_wordcloud_data(df: pd.DataFrame) -> pd.DataFrame:
    """Process interests data for visualization"""
    if 'detail_interests' not in df.columns:
        return pd.DataFrame()
    
    # Split multi-value interests (assuming they're separated by |)
    all_interests = []
    for interests in df['detail_interests'].dropna():
        if isinstance(interests, str):
            # Split by | and clean each interest
            for interest in interests.split('|'):
                cleaned = interest.strip()
                if cleaned:
                    all_interests.append(cleaned)
    
    # Count occurrences
    interest_counts = pd.Series(all_interests).value_counts().head(30)
    
    return pd.DataFrame({
        'value': interest_counts.index,  # Use lowercase for consistency
        'count': interest_counts.values,
        'percentage': (interest_counts.values / len(df) * 100).round(2)
    })

def create_metric_card(title: str, value: str, delta: Optional[str] = None) -> str:
    """Create HTML for a metric card"""
    delta_html = f'<p style="color: green; font-size: 14px;">{delta}</p>' if delta else ''
    
    return f"""
    <div style="
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    ">
        <p style="color: #666; margin: 0; font-size: 14px;">{title}</p>
        <h2 style="margin: 10px 0; color: #333;">{value}</h2>
        {delta_html}
    </div>
    """