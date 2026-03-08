import streamlit as st
from dashboard.settings import show_settings
from dashboard.dashboard import show_dashboard
from dashboard.export_logs import show_export

def show_config_pane():
    st.title("⚙️ Configuration Pane")
    tab1, tab2, tab3 = st.tabs(["Settings", "Dashboard", "Export Logs"])
    with tab1: show_settings()
    with tab2: show_dashboard()
    with tab3: show_export()
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        from utils.auth import logout
        logout()
