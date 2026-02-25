import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
from config.settings import settings
import yaml

st.set_page_config(page_title="RASP Security Dashboard", layout="wide")
st.title("🛡️ RASP Security Dashboard")

# Load events
try:
    conn = psycopg2.connect(settings.DB_URL)
    df = pd.read_sql("""
        SELECT timestamp, ip, endpoint, method, drift_score, risk_level, attack_type
        FROM runtime_events
        ORDER BY timestamp DESC
    """, conn)
    conn.close()
except Exception as e:
    st.error(f"DB Error: {e}")
    df = pd.DataFrame()

# --- CHARTS ---
if not df.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Risk Level Distribution")
        fig1 = px.histogram(df, x="risk_level", color="risk_level",
                           category_orders={"risk_level": ["LOW", "MEDIUM", "HIGH"]},
                           color_discrete_map={"LOW": "#2E8B57", "MEDIUM": "#FFA500", "HIGH": "#DC143C"})
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("Attack Types")
        fig2 = px.pie(df[df['attack_type'] != 'Normal'], names='attack_type')
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Drift Score Over Time")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    fig3 = px.line(df.sort_values('timestamp'), x='timestamp', y='drift_score', color='risk_level',
                   color_discrete_map={"LOW": "#2E8B57", "MEDIUM": "#FFA500", "HIGH": "#DC143C"})
    st.plotly_chart(fig3, use_container_width=True)

# --- EVENT LIST ---
st.subheader("🔴 Recent Security Events")
if not df.empty:
    for _, row in df.head(20).iterrows():
        color = {"LOW": "#2E8B57", "MEDIUM": "#FFA500", "HIGH": "#DC143C"}.get(row["risk_level"], "gray")
        st.markdown(
            f"<div style='border-left: 4px solid {color}; padding-left: 10px; margin: 8px 0;'>"
            f"<b>{row['timestamp'].strftime('%H:%M:%S')}</b> | {row['ip']} | "
            f"<code>{row['method']} {row['endpoint']}</code> | "
            f"Drift: {row['drift_score']:.1f} | "
            f"Risk: <span style='color:{color}'>{row['risk_level']}</span> | "
            f"Attack: <b>{row['attack_type']}</b>"
            f"</div>",
            unsafe_allow_html=True
        )
else:
    st.info("No events yet. Send some requests to /api/login or /api/transfer!")

# --- CONFIGURATION ---
st.subheader("⚙️ Configure Thresholds")
with open("config/thresholds.yaml") as f:
    cfg = yaml.safe_load(f)

new_medium = st.slider("Medium Risk Threshold", 0, 100, int(cfg["drift"]["medium"]))
new_high = st.slider("High Risk Threshold", 0, 100, int(cfg["drift"]["high"]))

if st.button("💾 Save Configuration"):
    with open("config/thresholds.yaml", "w") as f:
        yaml.dump({"drift": {"medium": new_medium, "high": new_high}}, f)
    st.success("Configuration updated!")
