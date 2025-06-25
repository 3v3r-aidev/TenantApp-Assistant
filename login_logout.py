import streamlit as st
import hashlib
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fetch credentials from .env
USERNAME = os.getenv("APP_USERNAME")
PASSWORD_HASH = os.getenv("APP_PASSWORD_HASH")

# Helper to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Authenticator
def login_user(username, password):
    return username == USERNAME and hash_password(password) == PASSWORD_HASH

# Streamlit Login UI
def login_ui():
    st.title("Tenant Application Portal")
    st.subheader("🔐 User Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if login_user(username, password):
            st.success(f"Welcome, {username}!")
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
        else:
            st.error("❌ Invalid username or password")

# Logout button UI
def logout_ui():
    if st.button("🚪 Logout"):
        st.session_state["logged_in"] = False
        st.session_state["user"] = ""
        st.success("You have been logged out.")
        st.experimental_rerun()

# Check session
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Show login if not logged in
if not st.session_state["logged_in"]:
    login_ui()
else:
    st.success("✅ You are logged in.")
    st.write("You can now proceed to upload and process tenant applications.")
    logout_ui()
