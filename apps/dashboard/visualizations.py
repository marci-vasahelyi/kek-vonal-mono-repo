"""
Visualization functions for Mental Health Dashboard
Creates Plotly charts for various data views
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def create_monthly_trend(df):
    """Create monthly trend line chart"""
    if 'letrehozva' not in df.columns or df.empty:
        return go.Figure().add_annotation(text="No data available", showarrow=False)
    
    df_copy = df.copy()
    df_copy['month'] = pd.to_datetime(df_copy['letrehozva']).dt.to_period('M')
    monthly = df_copy.groupby('month').size().reset_index(name='contacts')
    monthly['month'] = monthly['month'].astype(str)
    
    fig = px.line(
        monthly, 
        x='month', 
        y='contacts',
        markers=True,
        labels={'month': 'Month', 'contacts': 'Total Contacts'},
        title='Monthly Contact Trends'
    )
    
    fig.update_traces(line_color='#4A90E2', line_width=3)
    fig.update_layout(
        hovermode='x unified',
        plot_bgcolor='white',
        height=400
    )
    
    return fig

def create_gender_split(df):
    """Create gender distribution chart"""
    if 'nemi_identitasa' not in df.columns or df.empty:
        return go.Figure().add_annotation(text="No gender data available", showarrow=False)
    
    # Count by gender
    gender_counts = df['nemi_identitasa'].value_counts()
    
    fig = px.pie(
        values=gender_counts.values,
        names=gender_counts.index,
        title='Gender Distribution',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=400)
    
    return fig

def create_age_distribution(df):
    """Create age distribution histogram"""
    if 'eletkor' not in df.columns or df.empty:
        return go.Figure().add_annotation(text="No age data available", showarrow=False)
    
    df_filtered = df[df['eletkor'].notna()]
    
    if df_filtered.empty:
        return go.Figure().add_annotation(text="No age data available", showarrow=False)
    
    fig = px.histogram(
        df_filtered,
        x='eletkor',
        nbins=20,
        labels={'eletkor': 'Age', 'count': 'Number of Contacts'},
        title='Age Distribution',
        color_discrete_sequence=['#50C878']
    )
    
    fig.update_layout(
        bargap=0.1,
        plot_bgcolor='white',
        height=400
    )
    
    return fig

def create_channel_breakdown(df):
    """Create channel breakdown chart"""
    if 'csatorna' not in df.columns or df.empty:
        return go.Figure().add_annotation(text="No channel data available", showarrow=False)
    
    channel_counts = df['csatorna'].value_counts().reset_index()
    channel_counts.columns = ['Channel', 'Count']
    
    fig = px.bar(
        channel_counts,
        x='Channel',
        y='Count',
        title='Contact Channels',
        color='Count',
        color_continuous_scale='Blues'
    )
    
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        height=400
    )
    
    return fig

def create_category_breakdown(df):
    """Create mental health category breakdown"""
    if 'temak_listanezet' not in df.columns or df.empty:
        return go.Figure().add_annotation(text="No topic data available", showarrow=False)
    
    # Parse topics from comma-separated list
    all_topics = []
    for topics_str in df['temak_listanezet'].dropna():
        topics = [t.strip() for t in topics_str.split(',')]
        all_topics.extend(topics)
    
    if not all_topics:
        return go.Figure().add_annotation(text="No topic data available", showarrow=False)
    
    topic_counts = pd.Series(all_topics).value_counts().head(15)
    
    fig = px.bar(
        x=topic_counts.values,
        y=topic_counts.index,
        orientation='h',
        labels={'x': 'Number of Mentions', 'y': 'Topic'},
        title='Top 15 Mental Health Topics',
        color=topic_counts.values,
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(
        showlegend=False,
        plot_bgcolor='white',
        height=600,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def create_conversation_length_chart(df):
    """Create conversation length distribution"""
    if 'hivas_hossza' not in df.columns or df.empty:
        return go.Figure().add_annotation(text="No conversation length data", showarrow=False)
    
    df_filtered = df[df['hivas_hossza'].notna()]
    
    if df_filtered.empty:
        return go.Figure().add_annotation(text="No conversation length data", showarrow=False)
    
    fig = px.histogram(
        df_filtered,
        x='hivas_hossza',
        nbins=30,
        labels={'hivas_hossza': 'Duration (minutes)', 'count': 'Number of Conversations'},
        title='Conversation Length Distribution'
    )
    
    fig.update_layout(
        plot_bgcolor='white',
        height=400
    )
    
    return fig

