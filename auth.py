"""Authentication module for user login/registration."""

import streamlit as st
from database import HealthDatabase


def show_login_page():
    """Display login/registration page."""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🏥 AI Health Companion</h1>
        <p style="color: #666;">Your personal health assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    db = HealthDatabase()
    
    with tab1:
        st.subheader("Login to Your Account")
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary", use_container_width=True):
            if username and password:
                user_id = db.authenticate_user(username, password)
                if user_id:
                    st.session_state.authenticated = True
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter username and password")
    
    with tab2:
        st.subheader("Create New Account")
        
        new_username = st.text_input("Username", key="reg_username")
        new_email = st.text_input("Email (optional)", key="reg_email")
        new_password = st.text_input("Password", type="password", key="reg_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
        
        if st.button("Register", type="primary", use_container_width=True):
            if new_username and new_password:
                if new_password == confirm_password:
                    if db.register_user(new_username, new_password, new_email):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Username already exists")
                else:
                    st.error("Passwords don't match")
            else:
                st.warning("Please fill in all required fields")


def check_authentication():
    """Check if user is authenticated."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    return st.session_state.authenticated


def logout():
    """Logout current user."""
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.messages = []
    st.rerun()
