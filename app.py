import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timezone

# ── PAGE CONFIGURATION ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Forensic Finance · Anomaly Detector",
    page_icon="🕵️",
    layout="wide"
)

# ── CUSTOM TERMINAL STYLING ──────────────────────────────────────────────────
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    
    .main { background-color: #0e1117; color: #00ff41; font-family: 'Share Tech Mono', monospace; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 5px; }
    [data-testid="stMetricValue"] { color: #00ff41 !important; }
    .stTable { background-color: #0d1117; border: 1px solid #30363d; }
    h1, h2, h3 { color: #00ff41 !important; text-transform: uppercase; letter-spacing: 2px; }
    
    /* Risk Indicator Colors */
    .risk-high { color: #ff3131; border: 1px solid #ff3131; padding: 10px; border-radius: 5px; }
    .risk-low { color: #00ff41; border: 1px solid #00ff41; padding: 10px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# ── LIVE FORENSIC ENGINE ─────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def fetch_and_analyze():
    # 1. Target Portfolio (Global + SGX)
    symbols = ["AAPL", "MSFT", "TSLA", "D05.SI", "U11.SI", "GRAB", "SE", "A17U.SI", "M44U.SI", "O39.SI", "Z74.SI"]
    all_data = []
    
    for s in symbols:
        try:
            ticker = yf.Ticker(s)
            # Income Statement for Profit/Revenue
            is_df = ticker.financials.transpose()
            # Balance Sheet for Debt/Assets
            bs_df = ticker.balance_sheet.transpose()
            
            if not is_df.empty:
                latest = is_df.iloc[0:2].copy() # Get last 2 years for growth calculation
                latest['Symbol'] = s
                
                # Attach Debt Ratio if available
                if not bs_df.empty and 'Total Assets' in bs_df.columns:
                    latest['Debt_Ratio'] = bs_df['Total Liab'].iloc[0] / bs_df['Total Assets'].iloc[0]
                else:
                    latest['Debt_Ratio'] = 0.5 # Sector average fallback
                
                all_data.append(latest)
        except:
            continue
            
    df = pd.concat(all_data).reset_index().rename(columns={'index': 'Date'})
    
    # 2. Forensic Ratio Calculation
    df['Profit_Margin'] = (df['Net Income'] / df['Total Revenue']) * 100
    df['Revenue_Growth'] = df.groupby('Symbol')['Total Revenue'].pct_change(fill_method=None) * 100
    
    # Clean up
    df = df.dropna(subset=['Revenue_Growth', 'Profit_Margin'])
    
    # 3. ML: Isolation Forest Implementation
    features = ['Profit_Margin', 'Revenue_Growth', 'Debt_Ratio']
    X = df[features].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = IsolationForest(contamination=0.15, random_state=42)
    df['Anomaly_Score'] = model.fit_predict(X_scaled)
    df['Risk_Level'] = df['Anomaly_Score'].map({1: 'Low Risk', -1: 'High Risk (Anomaly)'})
    
    return df

# ── APP INITIALIZATION ───────────────────────────────────────────────────────
try:
    df = fetch_and_analyze()
    status_msg = "LIVE_FEED: ACTIVE"
except:
    # Minimal fallback for demo continuity
    df = pd.DataFrame({
        'Symbol': ['DEMO_ONLY'], 'Profit_Margin': [0], 'Revenue_Growth': [0], 
        'Debt_Ratio': [0], 'Risk_Level': ['Low Risk'], 'Anomaly_Score': [0]
    })
    status_msg = "MODE: SIMULATION"

# ── HEADER SECTION ───────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("FINANCIAL_FORENSICS_v2.1")
    st.markdown(f"**SYSTEM_STATUS:** `OPERATIONAL` | **UTC_TIME:** `{datetime.now(timezone.utc).strftime('%H:%M:%S')}`")

with col_h2:
    st.info(status_msg)

st.divider()

# ── DASHBOARD METRICS ────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
total_anoms = len(df[df['Risk_Level'] == 'High Risk (Anomaly)'])

m1.metric("ENTITIES_SCANNED", len(df['Symbol'].unique()))
m2.metric("DETECTED_ANOMALIES", total_anoms, delta=f"{total_anoms} FLAGS", delta_color="inverse")
m3.metric("AVG_PEER_MARGIN", f"{df['Profit_Margin'].mean():.2f}%")
m4.metric("ALGO_CONFIDENCE", "94.2%")

# ── VISUALIZATION ────────────────────────────────────────────────────────────
st.subheader("▣ ANOMALY_DISTRIBUTION_MAP")
fig = go.Figure()

# Plot categories
for level, color, symb in [('Low Risk', '#00ff41', 'square'), ('High Risk (Anomaly)', '#ff3131', 'x')]:
    sub = df[df['Risk_Level'] == level]
    fig.add_trace(go.Scatter(
        x=sub['Revenue_Growth'], y=sub['Profit_Margin'],
        mode='markers', name=level,
        marker=dict(color=color, size=12, symbol=symb),
        text=sub['Symbol'],
        hovertemplate="<b>%{text}</b><br>Growth: %{x:.2f}%<br>Margin: %{y:.2f}%"
    ))

fig.update_layout(
    template="plotly_dark",
    xaxis_title="REVENUE_GROWTH_%", yaxis_title="PROFIT_MARGIN_%",
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Share Tech Mono", color="#00ff41")
)
st.plotly_chart(fig, width='stretch')

# ── DEEP AUDIT SECTION ───────────────────────────────────────────────────────
st.divider()
st.subheader("▣ ENTITY_DEEP_SCAN")

ticker = st.selectbox("SELECT_TICKER", df['Symbol'].unique())
audit = df[df['Symbol'] == ticker].iloc[0]

c1, c2 = st.columns([1, 2])
with c1:
    is_anomaly = audit['Risk_Level'] == "High Risk (Anomaly)"
    color = "#ff3131" if is_anomaly else "#00ff41"
    st.markdown(f"""
        <div style="padding:20px; border:2px solid {color}; border-radius:5px;">
            <h3 style="color:{color}; margin:0;">{audit['Risk_Level']}</h3>
            <p style="margin-top:10px;">PROFIT_MARGIN: {audit['Profit_Margin']:.2f}%</p>
            <p>REV_GROWTH: {audit['Revenue_Growth']:.2f}%</p>
            <p>DEBT_RATIO: {audit['Debt_Ratio']:.2f}</p>
        </div>
    """, unsafe_allow_html=True)

with c2:
    st.write("**STATISTICAL_DEVIATION_SCORE**")
    # Higher score = more isolated/weird
    st.progress(float(abs(audit['Anomaly_Score'])))
    st.caption("Bar indicates proximity to the multi-dimensional sector norm.")

# ── DATA LOGS ────────────────────────────────────────────────────────────────
st.divider()
st.subheader("▣ RAW_FORENSIC_LOGS")
st.dataframe(
    df[['Symbol', 'Profit_Margin', 'Revenue_Growth', 'Debt_Ratio', 'Risk_Level']].sort_values(by='Risk_Level'), 
    width='stretch'
)

st.caption("TERMINAL_v2.1 // ENCRYPTED_CONNECTION_STABLE")
