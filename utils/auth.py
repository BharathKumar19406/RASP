import streamlit as st
import hashlib

USERS = {
    "admin@rasp.local": {"password_hash": hashlib.sha256("secure123".encode()).hexdigest(), "role": "Admin"},
}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def login(username: str, password: str) -> bool:
    user = USERS.get(username)
    if user and user["password_hash"] == hash_password(password):
        st.session_state.logged_in = True
        st.session_state.user = username
        st.session_state.role = user["role"]
        return True
    return False

def logout():
    st.session_state.clear()
    st.rerun()

def is_authenticated():
    return st.session_state.get("logged_in", False)
