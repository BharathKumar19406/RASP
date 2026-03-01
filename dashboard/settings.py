# dashboard/settings.py
import streamlit as st
import yaml
from config.settings import settings
from storage.db import SessionLocal, RuntimeEvent

def get_unique_attack_types():
    """Fetch distinct attack types from DB (excluding 'Behavioral Anomaly' if desired)"""
    db = SessionLocal()
    try:
        types = db.query(RuntimeEvent.attack_type).distinct().all()
        # Return non-empty, unique types
        return sorted({t[0] for t in types if t[0] and t[0] != "Behavioral Anomaly"})
    finally:
        db.close()

def show_settings():
    st.subheader("🔧 System Settings")

    # Safe Mode Toggle
    safe_mode = st.toggle("Safe Mode", value=settings.SAFE_MODE, help="Disable blocking during development")
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

    # Drift Thresholds
    st.subheader("Drift Thresholds")
    try:
        with open("config/thresholds.yaml") as f:
            cfg = yaml.safe_load(f)
        medium_default = cfg.get("drift", {}).get("medium", 15)
        high_default = cfg.get("drift", {}).get("high", 30)
    except Exception:
        medium_default, high_default = 15, 30

    medium = st.slider("Medium Risk Threshold", 0, 100, medium_default, key="medium")
    high = st.slider("High Risk Threshold", 0, 100, high_default, key="high")

    if st.button("💾 Save Thresholds"):
        with open("config/thresholds.yaml", "w") as f:
            yaml.dump({"drift": {"medium": medium, "high": high}}, f)
        st.success("✅ Thresholds saved! Refresh dashboard to see changes.")

    # ✅ Attack Type Filtering — Now Dynamic
    st.subheader("🔍 Attack Type Filtering")
    all_types = ["All"]
    unique_types = get_unique_attack_types()
    if unique_types:
        all_types.extend(unique_types)
    
    # Store selection in session state
    if "selected_attack_type" not in st.session_state:
        st.session_state.selected_attack_type = "All"
    
    selected = st.selectbox(
        "Filter events by attack type",
        options=all_types,
        index=all_types.index(st.session_state.selected_attack_type),
        key="attack_filter"
    )
    st.session_state.selected_attack_type = selected

    st.info(f"Showing: {selected}")
