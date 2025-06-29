# Streamlit US Economic Heatmap (Live Data from Investing.com)

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go
import datetime

st.set_page_config(layout="wide", page_title="US Economic Heatmap")
st.title("🇺🇸 US Economic Heatmap | Live Data")

# --- FUNCTIONS ---
def fetch_us_calendar():
    """
    Scrape Investing.com US economic calendar for today and returns DataFrame with actual, forecast, previous.
    """
    url = 'https://www.investing.com/economic-calendar/'
    headers = {'User-Agent': 'Mozilla/5.0'}
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', {'id':'economicCalendarData'})
    rows = []
    today = datetime.date.today().strftime('%b %d, %y')
    if table and table.tbody:
        for tr in table.tbody.find_all('tr', attrs={'data-eventid': True}):
            tds = tr.find_all('td')
            region = tds[2].get_text(strip=True)
            if region != 'USD':
                continue
            indicator = tds[3].get_text(strip=True)
            date = tds[1].get_text(strip=True)
            actual = tds[4].get_text(strip=True) or np.nan
            forecast = tds[5].get_text(strip=True) or np.nan
            previous = tds[6].get_text(strip=True) or np.nan
            # convert values
            def to_num(x):
                try:
                    return float(x.replace('%','').replace('K','').replace(',',''))
                except:
                    return np.nan
            actual_n = to_num(actual)
            forecast_n = to_num(forecast)
            previous_n = to_num(previous)
            surprise = actual_n - forecast_n if not np.isnan(actual_n) and not np.isnan(forecast_n) else np.nan
            usd_impact = 'Bullish' if surprise>0 else 'Bearish' if surprise<0 else 'Neutral'
            stocks_impact = usd_impact
            rows.append({
                'Indicator': indicator,
                'Date': date,
                'Surprise': f"{surprise:+.2f}" if not np.isnan(surprise) else '',
                'Actual': actual,
                'Forecast': forecast,
                'Previous': previous,
                'USD Impact': usd_impact,
                'Stocks Impact': stocks_impact
            })
    return pd.DataFrame(rows)

# Fetch and display
df = fetch_us_calendar()
st.subheader("US Economic Calendar Today")
if df.empty:
    st.warning("No USD events found or unable to fetch data.")
else:
    # style impact columns
    def color_map(val):
        if val=='Bullish': return 'background-color: #4a90e2; color:white'
        if val=='Bearish': return 'background-color: #d0021b; color:white'
        return ''
    styled = df.style.applymap(color_map, subset=['USD Impact','Stocks Impact'])
    st.dataframe(styled, use_container_width=True)

    # Overall bias gauge
    counts = df['USD Impact'].value_counts()
    pct = counts.get('Bullish',0)/len(df)*100
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        title={'text':'USD Bullish %'},
        gauge={'axis':{'range':[0,100]},
               'bar':{'color':'#4a90e2'},
               'steps':[
                   {'range':[0,40],'color':'#d0021b'},
                   {'range':[40,60],'color':'#9b9b9b'},
                   {'range':[60,100],'color':'#4a90e2'}
               ]}
    ))
    st.subheader("Overall USD Bias")
    st.plotly_chart(fig, use_container_width=True)

    # Explanations
    st.subheader("Event Bias Explanations")
    for _, r in df.iterrows():
        st.markdown(f"- **{r['Indicator']}**: Surprise {r['Surprise']} → **{r['USD Impact']}**")

# End
