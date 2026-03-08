import streamlit as st
import pandas as pd
from storage.db import SessionLocal
from storage.models import RuntimeEvent

def show_export():
    st.subheader("📥 Export Security Logs")
    db = SessionLocal()
    try:
        events = db.query(RuntimeEvent).order_by(RuntimeEvent.timestamp.desc()).all()
    finally:
        db.close()

    if not events:
        st.warning("No logs to export.")
        return

    df = pd.DataFrame([{
        "timestamp": e.timestamp,
        "ip_hash": e.ip_hash,
        "endpoint": e.endpoint,
        "risk_level": e.risk_level,
        "attack_type": e.attack_type,
        "drift_score": e.drift_score,
        "confidence": e.attack_confidence,
        "evidence": e.attack_evidence
    } for e in events])

    col1, col2 = st.columns(2)
    with col1:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download CSV", data=csv, file_name="rasp_security_events.csv", mime="text/csv")
    with col2:
        json_data = df.to_json(orient='records')
        st.download_button("📦 Download JSON", data=json_data, file_name="rasp_security_events.json", mime="application/json")
