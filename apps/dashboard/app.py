"""
Mental Health Dashboard - MVP
Simple visualization of Kék Vonal contact data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from data_loader import load_data, get_database_stats

# Page config
st.set_page_config(
    page_title="Kék Vonal Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Kék Vonal - Kapcsolatok Dashboard")

# Sidebar filters
st.sidebar.header("Szűrők")

# Date range
default_start = datetime.now() - timedelta(days=30)
default_end = datetime.now()

start_date = st.sidebar.date_input("Kezdő dátum", default_start)
end_date = st.sidebar.date_input("Befejező dátum", default_end)

# Load data
with st.spinner("Adatok betöltése..."):
    df = load_data(start_date=start_date, end_date=end_date)

if df.empty:
    st.error("Nincs adat a kiválasztott időszakra")
    st.stop()

# Show basic stats
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Összes kapcsolat", len(df))

with col2:
    if 'csatorna' in df.columns:
        unique_channels = df['csatorna'].nunique()
        st.metric("Csatornák száma", unique_channels)

with col3:
    if 'nemi_identitasa' in df.columns:
        unique_genders = df['nemi_identitasa'].nunique()
        st.metric("Nemi identitások", unique_genders)

with col4:
    if 'eletkor' in df.columns:
        age_count = df['eletkor'].notna().sum()
        st.metric("Életkor kitöltve", age_count)

st.markdown("---")

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Trendek", "📋 Csatornák", "🔍 Nyers Adatok"])

with tab1:
    st.subheader("Kapcsolatok időbeli alakulása")
    
    if 'letrehozva' in df.columns and not df.empty:
        # Group by date
        df_daily = df.copy()
        df_daily['datum'] = pd.to_datetime(df_daily['letrehozva']).dt.date
        daily_counts = df_daily.groupby('datum').size().reset_index(name='count')
        
        fig = px.line(
            daily_counts, 
            x='datum', 
            y='count',
            title='Napi kapcsolatok száma',
            labels={'datum': 'Dátum', 'count': 'Kapcsolatok száma'}
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Csatornák megoszlása")
    
    if 'csatorna' in df.columns and not df.empty:
        # Channel distribution
        channel_counts = df['csatorna'].value_counts().reset_index()
        channel_counts.columns = ['Csatorna', 'Darabszám']
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            fig = px.pie(
                channel_counts, 
                values='Darabszám', 
                names='Csatorna',
                title='Csatornák eloszlása'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(channel_counts, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("Nyers adatok")
    
    # Show dataframe
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Download button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Letöltés CSV-ként",
        data=csv,
        file_name=f"kek_vonal_export_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("*Dashboard utolsó frissítése: {}*".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
