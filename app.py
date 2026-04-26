import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import json

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Forensic Finance · Anomaly Detector",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS — Bloomberg / dark-terminal aesthetic ─────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Syne:wght@400;700&display=swap');

/* ── Reset & root ── */
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif !important;
    background-color: #0a0d12 !important;
    color: #c8d6ef !important;
}
.stApp { background-color: #0a0d12 !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 20px 28px 40px !important; max-width: 100% !important; }

/* ── Scanline overlay ── */
.stApp::before {
    content: '';
    position: fixed; inset: 0; pointer-events: none; z-index: 9999;
    background: repeating-linear-gradient(
        0deg, transparent, transparent 2px,
        rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px
    );
}

/* ── Plotly chart background ── */
.js-plotly-plot .plotly, .js-plotly-plot .plotly .main-svg {
    background: transparent !important;
}

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #10141c !important;
    border: 1px solid #1e2535 !important;
    border-radius: 0 !important;
    padding: 16px 18px !important;
}
[data-testid="metric-container"] label {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 9px !important;
    color: #5a7090 !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 28px !important;
    color: #c8d6ef !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 10px !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: #10141c !important;
    border: 1px solid #1e2535 !important;
    border-radius: 0 !important;
    color: #c8d6ef !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 11px !important;
}

/* ── Multiselect ── */
[data-testid="stMultiSelect"] > div {
    background: #10141c !important;
    border: 1px solid #1e2535 !important;
    border-radius: 0 !important;
}
.stMultiSelect span {
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 10px !important;
    background: #1e2535 !important;
    color: #00e5ff !important;
    border-radius: 0 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0d1018 !important;
    border-right: 1px solid #1e2535 !important;
}
[data-testid="stSidebar"] * { color: #c8d6ef !important; }

/* ── Horizontal rule ── */
hr { border-color: #1e2535 !important; }

/* ── Dataframe / table ── */
[data-testid="stDataFrame"] { background: #10141c !important; }
.dataframe { background: #10141c !important; color: #c8d6ef !important; }

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div {
    background: #1e2535 !important;
    border-radius: 0 !important;
}
[data-testid="stProgressBar"] > div > div {
    border-radius: 0 !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
MONO = "Share Tech Mono"

def mono(text: str, color: str = "#c8d6ef", size: int = 13,
         spacing: int = 2, weight: str = "normal") -> str:
    return (
        f"<span style=\"font-family:'{MONO}',monospace;"
        f"font-size:{size}px;color:{color};"
        f"letter-spacing:{spacing}px;font-weight:{weight}\">"
        f"{text}</span>"
    )

def panel_header(title: str, tag: str = "") -> None:
    tag_html = (
        f"<span style=\"font-family:'{MONO}',monospace;font-size:9px;"
        f"padding:3px 10px;border:1px solid #2a3347;color:#5a7090;letter-spacing:1px\">"
        f"{tag}</span>" if tag else ""
    )
    st.markdown(
        f"<div style='display:flex;align-items:center;justify-content:space-between;"
        f"padding:10px 0 10px;border-bottom:1px solid #1e2535;margin-bottom:14px'>"
        f"<span style=\"font-family:'{MONO}',monospace;font-size:10px;"
        f"color:#00e5ff;letter-spacing:3px;text-transform:uppercase\">{title}</span>"
        f"{tag_html}</div>",
        unsafe_allow_html=True,
    )

def badge(text: str, high: bool) -> str:
    color = "#ff3d71" if high else "#00d68f"
    return (
        f"<span style=\"font-family:'{MONO}',monospace;font-size:8px;"
        f"padding:2px 7px;border:1px solid {color};color:{color};"
        f"letter-spacing:1px\">{text}</span>"
    )


# ── Sample / fallback data ────────────────────────────────────────────────────
SAMPLE = pd.DataFrame([
    {"Symbol":"NVDA","Risk_Level":"Low Risk","Revenue_Growth":122,"Profit_Margin":55,"PE_Ratio":65,"Debt_Equity":0.42,"Anomaly_Score":-0.12},
    {"Symbol":"MSFT","Risk_Level":"Low Risk","Revenue_Growth":18,"Profit_Margin":45,"PE_Ratio":32,"Debt_Equity":0.55,"Anomaly_Score":-0.08},
    {"Symbol":"AAPL","Risk_Level":"Low Risk","Revenue_Growth":8,"Profit_Margin":26,"PE_Ratio":28,"Debt_Equity":1.76,"Anomaly_Score":-0.09},
    {"Symbol":"META","Risk_Level":"Low Risk","Revenue_Growth":27,"Profit_Margin":33,"PE_Ratio":24,"Debt_Equity":0.10,"Anomaly_Score":-0.11},
    {"Symbol":"AMZN","Risk_Level":"Low Risk","Revenue_Growth":13,"Profit_Margin":8,"PE_Ratio":58,"Debt_Equity":0.82,"Anomaly_Score":-0.07},
    {"Symbol":"TSLA","Risk_Level":"High Risk (Anomaly)","Revenue_Growth":-5,"Profit_Margin":9,"PE_Ratio":80,"Debt_Equity":0.18,"Anomaly_Score":0.34},
    {"Symbol":"UBER","Risk_Level":"High Risk (Anomaly)","Revenue_Growth":14,"Profit_Margin":-2,"PE_Ratio":None,"Debt_Equity":2.10,"Anomaly_Score":0.41},
    {"Symbol":"SNAP","Risk_Level":"High Risk (Anomaly)","Revenue_Growth":5,"Profit_Margin":-42,"PE_Ratio":None,"Debt_Equity":3.50,"Anomaly_Score":0.62},
    {"Symbol":"COIN","Risk_Level":"High Risk (Anomaly)","Revenue_Growth":-54,"Profit_Margin":-20,"PE_Ratio":None,"Debt_Equity":0.85,"Anomaly_Score":0.57},
    {"Symbol":"SHOP","Risk_Level":"Low Risk","Revenue_Growth":26,"Profit_Margin":4,"PE_Ratio":72,"Debt_Equity":0.13,"Anomaly_Score":-0.05},
    {"Symbol":"PLTR","Risk_Level":"High Risk (Anomaly)","Revenue_Growth":20,"Profit_Margin":-8,"PE_Ratio":220,"Debt_Equity":0.04,"Anomaly_Score":0.38},
    {"Symbol":"RIVN","Risk_Level":"High Risk (Anomaly)","Revenue_Growth":167,"Profit_Margin":-120,"PE_Ratio":None,"Debt_Equity":1.20,"Anomaly_Score":0.71},
    {"Symbol":"AMD","Risk_Level":"Low Risk","Revenue_Growth":4,"Profit_Margin":5,"PE_Ratio":64,"Debt_Equity":0.05,"Anomaly_Score":-0.06},
    {"Symbol":"GOOG","Risk_Level":"Low Risk","Revenue_Growth":10,"Profit_Margin":26,"PE_Ratio":25,"Debt_Equity":0.06,"Anomaly_Score":-0.10},
    {"Symbol":"NFLX","Risk_Level":"Low Risk","Revenue_Growth":15,"Profit_Margin":18,"PE_Ratio":43,"Debt_Equity":1.47,"Anomaly_Score":-0.04},
])


# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data() -> tuple[pd.DataFrame, bool]:
    try:
        df = pd.read_csv("results.csv")
        required = {"Symbol", "Risk_Level", "Revenue_Growth", "Profit_Margin"}
        if not required.issubset(df.columns):
            return SAMPLE, False
        # Fill optional columns with sensible defaults
        for col, default in [("Anomaly_Score", 0.0), ("Debt_Equity", 0.0), ("PE_Ratio", None)]:
            if col not in df.columns:
                df[col] = default
        return df, True
    except FileNotFoundError:
        return SAMPLE, False


df, using_real_data = load_data()

IS_HIGH = df["Risk_Level"] == "High Risk (Anomaly)"
n_total  = len(df)
n_high   = int(IS_HIGH.sum())
pct_high = round(n_high / n_total * 100)


# ── TOP BAR ──────────────────────────────────────────────────────────────────
now_utc = datetime.now(timezone.utc).strftime("%d %b %Y  %H:%M UTC")

st.markdown(
    f"""
    <div style='display:flex;align-items:center;justify-content:space-between;
                padding-bottom:14px;border-bottom:1px solid #1e2535;margin-bottom:20px'>
      <div style='display:flex;align-items:center;gap:14px'>
        <div style='width:36px;height:36px;border:1.5px solid #00e5ff;
                    display:flex;align-items:center;justify-content:center;position:relative;flex-shrink:0'>
          <div style='position:absolute;inset:3px;border:1px solid #2d3f58'></div>
          <span style="font-family:'{MONO}',monospace;font-size:10px;color:#00e5ff;letter-spacing:2px;position:relative">FF</span>
        </div>
        <div>
          <div style="font-family:'{MONO}',monospace;font-size:13px;color:#00e5ff;letter-spacing:3px">FORENSIC FINANCE</div>
          <div style="font-family:'{MONO}',monospace;font-size:10px;color:#5a7090;letter-spacing:2px;margin-top:2px">
            ANOMALY DETECTION SYSTEM · TRANSPARENTLY.AI / ENDOWUS
          </div>
        </div>
      </div>
      <div style='display:flex;align-items:center;gap:20px'>
        <span style="font-family:'{MONO}',monospace;font-size:10px;padding:4px 10px;
                     border:1px solid #00d68f;color:#00d68f;letter-spacing:1px">● LIVE</span>
        <span style="font-family:'{MONO}',monospace;font-size:10px;color:#5a7090">{now_utc}</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if not using_real_data:
    st.markdown(
        f"<div style='font-family:\"{MONO}\",monospace;font-size:10px;letter-spacing:2px;"
        f"color:#ffaa00;border:1px solid #ffaa00;padding:6px 14px;margin-bottom:16px;"
        f"display:inline-block'>⚠ DEMO MODE — results.csv not found. Showing sample data.</div>",
        unsafe_allow_html=True,
    )


# ── SIDEBAR — filters ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<div style=\"font-family:'{MONO}',monospace;font-size:11px;"
        f"color:#00e5ff;letter-spacing:3px;margin-bottom:16px\">FILTERS</div>",
        unsafe_allow_html=True,
    )
    risk_filter = st.multiselect(
        "Risk Level",
        options=df["Risk_Level"].unique().tolist(),
        default=df["Risk_Level"].unique().tolist(),
    )
    st.markdown("---")
    rev_min, rev_max = int(df["Revenue_Growth"].min()), int(df["Revenue_Growth"].max())
    rev_range = st.slider("Revenue Growth (%)", rev_min, rev_max, (rev_min, rev_max))
    st.markdown("---")
    pm_min, pm_max = int(df["Profit_Margin"].min()), int(df["Profit_Margin"].max())
    pm_range = st.slider("Profit Margin (%)", pm_min, pm_max, (pm_min, pm_max))


# ── Apply filters ─────────────────────────────────────────────────────────────
mask = (
    df["Risk_Level"].isin(risk_filter) &
    df["Revenue_Growth"].between(*rev_range) &
    df["Profit_Margin"].between(*pm_range)
)
filtered = df[mask].copy()


# ── METRIC CARDS ─────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Companies Analyzed", n_total, "Portfolio universe")

with c2:
    st.metric(
        "High-Risk Anomalies",
        n_high,
        f"{pct_high}% of universe",
        delta_color="inverse",
    )

with c3:
    st.metric("Market Sentiment", "CAUTIONARY", "-2.4% 30d momentum", delta_color="inverse")

st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)


# ── SCATTER MAP + RISK QUEUE ─────────────────────────────────────────────────
import plotly.graph_objects as go

col_chart, col_queue = st.columns([3, 1.4])

with col_chart:
    panel_header("Anomaly Scatter Map", "ISO-FOREST")

    low_df  = filtered[~(filtered["Risk_Level"] == "High Risk (Anomaly)")]
    high_df = filtered[filtered["Risk_Level"] == "High Risk (Anomaly)"]

    fig = go.Figure()

    # Grid-style axis lines
    fig.add_hline(y=0, line_color="#2d3f58", line_dash="dot", line_width=1)
    fig.add_vline(x=0, line_color="#2d3f58", line_dash="dot", line_width=1)

    def make_hover(d):
        return [
            f"<b style='font-family:Share Tech Mono'>{sym}</b><br>"
            f"<span style='color:#5a7090'>REV GROWTH</span> {rg}%<br>"
            f"<span style='color:#5a7090'>PROFIT MARGIN</span> {pm}%<br>"
            f"<span style='color:#5a7090'>ANOMALY SCORE</span> {sc:.2f}"
            for sym, rg, pm, sc in zip(d["Symbol"], d["Revenue_Growth"],
                                        d["Profit_Margin"], d["Anomaly_Score"])
        ]

    for subset, color, name, symbol in [
        (low_df,  "#00d68f", "Low Risk",            "circle"),
        (high_df, "#ff3d71", "High Risk (Anomaly)", "circle"),
    ]:
        if subset.empty:
            continue
        fig.add_trace(go.Scatter(
            x=subset["Revenue_Growth"],
            y=subset["Profit_Margin"],
            mode="markers+text",
            name=name,
            marker=dict(
                color=color,
                size=10,
                opacity=0.85,
                symbol=symbol,
                line=dict(width=0),
            ),
            text=subset["Symbol"],
            textposition="top center",
            textfont=dict(family="Share Tech Mono", size=9, color=color),
            hovertemplate="%{customdata}<extra></extra>",
            customdata=make_hover(subset),
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0d1018",
        font=dict(family="Share Tech Mono", color="#5a7090"),
        height=340,
        margin=dict(l=50, r=20, t=10, b=50),
        xaxis=dict(
            title=dict(text="REVENUE GROWTH (%)", font=dict(size=9, color="#3d5575")),
            gridcolor="#1a2235", gridwidth=1,
            zeroline=False, tickfont=dict(size=9, color="#3d5575"),
            linecolor="#1e2535",
        ),
        yaxis=dict(
            title=dict(text="PROFIT MARGIN (%)", font=dict(size=9, color="#3d5575")),
            gridcolor="#1a2235", gridwidth=1,
            zeroline=False, tickfont=dict(size=9, color="#3d5575"),
            linecolor="#1e2535",
        ),
        legend=dict(
            font=dict(family="Share Tech Mono", size=9, color="#5a7090"),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="#1e2535",
            borderwidth=1,
            x=0.01, y=0.01,
        ),
        hoverlabel=dict(
            bgcolor="#0d1422",
            bordercolor="#2a3347",
            font=dict(family="Share Tech Mono", size=10, color="#c8d6ef"),
        ),
    )
    st.plotly_chart(fig, use_container_width=True)


with col_queue:
    panel_header("Risk Queue", "ISO-FOREST")

    sorted_df = filtered.sort_values("Anomaly_Score", ascending=False)

    for _, row in sorted_df.iterrows():
        is_high = row["Risk_Level"] == "High Risk (Anomaly)"
        col_a, col_b, col_c = st.columns([2, 2.5, 1.5])
        with col_a:
            st.markdown(
                mono(row["Symbol"], "#c8d6ef", size=11, spacing=1),
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown(badge("ANOMALY" if is_high else "CLEAR", is_high),
                        unsafe_allow_html=True)
        with col_c:
            score_color = "#ff3d71" if is_high else "#00d68f"
            st.markdown(
                mono(f"{row['Anomaly_Score']:.2f}", score_color, size=10),
                unsafe_allow_html=True,
            )
        st.markdown(
            "<hr style='border:none;border-top:1px solid #1e2535;margin:4px 0'>",
            unsafe_allow_html=True,
        )


# ── DEEP AUDIT PANEL ─────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
st.markdown(
    f"<div style='border:1px solid #1e2535;background:#10141c;padding:0'>",
    unsafe_allow_html=True,
)

panel_header("Deep Audit Report", "SELECT A COMPANY")

selected_symbol = st.selectbox(
    "Select a company to audit",
    options=df["Symbol"].unique().tolist(),
    label_visibility="collapsed",
)

row = df[df["Symbol"] == selected_symbol].iloc[0]
is_high = row["Risk_Level"] == "High Risk (Anomaly)"
risk_pct = 0.85 if is_high else 0.15
bar_color = "#ff3d71" if is_high else "#00d68f"
status_text = "HIGH RISK · ISOLATION FOREST ANOMALY DETECTED" if is_high else "LOW RISK · WITHIN NORMAL PARAMETERS"

# Detail header row
dh1, dh2 = st.columns([3, 2])
with dh1:
    st.markdown(
        f"<div style=\"font-family:'{MONO}',monospace;font-size:22px;"
        f"color:#c8d6ef;letter-spacing:3px\">{selected_symbol}</div>"
        f"<div style=\"font-family:'{MONO}',monospace;font-size:10px;"
        f"color:#5a7090;margin-top:4px;letter-spacing:1px\">{status_text}</div>",
        unsafe_allow_html=True,
    )
with dh2:
    st.markdown(
        f"<div style='text-align:right'>"
        f"<div style=\"font-family:'{MONO}',monospace;font-size:9px;"
        f"color:#5a7090;letter-spacing:2px;margin-bottom:6px\">RISK PROBABILITY</div>"
        f"<div style='width:100%;height:6px;background:#2d3f58;position:relative'>"
        f"  <div style='width:{int(risk_pct*100)}%;height:100%;background:{bar_color}'></div>"
        f"</div>"
        f"<div style=\"font-family:'{MONO}',monospace;font-size:10px;"
        f"color:#5a7090;margin-top:4px\">{int(risk_pct*100)}% internal risk score</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)

# Stat cells
s1, s2, s3, s4 = st.columns(4)

def stat_cell(col, label: str, value: str, value_color: str = "#c8d6ef") -> None:
    col.markdown(
        f"<div style='border:1px solid #1e2535;padding:10px 12px;background:#0a0d12'>"
        f"<div style=\"font-family:'{MONO}',monospace;font-size:8px;"
        f"color:#5a7090;letter-spacing:2px;text-transform:uppercase;margin-bottom:5px\">{label}</div>"
        f"<div style=\"font-family:'{MONO}',monospace;font-size:15px;color:{value_color}\">{value}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

rev_g  = row["Revenue_Growth"]
pm     = row["Profit_Margin"]
ascore = row["Anomaly_Score"]
de     = row["Debt_Equity"]

stat_cell(s1, "Revenue Growth",
          f"{rev_g}%",
          "#ff3d71" if rev_g < 0 else "#00d68f")

stat_cell(s2, "Profit Margin",
          f"{pm}%",
          "#ff3d71" if pm < 0 else "#c8d6ef")

stat_cell(s3, "Anomaly Score",
          f"{ascore:.2f}",
          "#ff3d71" if is_high else "#00d68f")

stat_cell(s4, "Debt / Equity",
          f"{de:.2f}x",
          "#ffaa00" if de > 2 else "#c8d6ef")

st.markdown("</div>", unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("<div style='margin-top:32px'></div>", unsafe_allow_html=True)
st.markdown(
    f"<div style='border-top:1px solid #1e2535;padding-top:12px;"
    f"display:flex;justify-content:space-between;align-items:center'>"
    f"<span style=\"font-family:'{MONO}',monospace;font-size:9px;"
    f"color:#2d3f58;letter-spacing:2px\">FORENSIC FINANCE · ISOLATION FOREST v2.1</span>"
    f"<span style=\"font-family:'{MONO}',monospace;font-size:9px;"
    f"color:#2d3f58;letter-spacing:2px\">TRANSPARENTLY.AI / ENDOWUS · {now_utc}</span>"
    f"</div>",
    unsafe_allow_html=True,
)
