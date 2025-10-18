"""
Mental Health Contacts Dashboard
Interactive visualization of contact data from Kék Vonal
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_data, get_mental_health_categories
from visualizations import (
    create_monthly_trend,
    create_gender_split,
    create_age_distribution,
    create_channel_breakdown,
    create_category_breakdown
)

# Page config
st.set_page_config(
    page_title="Mental Health Dashboard",
    page_icon="📊",
    layout="wide"
)

# Header
st.title("📊 Mental Health Contacts Dashboard")
st.markdown("**Kék Vonal** - Psychological support contact analytics")

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Date range
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("From", value=pd.Timestamp.now() - pd.Timedelta(days=90))
with col2:
    end_date = st.date_input("To", value=pd.Timestamp.now())

# Mental health category filter
categories = get_mental_health_categories()
selected_category = st.sidebar.selectbox(
    "Mental Health Category",
    options=["All Categories"] + categories,
    index=0
)

# Channel filter
channels = ["All Channels", "Telefon", "Chat", "Email", "Egyéb"]
selected_channel = st.sidebar.selectbox("Contact Channel", channels)

# Load data button
if st.sidebar.button("🔄 Refresh Data", type="primary"):
    st.cache_data.clear()

# Load data
try:
    with st.spinner("Loading data from database..."):
        df = load_data(
            start_date=start_date,
            end_date=end_date,
            category=None if selected_category == "All Categories" else selected_category,
            channel=None if selected_channel == "All Channels" else selected_channel
        )
    
    if df.empty:
        st.warning("No data found for the selected filters.")
        st.stop()
    
    # KPIs
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Contacts", f"{len(df):,}")
    
    with col2:
        avg_age = df['eletkor'].mean() if 'eletkor' in df.columns else 0
        st.metric("Average Age", f"{avg_age:.1f}" if avg_age > 0 else "N/A")
    
    with col3:
        if 'rovid_hosszu' in df.columns:
            long_pct = (df['rovid_hosszu'] == False).sum() / len(df) * 100
            st.metric("Long Conversations", f"{long_pct:.0f}%")
    
    with col4:
        if 'nemi_identitasa' in df.columns:
            girls = (df['nemi_identitasa'] == 'Lány').sum()
            st.metric("Girls", f"{girls:,}")
    
    st.markdown("---")
    
    # Main visualizations
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Trends", "👥 Demographics", "📞 Channels", "🧠 Topics", "📊 Raw Data"
    ])
    
    with tab1:
        st.subheader("Monthly Contact Trends")
        fig_trend = create_monthly_trend(df)
        st.plotly_chart(fig_trend, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Weekly Pattern")
            if 'letrehozva' in df.columns:
                df_copy = df.copy()
                df_copy['day_of_week'] = pd.to_datetime(df_copy['letrehozva']).dt.day_name()
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                weekly = df_copy.groupby('day_of_week').size().reindex(day_order)
                fig_weekly = px.bar(weekly, labels={'value': 'Contacts', 'index': 'Day'})
                st.plotly_chart(fig_weekly, use_container_width=True)
        
        with col2:
            st.subheader("Hourly Pattern")
            if 'letrehozva' in df.columns:
                df_copy = df.copy()
                df_copy['hour'] = pd.to_datetime(df_copy['letrehozva']).dt.hour
                hourly = df_copy.groupby('hour').size()
                fig_hourly = px.line(hourly, labels={'value': 'Contacts', 'index': 'Hour'})
                st.plotly_chart(fig_hourly, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Gender Distribution")
            fig_gender = create_gender_split(df)
            st.plotly_chart(fig_gender, use_container_width=True)
        
        with col2:
            st.subheader("Age Distribution")
            fig_age = create_age_distribution(df)
            st.plotly_chart(fig_age, use_container_width=True)
    
    with tab3:
        st.subheader("Contact Channels")
        fig_channel = create_channel_breakdown(df)
        st.plotly_chart(fig_channel, use_container_width=True)
        
        # Channel over time
        if 'csatorna' in df.columns and 'letrehozva' in df.columns:
            st.subheader("Channel Usage Over Time")
            df_copy = df.copy()
            df_copy['month'] = pd.to_datetime(df_copy['letrehozva']).dt.to_period('M').astype(str)
            channel_time = df_copy.groupby(['month', 'csatorna']).size().reset_index(name='count')
            fig_channel_time = px.line(
                channel_time, 
                x='month', 
                y='count', 
                color='csatorna',
                labels={'count': 'Contacts', 'month': 'Month', 'csatorna': 'Channel'}
            )
            st.plotly_chart(fig_channel_time, use_container_width=True)
    
    with tab4:
        st.subheader("Mental Health Topics")
        
        if selected_category == "All Categories":
            fig_topics = create_category_breakdown(df)
            st.plotly_chart(fig_topics, use_container_width=True)
        else:
            st.info(f"Showing data filtered by: **{selected_category}**")
        
        # Topic trends
        if 'temak_listanezet' in df.columns and 'letrehozva' in df.columns:
            st.subheader("Topic Trends Over Time")
            df_copy = df.copy()
            df_copy['month'] = pd.to_datetime(df_copy['letrehozva']).dt.to_period('M').astype(str)
            
            # Get top 5 topics
            all_topics = []
            for topics_str in df_copy['temak_listanezet'].dropna():
                all_topics.extend(topics_str.split(', '))
            top_topics = pd.Series(all_topics).value_counts().head(5).index.tolist()
            
            # Create trend for top topics
            topic_trends = []
            for month in df_copy['month'].unique():
                month_data = df_copy[df_copy['month'] == month]
                for topic in top_topics:
                    count = month_data['temak_listanezet'].str.contains(topic, na=False).sum()
                    topic_trends.append({'month': month, 'topic': topic, 'count': count})
            
            df_trends = pd.DataFrame(topic_trends)
            fig_topic_trends = px.line(
                df_trends,
                x='month',
                y='count',
                color='topic',
                labels={'count': 'Mentions', 'month': 'Month', 'topic': 'Topic'}
            )
            st.plotly_chart(fig_topic_trends, use_container_width=True)
    
    with tab5:
        st.subheader("Raw Data")
        st.dataframe(df, use_container_width=True)
        
        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"mental_health_data_{start_date}_{end_date}.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.exception(e)

# Footer
st.markdown("---")
st.markdown("💙 **Kék Vonal** | Data updated in real-time from PostgreSQL database")

