# Streamlit Live Economic Heatmap & Bias Tracker (Fixed Indentation)

import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import datetime

# --- DATABASE SETUP ---
DB_NAME = "macro_history.db"
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS macro_data (
    region TEXT,
    indicator TEXT,
    date TEXT,
    actual REAL,
    forecast REAL,
    previous REAL,
    surprise REAL,
    bias TEXT
)''')
conn.commit()

# --- SUPPORTED REGIONS ---
REGIONS = {"US": "USD", "EU": "EUR", "UK": "GBP", "JP": "JPY", "CA": "CAD"}

# --- LIVE ECONOMIC CALENDAR SCRAPER ---
def get_live_events():
    url = 'https://www.investing.com/economic-calendar/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', {'id': 'economicCalendarData'})
    events = []
    today = datetime.date.today().isoformat()
    if table and table.tbody:
        for row in table.tbody.find_all('tr', attrs={'data-eventid': True}):
            cells = row.find_all('td')
            curr = cells[2].get_text(strip=True)
            if curr not in REGIONS.values():
                continue
            event = cells[3].get_text(strip=True)
            actual = cells[4].get_text(strip=True) or None
            forecast = cells[5].get_text(strip=True) or None
            previous = cells[6].get_text(strip=True) or None
            try:
                actual_f = float(actual)
                forecast_f = float(forecast)
                previous_f = float(previous) if previous else None
            except:
                continue
            surprise = round(actual_f - forecast_f, 2)
            bias = 'Bullish' if surprise > 0 else 'Bearish' if surprise < 0 else 'Neutral'
            region_key = next(k for k, v in REGIONS.items() if v == curr)
            events.append({
                'region': region_key,
                'indicator': event,
                'date': today,
                'actual': actual_f,
                'forecast': forecast_f,
                'previous': previous_f,
                'surprise': surprise,
                'bias': bias
            })
    cols = ['region','indicator','date','actual','forecast','previous','surprise','bias']
    return pd.DataFrame(events, columns=cols)

# --- STREAMLIT APP ---
st.set_page_config(layout="wide")
st.title("🌐 Live Economic Heatmap & Bias Tracker")

# Region selection
region = st.selectbox(
    "Select Region/Currency:",
    list(REGIONS.keys()),
    format_func=lambda x: f"{x} ({REGIONS[x]})"
)

# Fetch live data
df_live = get_live_events()
st.subheader("📅 Today's Economic Calendar")

# Fallback to show most recent stored data

def show_recent_from_db():
    hist_all = pd.read_sql_query(
        "SELECT * FROM macro_data WHERE region=? ORDER BY date DESC", conn,
        params=(region,)
    )
    if hist_all.empty:
        st.warning("No stored data available.")
        return
    hist_all['date'] = pd.to_datetime(hist_all['date'])
    latest_date = hist_all['date'].max().date()
    recent = hist_all[hist_all['date'].dt.date == latest_date]
    st.subheader(f"Most Recent Data ({latest_date})")
    st.dataframe(recent[['indicator','actual','forecast','previous','surprise','bias']])
    counts = recent['bias'].value_counts()
    overall = (
        'Bullish' if counts.get('Bullish',0) > counts.get('Bearish',0)
        else 'Bearish' if counts.get('Bearish',0) > counts.get('Bullish',0)
        else 'Neutral'
    )
    st.markdown(f"## ⚖️ Overall Market Bias: **{overall}**")

# Display live or fallback data
if df_live.empty:
    st.info("No live economic events could be fetched at this time. Showing most recent stored data.")
    show_recent_from_db()
else:
    sub = df_live[df_live['region'] == region]
    if sub.empty:
        st.info("No live events for this region today. Showing most recent stored data.")
        show_recent_from_db()
    else:
        st.dataframe(sub[['indicator','actual','forecast','previous','surprise','bias']])
        st.markdown("### 🧠 Event Bias Explanations")
        for _, r in sub.iterrows():
            st.markdown(
                f"- **{r['indicator']}**: Actual {r['actual']} vs Forecast {r['forecast']} "
                f"→ Surprise {r['surprise']} → **{r['bias']}**"
            )
        counts = sub['bias'].value_counts()
        overall = (
            'Bullish' if counts.get('Bullish',0) > counts.get('Bearish',0)
            else 'Bearish' if counts.get('Bearish',0) > counts.get('Bullish',0)
            else 'Neutral'
        )
        st.markdown(f"## ⚖️ Overall Market Bias: **{overall}**")
        for _, r in sub.iterrows():
            c.execute(
                "INSERT INTO macro_data VALUES (?,?,?,?,?,?,?,?)",(
                    region, r['indicator'], r['date'], r['actual'], r['forecast'],
                    r['previous'], r['surprise'], r['bias']
                )
            )
        conn.commit()

# Historical data
st.subheader("📈 Historical Records")
hist = pd.read_sql_query(
    "SELECT region, indicator, date, actual, forecast, previous, surprise FROM macro_data WHERE region=? ORDER BY date DESC", conn,
    params=(region,)
)
hist['date'] = pd.to_datetime(hist['date'])

# Date filter input
default_start = datetime.date.today() - datetime.timedelta(days=30)
default_end = datetime.date.today()
dates = st.date_input(
    "Filter by date range:",
    value=(default_start, default_end),
    help="Select start and end dates"
)
if isinstance(dates, (list, tuple)) and len(dates) == 2:
    start_date, end_date = dates
else:
    start_date = end_date = dates

filtered = hist[(hist['date'] >= pd.to_datetime(start_date)) & (hist['date'] <= pd.to_datetime(end_date))]
st.dataframe(filtered)

# Bias evolution chart
st.markdown("### 📊 Bullish Bias % Over Time")
time_df = (
    hist.groupby(hist['date'].dt.date)['surprise']
    .apply(lambda s: (s > 0).sum() / len(s) * 100)
    .reset_index(name='bullish_pct')
)
fig_line = px.line(time_df, x='date', y='bullish_pct', title='Bullish Bias % Over Time')
st.plotly_chart(fig_line, use_container_width=True)

# CSV Export
st.download_button(
    label="Download Historical Data as CSV",
    data=filtered.to_csv(index=False).encode('utf-8'),
    file_name=f'{region}_history.csv',
    mime='text/csv'
)

conn.close()
