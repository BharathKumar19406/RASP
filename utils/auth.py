import streamlit as st
import jwt
import time

def login_form():
    st.markdown("### 🔐 Sign In")
    username = st.text_input("Email", value="admin@rasp.local")
    password = st.text_input("Password", type="password", value="secure123")
    if st.button("Sign In"):
        if username == "admin@rasp.local" and password == "secure123":
            st.session_state.logged_in = True
            st.session_state.user = "Admin"
            st.rerun()
        else:
            st.error("Invalid credentials")

def get_current_user():
    return st.session_state.get("user", "Guest")
