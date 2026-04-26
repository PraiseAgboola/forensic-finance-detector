import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timezone

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Forensic Finance · Anomaly Detector", page_icon="🕵️", layout="wide")

# [KEEP ALL YOUR BEAUTIFUL CSS HERE...]

# ── NEW: Live Forensic Engine ────────────────────────────────────────────────
@st.cache_data(ttl=3600) # Refreshes every hour
def fetch_and_analyze():
    # 1. Pull Live Data
    symbols = ["AAPL", "MSFT", "TSLA", "D05.SI", "U11.SI", "GRAB", "SE", "A17U.SI", "M44U.SI"]
    all_data = []
    for s in symbols:
        ticker = yf.Ticker(s)
        df_temp = ticker.financials.transpose()
        if not df_temp.empty:
            df_temp['Symbol'] = s
            # Get Debt Ratio from Balance Sheet
            bs = ticker.balance_sheet.transpose()
            if 'Total Assets' in bs.columns and 'Total Liab' in bs.columns:
                 df_temp['Debt_Ratio'] = bs['Total Liab'] / bs['Total Assets']
            all_data.append(df_temp)
    
    df = pd.concat(all_data).reset_index().rename(columns={'index': 'Date'})
    
    # 2. Calculate Ratios
    df['Profit_Margin'] = (df['Net Income'] / df['Total Revenue']) * 100
    df['Revenue_Growth'] = df.groupby('Symbol')['Total Revenue'].pct_change() * 100
    df = df.dropna(subset=['Profit_Margin', 'Revenue_Growth']).fillna(0)
    
    # 3. ML: Isolation Forest
    features = ['Profit_Margin', 'Revenue_Growth', 'Debt_Ratio']
    X = df[features]
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = IsolationForest(contamination=0.15, random_state=42)
    df['Anomaly_Score'] = model.fit_predict(X_scaled)
    df['Risk_Level'] = df['Anomaly_Score'].map({1: 'Low Risk', -1: 'High Risk (Anomaly)'})
    
    return df

# ── RUN ENGINE ───────────────────────────────────────────────────────────────
try:
    df = fetch_and_analyze()
    using_real_data = True
except Exception as e:
    st.error(f"Engine Error: {e}")
    # Fallback to your SAMPLE data if yfinance fails
    df = SAMPLE 
    using_real_data = False

# [KEEP THE REST OF YOUR UI CODE HERE...]
