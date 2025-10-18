"""
Mental Health Dashboard - MVP
Simple visualization of Kék Vonal contact data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from data_loader import load_data, get_database_stats
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Kék Vonal Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

# Authentication check
def check_password():
    """Returns True if the user entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == os.getenv("DASHBOARD_PASSWORD", "admin"):
            st.session_state.authenticated = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state.authenticated = False

    # Show password input if not authenticated
    if not st.session_state.authenticated:
        st.title("🔐 Kék Vonal - Dashboard Bejelentkezés")
        st.text_input(
            "Jelszó", 
            type="password", 
            on_change=password_entered, 
            key="password",
            help="Kérjük, adja meg a dashboard jelszót"
        )
        st.warning("⚠️ Kérjük, jelentkezzen be a dashboard eléréséhez")
        return False
    else:
        return True

# Check authentication before showing dashboard
if not check_password():
    st.stop()

# Logout button in sidebar
with st.sidebar:
    if st.button("🚪 Kijelentkezés"):
        st.session_state.authenticated = False
        st.rerun()

# Title
st.title("📊 Kék Vonal - Megkeresések Dashboard")

# Sidebar filters
st.sidebar.header("Szűrők")

# Date range
default_start = datetime.now() - timedelta(days=365)  # Last year
default_end = datetime.now()

start_date = st.sidebar.date_input("Kezdő dátum", default_start)
end_date = st.sidebar.date_input("Befejező dátum", default_end)

# Load initial data
with st.spinner("Adatok betöltése..."):
    df = load_data(start_date=start_date, end_date=end_date)

if df.empty:
    st.error("Nincs adat a kiválasztott időszakra")
    st.stop()

# Extract all unique values for filters
def extract_topics(df, column):
    """Extract unique topics from semicolon-separated column"""
    all_topics = set()
    for topics in df[column].dropna():
        if isinstance(topics, str):
            all_topics.update([t.strip() for t in topics.split(';') if t.strip()])
    return sorted(list(all_topics))

# Get unique values for filters
unique_channels = ['Összes'] + sorted(df['csatorna'].dropna().unique().tolist())
unique_fotema = ['Összes'] + extract_topics(df, 'temak_listanezet')
unique_altema = ['Összes'] + extract_topics(df, 'altemak_listanezet')
unique_ages = ['Összes'] + sorted(df['eletkor'].dropna().unique().tolist())
unique_genders = ['Összes'] + sorted(df['nemi_identitasa'].dropna().unique().tolist())

# Filter controls
st.sidebar.markdown("---")
selected_channel = st.sidebar.selectbox("Csatorna", unique_channels)
selected_fotema = st.sidebar.selectbox("Főtéma", unique_fotema)
selected_altema = st.sidebar.selectbox("Altéma", unique_altema)
selected_age = st.sidebar.selectbox("Életkor", unique_ages)
selected_gender = st.sidebar.selectbox("Nemi identitás", unique_genders)

# Apply filters
df_filtered = df.copy()

if selected_channel != 'Összes':
    df_filtered = df_filtered[df_filtered['csatorna'] == selected_channel]

if selected_fotema != 'Összes':
    df_filtered = df_filtered[df_filtered['temak_listanezet'].str.contains(selected_fotema, na=False)]

if selected_altema != 'Összes':
    df_filtered = df_filtered[df_filtered['altemak_listanezet'].str.contains(selected_altema, na=False)]

if selected_age != 'Összes':
    df_filtered = df_filtered[df_filtered['eletkor'] == selected_age]

if selected_gender != 'Összes':
    df_filtered = df_filtered[df_filtered['nemi_identitasa'] == selected_gender]

if df_filtered.empty:
    st.warning("Nincs adat a kiválasztott szűrőkkel")
    st.stop()

# Show basic stats
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Összes megkeresés", len(df_filtered))

with col2:
    if 'csatorna' in df_filtered.columns:
        unique_channels_count = df_filtered['csatorna'].nunique()
        st.metric("Csatornák száma", unique_channels_count)

with col3:
    if 'nemi_identitasa' in df_filtered.columns:
        unique_genders = df_filtered['nemi_identitasa'].nunique()
        st.metric("Nemi identitások", unique_genders)

with col4:
    if 'eletkor' in df_filtered.columns:
        age_count = df_filtered['eletkor'].notna().sum()
        st.metric("Életkor kitöltve", age_count)

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["🧠 Altémák", "📈 Trendek", "📋 Megoszlások", "🔍 Nyers Adatok"])

with tab1:
    st.subheader("Főbb Altémák témák időbeli alakulása")
    
    # Define the 6 key topics to track
    key_topics = [
        "Általános lehangoltság",
        "Szorongás, félelmek",
        "Öngyilkossági gondolat",
        "Önsértés",
        "Evészavarok",
        "Diagnosztizált pszichés betegség"
    ]
    
    if 'letrehozva' in df_filtered.columns and 'altemak_listanezet' in df_filtered.columns and not df_filtered.empty:
        # Prepare data for time series (using filtered data)
        df_topics = df_filtered.copy()
        df_topics['datum'] = pd.to_datetime(df_topics['letrehozva']).dt.to_period('M').dt.to_timestamp()
        
        # Count occurrences of each topic per month
        topic_data = []
        for topic in key_topics:
            monthly_counts = df_topics[df_topics['altemak_listanezet'].str.contains(topic, na=False)].groupby('datum').size()
            for date, count in monthly_counts.items():
                topic_data.append({'Dátum': date, 'Téma': topic, 'Megkeresések': count})
        
        if topic_data:
            df_plot = pd.DataFrame(topic_data)
            
            fig = px.line(
                df_plot,
                x='Dátum',
                y='Megkeresések',
                color='Téma',
                title='Főbb altémák havi alakulása',
                labels={'Megkeresések': 'Megkeresések száma', 'Téma': 'Téma'},
                markers=True
            )
            fig.update_layout(height=500, hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nincs elegendő adat a kiválasztott témákhoz a szűrőkkel")

with tab2:
    st.subheader("Megkeresések időbeli alakulása")
    
    if 'letrehozva' in df_filtered.columns and not df_filtered.empty:
        # Group by date
        df_daily = df_filtered.copy()
        df_daily['datum'] = pd.to_datetime(df_daily['letrehozva']).dt.date
        daily_counts = df_daily.groupby('datum').size().reset_index(name='count')
        
        fig = px.line(
            daily_counts, 
            x='datum', 
            y='count',
            title='Napi Megkeresések száma',
            labels={'datum': 'Dátum', 'count': 'Megkeresések száma'}
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Megoszlások")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Channel distribution
        if 'csatorna' in df_filtered.columns and not df_filtered.empty:
            channel_counts = df_filtered['csatorna'].value_counts().reset_index()
            channel_counts.columns = ['Csatorna', 'Darabszám']
            
            fig = px.bar(
                channel_counts,
                x='Csatorna',
                y='Darabszám',
                title='Csatornák megoszlása',
                color='Darabszám',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Age distribution
        if 'eletkor' in df_filtered.columns and not df_filtered.empty:
            age_counts = df_filtered['eletkor'].value_counts().reset_index()
            age_counts.columns = ['Életkor', 'Darabszám']
            age_counts = age_counts.head(10)  # Top 10
            
            fig = px.bar(
                age_counts,
                x='Életkor',
                y='Darabszám',
                title='Top 10 életkor kategória',
                color='Darabszám',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Főtéma distribution
    st.markdown("---")
    if 'temak_listanezet' in df_filtered.columns:
        st.subheader("Főtémák gyakorisága")
        
        # Extract all topics
        all_fotema = []
        for topics in df_filtered['temak_listanezet'].dropna():
            if isinstance(topics, str):
                all_fotema.extend([t.strip() for t in topics.split(';') if t.strip()])
        
        if all_fotema:
            fotema_counts = pd.Series(all_fotema).value_counts().reset_index()
            fotema_counts.columns = ['Főtéma', 'Darabszám']
            fotema_counts = fotema_counts.head(15)  # Top 15
            
            fig = px.bar(
                fotema_counts,
                x='Darabszám',
                y='Főtéma',
                orientation='h',
                title='Top 15 főtéma',
                color='Darabszám',
                color_continuous_scale='Reds'
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("Nyers adatok")
    
    # Show dataframe
    st.dataframe(df_filtered, use_container_width=True, hide_index=True)
    
    # Download button
    csv = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Letöltés CSV-ként",
        data=csv,
        file_name=f"kek_vonal_export_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# Footer
st.markdown("---")
st.markdown("*Dashboard utolsó frissítése: {}*".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
