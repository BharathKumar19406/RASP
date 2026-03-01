import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/..")
import streamlit as st
from dashboard.settings import show_settings
from dashboard.dashboard import show_dashboard
from dashboard.export_logs import show_export

st.set_page_config(page_title="Configuration Pane", layout="wide")
st.title("⚙️ Configuration Pane")

tab1, tab2, tab3 = st.tabs(["Settings", "Dashboard", "Export Logs"])

with tab1:
    show_settings()

with tab2:
    show_dashboard()

with tab3:
    show_export()
