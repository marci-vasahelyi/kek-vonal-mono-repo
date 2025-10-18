"""
Data loading utilities for Mental Health Dashboard
Connects to PostgreSQL database and loads Kék Vonal contact data
"""

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

def get_db_connection():
    """Create database connection using credentials from .env"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', '192.168.1.100'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'directus'),
        user=os.getenv('POSTGRES_USER', 'directus'),
        password=os.getenv('POSTGRES_PASSWORD', ''),
        connect_timeout=10
    )

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data(start_date=None, end_date=None, category=None, channel=None):
    """
    Load contact data from PostgreSQL database
    
    Args:
        start_date: Filter from this date
        end_date: Filter to this date
        category: Mental health category filter (fotema)
        channel: Contact channel filter (csatorna)
    
    Returns:
        pandas DataFrame with contact data
    """
    
    # Base query
    query = """
    SELECT 
        j.id,
        j.jegyzokonyv_azonosito,
        j.letrehozva,
        j.csatorna,
        j.megkereso_neve,
        j.eletkor,
        j.nem,
        j.nemi_identitasa,
        j.rovid_hosszu,
        j.miota_megkeresonk,
        j.kivel_el,
        j.hivas_hossza,
        j.temak_listanezet,
        j.altemak_listanezet,
        j.segitseg_listanezet,
        j.szakember_listanezet,
        j.jellemzok_listanezet,
        j.megkereses_tipus,
        j.letrehozo_neve
    FROM jegyzokonyv j
    WHERE 1=1
    """
    
    params = []
    
    # Add date filters
    if start_date:
        query += " AND j.letrehozva >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND j.letrehozva <= %s"
        params.append(pd.Timestamp(end_date) + pd.Timedelta(days=1))
    
    # Add category filter
    if category:
        query += " AND j.temak_listanezet LIKE %s"
        params.append(f'%{category}%')
    
    # Add channel filter
    if channel:
        query += " AND j.csatorna = %s"
        params.append(channel)
    
    query += " ORDER BY j.letrehozva DESC"
    
    # Execute query
    try:
        conn = get_db_connection()
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        # Convert date columns
        if 'letrehozva' in df.columns:
            df['letrehozva'] = pd.to_datetime(df['letrehozva'])
        
        return df
    
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return pd.DataFrame()

def get_mental_health_categories():
    """
    Get list of mental health categories (főtémák) from database
    Based on the n8n workflow logic
    """
    return [
        "Általános lehangoltság",
        "Szorongás, félelmek",
        "Öngyilkossági gondolat",
        "Öngyilkossági késztetés",
        "Akut öngyilkossági kísérlet",
        "Önsértés",
        "Önsértés gondolata",
        "Akut önsértés (nem szuicid szándékkal)",
        "Evészavarok",
        "Diagnosztizált pszichés betegség",
        "Indulatkontroll zavar",
        "Pánik jellegű tünetek",
        "Magány",
        "Önértékelési probléma",
        "Bűntudat, megbánás",
        "Másért való aggódás",
        "Veszteség, gyász",
        "Vetélés",
        "Agresszív késztetések",
        "Pszichés ellátás",
        "Pszichés ellátás hiánya",
        "Szomatikus betegség",
        "Pozitív érzelmek megosztás",
        "Öngyilkosság mint téma"
    ]

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_database_stats():
    """Get basic statistics about the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total records
        cursor.execute("SELECT COUNT(*) FROM jegyzokonyv")
        total_records = cursor.fetchone()[0]
        
        # Date range
        cursor.execute("SELECT MIN(letrehozva), MAX(letrehozva) FROM jegyzokonyv")
        min_date, max_date = cursor.fetchone()
        
        # Unique channels
        cursor.execute("SELECT COUNT(DISTINCT csatorna) FROM jegyzokonyv")
        unique_channels = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_records': total_records,
            'date_range': (min_date, max_date),
            'unique_channels': unique_channels
        }
    
    except Exception as e:
        st.error(f"Error getting database stats: {str(e)}")
        return {}

