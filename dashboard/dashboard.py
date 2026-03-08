import streamlit as st
import pandas as pd
import plotly.express as px
from storage.db import SessionLocal
from storage.models import RuntimeEvent

def show_dashboard():
    st.subheader("🚨 Recent Security Events")
    db = SessionLocal()
    try:
        events = db.query(RuntimeEvent).order_by(RuntimeEvent.timestamp.desc()).limit(20).all()
    finally:
        db.close()

    if not events:
        st.info("No security events yet.")
        return

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

    selected = st.session_state.get("selected_attack_type", "All")
    if selected != "All":
        df = df[df["Attack"] == selected]

    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.histogram(df, x="Risk", color="Risk",
                            category_orders={"Risk": ["LOW", "MEDIUM", "HIGH"]},
                            color_discrete_map={"LOW": "#2E8B57", "MEDIUM": "#FFA500", "HIGH": "#DC143C"})
        st.plotly_chart(fig1, width='stretch')
    with col2:
        non_behavioral = df[df["Attack"] != "Behavioral Anomaly"]
        if not non_behavioral.empty:
            fig2 = px.pie(non_behavioral, names='Attack')
            st.plotly_chart(fig2, width='stretch')

    st.dataframe(df, width='stretch')
