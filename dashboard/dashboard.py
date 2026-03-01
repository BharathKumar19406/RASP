# dashboard/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px
from storage.db import SessionLocal, RuntimeEvent
from datetime import datetime

def show_dashboard():
    st.subheader("🚨 Recent Security Events")

    db = SessionLocal()
    try:
        events = db.query(RuntimeEvent).order_by(RuntimeEvent.timestamp.desc()).limit(20).all()
    finally:
        db.close()

    if not events:
        st.info("No security events yet. Send requests to /api/login or /api/transfer to generate data.")
        return

    # ✅ Build DataFrame with exact column names
    df = pd.DataFrame([{
        "Time": e.timestamp.strftime("%H:%M:%S"),
        "IP": e.ip_hash[:8],
        "Endpoint": e.endpoint,
        "Method": e.method,
        "Drift": round(e.drift_score, 1),
        "Risk": e.risk_level,
        "Attack": e.attack_type,
        "Confidence": f"{e.attack_confidence:.0%}"
    } for e in events])

    # ✅ Apply attack type filter from session state
    selected_type = st.session_state.get("selected_attack_type", "All")
    if selected_type != "All":
        df = df[df["Attack"] == selected_type]

    # Risk Distribution Chart
    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.histogram(
            df,
            x="Risk",
            color="Risk",
            category_orders={"Risk": ["LOW", "MEDIUM", "HIGH"]},
            color_discrete_map={"LOW": "#2E8B57", "MEDIUM": "#FFA500", "HIGH": "#DC143C"}
        )
        st.plotly_chart(fig1, width='stretch')

    with col2:
        # Only show pie chart if non-Behavioral attacks exist
        non_behavioral = df[df["Attack"] != "Behavioral Anomaly"]
        if not non_behavioral.empty:
            fig2 = px.pie(non_behavioral, names='Attack', title="Attack Types")
            st.plotly_chart(fig2, width='stretch')
        else:
            st.info("No classified attacks yet.")

    # Event Table
    st.dataframe(df, width='stretch')
