import streamlit as st
import yaml
from config.settings import settings
from storage.db import SessionLocal
from storage.models import RuntimeEvent

def get_unique_attack_types():
    db = SessionLocal()
    try:
        types = db.query(RuntimeEvent.attack_type).distinct().all()
        return sorted({t[0] for t in types if t[0]})
    finally:
        db.close()

def show_settings():
    st.subheader("🔧 System Settings")
    safe_mode = st.toggle("Safe Mode", value=settings.SAFE_MODE)
    if safe_mode != settings.SAFE_MODE:
        with open(".env", "r") as f:
            lines = f.readlines()
        with open(".env", "w") as f:
            for line in lines:
                if line.startswith("SAFE_MODE="):
                    f.write(f"SAFE_MODE={'true' if safe_mode else 'false'}\n")
                else:
                    f.write(line)
        st.success("✅ Safe Mode updated. Restart app to apply.")

    st.subheader("🔍 Attack Type Filtering")
    attack_types = ["All"] + get_unique_attack_types()
    selected = st.selectbox("Filter events by attack type", attack_types)
    st.session_state.selected_attack_type = selected
