# 🚀 Quick Start Guide

## ✅ MVP is Running!

**Dashboard URL**: http://localhost:8501

## If Database Connection Fails

### 1. Check Directus is Running

```bash
cd ../..
docker-compose ps database
```

Should show `database` as "Up"

### 2. Test Database Connection

```bash
# From dashboard directory
source venv/bin/activate
python3 << 'EOF'
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv("../../.env")

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    print("✅ Database connection successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jegyzokonyv")
    count = cursor.fetchone()[0]
    print(f"✅ Found {count} records in jegyzokonyv table")
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
EOF
```

### 3. Common Issues

**"Connection refused"**
- Start database: `docker-compose up -d database`
- Check port in `.env`: should be `DB_PORT=5432`

**"No table jegyzokonyv"**
- Database might be empty
- Restore from backup first (see main README.md)

**"Permission denied"**
- Check credentials in `.env`
- Make sure `POSTGRES_PASSWORD` is correct

## Stop Dashboard

```bash
# Find process
ps aux | grep streamlit

# Kill it
kill <PID>

# Or restart
./run.sh
```

## View Logs

```bash
# Dashboard logs are in terminal where you ran run.sh
# Or check:
tail -f ~/.streamlit/logs/*.log
```

## Test with Sample Data

If database is empty, you can test with mock data:

```bash
# TODO: Add sample data generator if needed
```

## 🎉 What You Should See

- **KPI Cards**: Total contacts, average age, etc.
- **5 Tabs**: Trends, Demographics, Channels, Topics, Raw Data
- **Filters**: Date range, category, channel selectors
- **Charts**: Interactive Plotly visualizations

## 📊 Features

- Click and drag on charts to zoom
- Hover for details
- Download charts as PNG
- Export data as CSV

## Need Help?

Check: `apps/dashboard/README.md` for full documentation

