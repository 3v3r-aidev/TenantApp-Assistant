import streamlit as st
import os
import pandas as pd
import json
import base64
from datetime import datetime
import re
from login import login_ui, logout_ui
from extract_tenant_data import process_pdf
from extract_tenant_data import flatten_extracted_data, parse_gpt_output
from write_template_holder import append_to_template_holder, write_multiple_applicants_to_template

# --- Page Config MUST be first ---
st.set_page_config(page_title="Tenant App Dashboard", layout="wide")

# Function to enconde to base64 the app logo
def get_base64_image(path):
    with open(path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Encode local image
img_base64 = get_base64_image("assets/medical-history.png")

# Inject fixed-position app logo with caption below
st.markdown(f"""
    <style>
        .evercrest-logo {{
            position: fixed;
            top: 16px;
            right: 16px;
            text-align: center;
            z-index: 999;
        }}

        .evercrest-logo img {{
            width: 100px;
            height: 100px;
            display: block;
            margin: 0 auto;
        }}

        .evercrest-logo span {{
            display: block;
            font-size: 8px;
            color: #373535;
            margin-top: 2px;
        }}
    </style>

    <div class="evercrest-logo">
        <img src="data:image/png;base64,{img_base64}" />
        <span>Icon by Iconic Panda</span>
    </div>
""", unsafe_allow_html=True)

def generate_filename_from_address(address: str) -> str:
    """Return '<first_two_words>_<yyyymmdd>_app.xlsx'."""
    cleaned = re.sub(r'[^\w\s]', '', str(address))      # remove punctuation
    words = cleaned.strip().split()
    first_two = "_".join(words[:2]) if len(words) >= 2 else "_".join(words)
    date_str = datetime.now().strftime("%Y%m%d")
    return f"{first_two}_{date_str}_app.xlsx".lower()

# Load credentials 
USERNAME = st.secrets["app"]["username"]
PASSWORD = st.secrets["app"]["password"]


# --- Login Logic ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("Login"):
        st.subheader("🔐 TenantApp Assistant Login")
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button:
            if username_input == USERNAME and password_input == PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
    st.stop()
else:
    st.sidebar.success(f"🔓 Logged in as {USERNAME}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- Main App Logic ---
EXTRACTED_DATA_PATH = "templates/Template_Data_Holder.xlsx"

st.sidebar.title("Navigation")
st.title(" Tenant Application Assistant")
st.markdown("This tool extracts, previews, edits, and validates tenant application data.")

# Template paths
SINGLE_TEMPLATE_PATH = "templates/Tenant_Template.xlsx"
MULTIPLE_TEMPLATE_PATH = "templates/Tenant_Template_Multiple.xlsx"

# 1. Select template type
template_type = st.sidebar.selectbox(
    "Select number of applicants:",
    ["1–2 Applicants", "3+ Applicants"],
    key="template_type_selector"
)

# 2. File check and sidebar UI
if not os.path.exists(EXTRACTED_DATA_PATH):
    st.sidebar.warning("⚠️ Data holder file is missing. Please extract and save at least one application to initialize.")
else:
    # File exists — read it now
    df_holder = pd.read_excel(EXTRACTED_DATA_PATH)

    # Optional: show info
    st.sidebar.markdown(f"📄 File loaded. Rows: **{len(df_holder)}**")

    selected_indices = st.sidebar.multiselect(
        "Select applicant(s) to write to tenant template:",
        options=df_holder.index,
        format_func=lambda i: f"{df_holder.at[i, 'FullName']} - {df_holder.at[i, 'Property Address']}",
        key="applicant_selector"
    )

    # 3. Save to tenant template
    if st.sidebar.button("Save to Tenant Template", key="save_to_template"):
        selected_df = df_holder.loc[selected_indices] if selected_indices else pd.DataFrame()

        if selected_df.empty:
            st.sidebar.warning("Please select at least one applicant.")
        else:
            # Choose template path
            template_to_use = SINGLE_TEMPLATE_PATH if template_type == "1–2 Applicants" else MULTIPLE_TEMPLATE_PATH

            if not os.path.exists(template_to_use):
                st.sidebar.warning(f"{template_to_use} not found.")
            else:
                try:
                    # Generate output in memory and dynamic file name
                    output_bytes, download_filename = write_multiple_applicants_to_template(selected_df, template_to_use)

                    # Display download button in sidebar
                    st.sidebar.download_button(
                        label="⬇️ Download Final Tenant Template",
                        data=output_bytes,
                        file_name=download_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.sidebar.error(f"❌ Failed to write to tenant template: {e}")

# PDF Upload section
uploaded_pdfs = st.file_uploader("Upload Tenant Application PDFs", type=["pdf"], accept_multiple_files=True)
if uploaded_pdfs:
    for uploaded_file in uploaded_pdfs:
        filename = uploaded_file.name
        key_prefix = filename.replace(".", "_").replace(" ", "_")

        with st.expander(f"{filename}"):
            # Save uploaded file temporarily for processing
            pdf_temp_path = os.path.join("temp", filename)
            os.makedirs("temp", exist_ok=True)
            with open(pdf_temp_path, "wb") as f:
                f.write(uploaded_file.read())

            # Handle extract button
            if st.button(f"Extract: {filename}", key=f"extract_{key_prefix}"):
                with st.spinner("Extracting data from application..."):
                    extracted, _ = process_pdf(pdf_temp_path)
                    st.session_state[f"form_data_{key_prefix}"] = extracted

            # Check if extracted data exists
            if f"form_data_{key_prefix}" in st.session_state:
                form_data = st.session_state[f"form_data_{key_prefix}"]

                st.subheader("Data extracted.")

                # Save to Template_Holder.xlsx
                if st.button(f"Save {filename} to Excel", key=f"save_{key_prefix}"):
                    try:
                        parsed_data = parse_gpt_output(form_data)
                        flat_data = flatten_extracted_data(parsed_data)
                        df_holder = pd.concat([df_holder, pd.DataFrame([flat_data])], ignore_index=True)
                        df_holder.to_excel(EXTRACTED_DATA_PATH, index=False)
                        st.session_state[f"flattened_data_{key_prefix}"] = flat_data
                        st.success("✅ Saved to Template_Holder.xlsx")
                    except Exception as e:
                        st.error(f"❌ Failed to parse and save data: {e}")

# Sidebar Footer
st.sidebar.markdown("""
    <div style="
        margin-top: 192px;
        line-height: 1.2;
        text-align: center;
    ">
        <p style="font-size: 0.75rem; margin: 0; color: #F5F7FA;">
            © 2025 TenantApp Assistant — Evercrest Homes
        </p>
        <p style="font-size: 0.70rem; margin: 0; color: #F5F7FA;">
            Powered by OpenAI | Developed by R.B. Urbis
        </p>
    </div>
""", unsafe_allow_html=True)




            
