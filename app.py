import streamlit as st
import os
import pandas as pd
import json
import base64
from datetime import datetime
import re
from extract_tenant_data import flatten_extracted_data, parse_gpt_output, process_pdf
from write_to_excel_template import write_multiple_applicants_to_template
from write_template_holder import write_to_template_holder
from email.message import EmailMessage
from email_ui import render_email_ui
import smtplib

# --- Page Config MUST be first ---
st.set_page_config(page_title="Tenant App Dashboard", layout="wide")

# Function to encode to base64 the app logo
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
    try:
        cleaned = re.sub(r'[^\w\s]', '', str(address))
        words = cleaned.strip().split()
        first_two = "_".join(words[:2]) if len(words) >= 2 else "_".join(words)
        date_str = datetime.now().strftime("%Y%m%d")
        return f"{first_two}_{date_str}_app.xlsx".lower()
    except Exception:
        return f"unknown_{datetime.now().strftime('%Y%m%d')}_app.xlsx"
        
# --- Credentials ---
USERNAME = st.secrets["app"] ["APP_USERNAME"]
PASSWORD = st.secrets["app"] ["APP_PASSWORD"]
EMAIL_USER = st.secrets["email"]["EMAIL_USER"]
EMAIL_PASS = st.secrets["email"]["EMAIL_PASS"]

# --- Login Logic ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("Login"):
        st.subheader("\U0001F510 TenantApp Assistant Login")
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button:
            if username_input == USERNAME and password_input == PASSWORD:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("\u274C Invalid credentials")
    st.stop()
else:
    st.sidebar.success(f"\U0001F513 Logged in as {USERNAME}")
    if st.sidebar.button("\U0001F6AA Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- Main App Logic ---
EXTRACTED_DATA_PATH = "templates/Template_Data_Holder.xlsx"
SINGLE_TEMPLATE_PATH = "templates/Tenant_Template.xlsx"
MULTIPLE_TEMPLATE_PATH = "templates/Tenant_Template_Multiple.xlsx"

st.sidebar.title("Navigation")
st.title(" Tenant Application Assistant")
st.markdown("This tool extracts and validates tenant application data.")

# Template selection
template_type = st.sidebar.selectbox(
    "Select number of applicants:",
    ["1–2 Applicants", "3+ Applicants"],
    key="template_type_selector"
)

if not os.path.exists(EXTRACTED_DATA_PATH):
    st.sidebar.warning("\u26A0\uFE0F Data holder file is missing. Please extract and save at least one application to initialize.")
else:
    df_holder = pd.read_excel(EXTRACTED_DATA_PATH)
    st.sidebar.markdown(f"\U0001F4C4 File loaded. Rows: **{len(df_holder)}**")
    selected_indices = st.sidebar.multiselect(
        "Select applicant(s) to write to tenant template:",
        options=df_holder.index,
        format_func=lambda i: f"{df_holder.at[i, 'FullName']} - {df_holder.at[i, 'Property Address']}",
        key="applicant_selector"
    )

def is_missing(value):
    try:
        if pd.isna(value):
            return True
        return str(value).strip().lower() in {"", "n/a", "-", "none", "null", "nan"}
    except Exception:
        return True

# --- Save to Tenant Template block ---
if st.sidebar.button("Save to Tenant Template", key="save_to_template"):
    selected_df = df_holder.loc[selected_indices] if selected_indices else pd.DataFrame()

    if selected_df.empty:
        st.sidebar.warning("Please select at least one applicant.")
    else:
        template_to_use = SINGLE_TEMPLATE_PATH if template_type == "1–2 Applicants" else MULTIPLE_TEMPLATE_PATH

        if not os.path.exists(template_to_use):
            st.sidebar.warning(f"{template_to_use} not found.")
        else:
            try:
                output_bytes, download_filename = write_multiple_applicants_to_template(selected_df, template_to_use)

                # Save to session for persistent use
                st.session_state["final_output_bytes"] = output_bytes
                st.session_state["final_filename"] = download_filename

                # ✅ Trigger validation separately
                st.session_state["trigger_validation"] = True

            except Exception as e:
                st.sidebar.error(f"\u274C Failed to write to tenant template: {e}")


# ⬇️ Download button *outside* the button block
if "final_output_bytes" in st.session_state and "final_filename" in st.session_state:
    st.sidebar.download_button(
        label="\u2B07\uFE0F Download Final Tenant Template",
        data=st.session_state["final_output_bytes"],
        file_name=st.session_state["final_filename"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
# === upload PDF logic ===
uploaded_pdfs = st.file_uploader(
    "Upload Tenant Application PDFs",
    type=["pdf"],
    accept_multiple_files=True,
    key="tenant_pdf_uploader"
)

# Initialize session state once
if "saved_applicants" not in st.session_state:
    st.session_state["saved_applicants"] = []
if "upload_batch_started" not in st.session_state:
    st.session_state["upload_batch_started"] = False

# Reset flag if no upload
if not uploaded_pdfs:
    st.session_state["upload_batch_started"] = False

# Clear data if it's a new upload batch
if uploaded_pdfs and not st.session_state["upload_batch_started"]:
    # Clear Template_Data_Holder.xlsx
    if os.path.exists(EXTRACTED_DATA_PATH):
        pd.DataFrame().to_excel(EXTRACTED_DATA_PATH, index=False)

    st.session_state["saved_applicants"] = []
    st.session_state["upload_batch_started"] = True

    # Clear related email/form session flags
    for key in list(st.session_state.keys()):
        if key.startswith("email_sent_success_") or key.startswith("form_data_") or key == "email_validation_done":
            del st.session_state[key]

# === Process each uploaded PDF ===
for uploaded_file in uploaded_pdfs:
    filename = uploaded_file.name
    key_prefix = filename.replace(".", "_").replace(" ", "_")

    with st.expander(f"{filename}"):
        pdf_temp_path = os.path.join("temp", filename)
        os.makedirs("temp", exist_ok=True)
        with open(pdf_temp_path, "wb") as f:
            f.write(uploaded_file.read())

        if st.button(f"Extract: {filename}", key=f"extract_{key_prefix}"):
            with st.spinner("Extracting data from application..."):
                extracted, _ = process_pdf(pdf_temp_path)
                st.session_state[f"form_data_{key_prefix}"] = extracted

        if f"form_data_{key_prefix}" in st.session_state:
            form_data = st.session_state[f"form_data_{key_prefix}"]
            st.subheader("Data extracted.")

            if st.button(f"Save {filename} to Excel", key=f"save_{key_prefix}"):
                try:
                    parsed_data = parse_gpt_output(form_data)
                    flat_data = flatten_extracted_data(parsed_data)
                    st.session_state["saved_applicants"].append(flat_data)

                    df = pd.DataFrame(st.session_state["saved_applicants"])
                    df.to_excel(EXTRACTED_DATA_PATH, index=False)

                    st.success("✅ Saved to Template_Holder.xlsx")
                except Exception as e:
                    st.error(f"❌ Failed to parse and save data: {e}")


# === Applicant Info Validation & Email Notification ===
if st.session_state.get("trigger_validation", False) and not st.session_state.get("email_validation_done", False):
    st.caption("Validating Missing Info + Send Email")

    any_missing = False
    df_check = pd.read_excel(EXTRACTED_DATA_PATH)

    for idx, row in df_check.iterrows():
        email = str(row.get("Email", "") or "").strip()
        full_name = str(row.get("FullName", "") or "Applicant").strip()
        missing_fields = []

        required_fields = {
            "Full Name": row.get("FullName", ""),
            "Phone": row.get("Phone", ""),
            "SSN": row.get("SSN", ""),
            "DOB": row.get("DOB", ""),
            
        }

        for field_name, value in required_fields.items():
            if is_missing(value):
                missing_fields.append(field_name)

        if missing_fields:
            any_missing = True
            key_suffix = f"{idx}_{email.replace('@', '_').replace('.', '_') if email else f'no_email_{idx}'}"

            render_email_ui(
                email=email,
                missing_fields=missing_fields,
                full_name=full_name,
                key_suffix=key_suffix,
                email_user=EMAIL_USER,
                email_pass=EMAIL_PASS
            )

    if not any_missing:
        st.success("✅ All applicants have complete required fields.")
        st.session_state["trigger_validation"] = False
    else:
        st.info("📨 Missing info found.")

