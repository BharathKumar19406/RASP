import streamlit as st
from utils.auth import login_form

st.set_page_config(page_title="RASP Security Suite", layout="wide")
st.title("🔐 Welcome Back")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_form()
else:
    st.success(f"✅ Logged in as {st.session_state.user}")
    st.markdown("### 🚀 Get Started")
    st.page_link("dashboard/config_pane.py", label="→ Go to Configuration Pane", icon="⚙️")
