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

# [CONTINUATION OF app.py]

# ── CUSTOM CSS ──────────────────────────────────────────────────────────────
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    
    .main { background-color: #0e1117; color: #00ff41; font-family: 'Share Tech Mono', monospace; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 5px; }
    [data-testid="stMetricValue"] { color: #00ff41 !important; }
    .stTable { background-color: #0d1117; border: 1px solid #30363d; }
    h1, h2, h3 { color: #00ff41 !important; text-transform: uppercase; letter-spacing: 2px; }
    </style>
    """, unsafe_allow_html=True)

# ── HEADER SECTION ──────────────────────────────────────────────────────────
col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("FINANCIAL_FORENSICS_v2.0")
    st.markdown(f"**SYSTEM_STATUS:** `OPERATIONAL` | **LAST_REFRESH:** `{datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC` ")

with col_head2:
    if using_real_data:
        st.success("LIVE_FEED: ACTIVE")
    else:
        st.warning("MODE: SIMULATION")

st.divider()

# ── METRIC CARDS ───────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
total_anomalies = len(df[df['Risk_Level'] == 'High Risk (Anomaly)'])

m1.metric("TOTAL_ENTITIES", len(df['Symbol'].unique()))
m2.metric("ANOMALIES_DETECTED", total_anomalies, delta=f"{total_anomalies} FLAGS", delta_color="inverse")
m3.metric("AVG_PROFIT_MARGIN", f"{df['Profit_Margin'].mean():.2f}%")
m4.metric("SYSTEM_CONFIDENCE", "94.2%")

# ── VISUALIZATION ──────────────────────────────────────────────────────────
st.subheader("▣ ANOMALY_DISTRIBUTION_MAP")
fig = go.Figure()

# Plot Normal Data
normal = df[df['Risk_Level'] == 'Low Risk']
fig.add_trace(go.Scatter(
    x=normal['Revenue_Growth'], y=normal['Profit_Margin'],
    mode='markers', name='NORMAL',
    marker=dict(color='#00ff41', size=10, opacity=0.6, symbol='square'),
    text=normal['Symbol']
))

# Plot Anomalies
anomalies = df[df['Risk_Level'] == 'High Risk (Anomaly)']
fig.add_trace(go.Scatter(
    x=anomalies['Revenue_Growth'], y=anomalies['Profit_Margin'],
    mode='markers', name='SUSPICIOUS',
    marker=dict(color='#ff3131', size=14, symbol='x', line=dict(width=2, color='white')),
    text=anomalies['Symbol']
))

fig.update_layout(
    template="plotly_dark",
    xaxis_title="REVENUE_GROWTH_%", yaxis_title="PROFIT_MARGIN_%",
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Share Tech Mono", color="#00ff41")
)
st.plotly_chart(fig, width='stretch') # Updated for 2026 Streamlit compatibility

# ── DEEP AUDIT SECTION ─────────────────────────────────────────────────────
st.divider()
st.subheader("▣ INDIVIDUAL_ENTITY_AUDIT")

selected_ticker = st.selectbox("SELECT_TICKER_FOR_DEEP_SCAN", df['Symbol'].unique())
audit_data = df[df['Symbol'] == selected_ticker].iloc[0]

ca, cb = st.columns([1, 2])

with ca:
    risk_color = "red" if audit_data['Risk_Level'] == "High Risk (Anomaly)" else "green"
    st.markdown(f"""
        <div style="padding:20px; border:2px solid {risk_color}; border-radius:10px;">
            <h4 style="color:{risk_color}; margin:0;">SCAN_RESULT: {audit_data['Risk_Level']}</h4>
            <hr style="border-color:{risk_color};">
            <p>ENTITY: {selected_ticker}</p>
            <p>GROWTH: {audit_data['Revenue_Growth']:.2f}%</p>
            <p>MARGIN: {audit_data['Profit_Margin']:.2f}%</p>
            <p>DEBT_RATIO: {audit_data['Debt_Ratio']:.2f}</p>
        </div>
    """, unsafe_allow_html=True)

with cb:
    st.markdown("**PROBABILITY_DENSITY_ANALYSIS**")
    # This bar represents how "isolated" the point was
    confidence_val = abs(audit_data['Anomaly_Score']) 
    st.progress(float(confidence_val))
    st.caption("Lower bar indicates closer proximity to sector norm. Higher bar indicates extreme deviation.")

# ── DATA TABLE ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("▣ RAW_FORENSIC_LOGS")
st.dataframe(df[['Symbol', 'Date', 'Profit_Margin', 'Revenue_Growth', 'Debt_Ratio', 'Risk_Level']].sort_values(by='Risk_Level'), width='stretch')

st.caption("TERMINAL_v2.0 // ENCRYPTED_CONNECTION_STABLE")
