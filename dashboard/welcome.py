import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from utils.auth import login, is_authenticated, logout
from dashboard.config_pane import show_config_pane

st.set_page_config(page_title="RASP Security Suite", layout="wide")

if not is_authenticated():
    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🔐 RASP Security Suite</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2em; color: #666;'>Runtime Application Self-Protection with Behavior Drift Detection</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Sign In to Continue")
        username = st.text_input("Email", placeholder="admin@rasp.local")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        
        if st.button("Sign In", type="primary", use_container_width=True):
            if login(username, password):
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Try: admin@rasp.local / secure123")
else:
    show_config_pane()
