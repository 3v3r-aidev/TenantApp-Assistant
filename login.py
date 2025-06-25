import streamlit as st

# Fetch credentials from Streamlit secrets only
USERNAME = st.secrets["app"]["username"]
PASSWORD = st.secrets["app"]["password"]


# Authenticator (no hashing)
def login_user(username, password):
    return username == USERNAME and password == PASSWORD

# Login UI
def login_ui():
    st.title("Tenant Application Assistant")
    st.subheader("🔐 User Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        if login_user(username, password):
            st.session_state["logged_in"] = True
            st.session_state["user"] = username
            st.success(f"✅ Welcome, {username}!")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid username or password")

# Logout UI
def logout_ui():
    if st.button("🚪 Logout"):
        st.session_state.clear()
        st.success("You have been logged out.")
        st.experimental_rerun()

# Ensure session keys exist
def initialize_session():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    if "user" not in st.session_state:
        st.session_state["user"] = ""
