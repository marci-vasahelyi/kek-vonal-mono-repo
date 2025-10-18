# 📊 Mental Health Dashboard

Interactive data visualization dashboard for Kék Vonal psychological support contacts.

## Features

- **📈 Trends**: Monthly, weekly, and hourly contact patterns
- **👥 Demographics**: Gender distribution and age analysis
- **📞 Channels**: Contact method breakdown and trends
- **🧠 Topics**: Mental health category analysis
- **📊 Raw Data**: Exportable data tables

## Tech Stack

- **Streamlit**: Interactive web UI
- **Plotly**: Interactive charts and graphs
- **Pandas**: Data processing
- **PostgreSQL**: Database (shared with Directus)

## Quick Start

### 1. Install Dependencies

```bash
cd apps/dashboard
pip install -r requirements.txt
```

### 2. Configure Environment

The dashboard uses the same `.env` file as the rest of the monorepo:

```bash
# Already configured in root .env:
POSTGRES_USER=directus
POSTGRES_PASSWORD=your_password
POSTGRES_DB=directus
DB_HOST=192.168.1.100  # or localhost for local dev
DB_PORT=5432
```

### 3. Run Dashboard

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## Usage

### Filters

- **Date Range**: Select start and end dates
- **Mental Health Category**: Filter by specific psychological topics
- **Contact Channel**: Filter by contact method (phone, chat, email)

### Tabs

1. **📈 Trends**: View contact patterns over time
2. **👥 Demographics**: Analyze age and gender distribution
3. **📞 Channels**: Understand how people reach out
4. **🧠 Topics**: See most common mental health concerns
5. **📊 Raw Data**: Export filtered data as CSV

## Development

### Project Structure

```
apps/dashboard/
├── app.py                 # Main Streamlit application
├── data_loader.py         # Database connection and queries
├── visualizations.py      # Plotly chart functions
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Database Schema

The dashboard reads from the `jegyzokonyv` table:

**Key Fields**:
- `letrehozva`: Creation timestamp
- `csatorna`: Contact channel (Telefon, Chat, Email)
- `eletkor`: Age
- `nemi_identitasa`: Gender identity
- `temak_listanezet`: Mental health topics (comma-separated)
- `altemak_listanezet`: Subtopics
- `hivas_hossza`: Conversation duration
- `rovid_hosszu`: Short/long conversation flag

### Adding New Visualizations

1. Add chart function to `visualizations.py`:
```python
def create_my_chart(df):
    fig = px.bar(df, x='column', y='value')
    return fig
```

2. Import and use in `app.py`:
```python
from visualizations import create_my_chart

fig = create_my_chart(df)
st.plotly_chart(fig, use_container_width=True)
```

## Docker Deployment (Optional)

### Add to docker-compose.yml

```yaml
dashboard:
  build: ./apps/dashboard
  ports:
    - "8501:8501"
  environment:
    - POSTGRES_USER=${POSTGRES_USER}
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    - POSTGRES_DB=${POSTGRES_DB}
    - DB_HOST=database
    - DB_PORT=5432
  depends_on:
    - database
  networks:
    - directus
```

### Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

## Performance

- **Data Caching**: Queries are cached for 5 minutes
- **Connection Pooling**: Reuses database connections
- **Lazy Loading**: Charts render on-demand per tab

## Security

- Database credentials in `.env` (gitignored)
- Read-only database access recommended
- No data modification, only visualization
- Local deployment by default (not exposed to internet)

## Troubleshooting

### "No data available"
- Check database connection in `.env`
- Verify `jegyzokonyv` table exists
- Check date filters (data within range?)

### Slow loading
- Increase cache TTL in `data_loader.py`
- Reduce date range filter
- Add database indexes on `letrehozva` column

### Connection errors
```bash
# Test database connection
python -c "from data_loader import get_db_connection; conn = get_db_connection(); print('✅ Connected')"
```

## Future Enhancements

- [ ] User authentication
- [ ] Export to PDF reports
- [ ] Email alerts for anomalies
- [ ] Predictive analytics
- [ ] Real-time updates (WebSocket)
- [ ] Multi-language support
- [ ] Mobile responsive design
- [ ] Advanced filtering (multiple categories)

## Data Privacy

⚠️ **Important**: This dashboard displays aggregated mental health data.
- No personally identifiable information shown
- Names are excluded from visualizations
- Follow data protection regulations (GDPR)
- Use secure connections in production

## Support

For issues or questions:
- Check [MAINTENANCE.md](../../docs/MAINTENANCE.md) for database maintenance
- Review [SECURITY.md](../../docs/SECURITY.md) for security guidelines
- Database schema: See Directus admin panel

## License

Internal use only - Kék Vonal organization

