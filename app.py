import streamlit as st
import os
import pandas as pd
import json
import base64
from datetime import datetime
import re
from io import BytesIO
from extract_tenant_data import flatten_extracted_data, parse_gpt_output, process_pdf, extract_images_from_pdf, call_gpt_vision_api
from extract_utils import detect_form_type, extract_text_from_first_page, extract_data_by_form_type,extract_handwritten_form
from write_to_excel_template import write_multiple_applicants_to_template, write_flattened_to_template, write_to_summary_template
from write_template_holder import write_to_template_holder
from email.message import EmailMessage
from email_ui import render_email_ui
import smtplib

# --- Page Config MUST be first ---
st.set_page_config(page_title="Tenant App Dashboard", layout="wide")

# Ensure temp directory exists
os.makedirs("temp", exist_ok=True)

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
SUMMARY_TEMPLATE_PATH ="templates/App_Summary_Template.xlsx"

st.sidebar.title("Navigation")
st.title(" Tenant Application Assistant")
st.markdown("This tool extracts and validates tenant application data.")

# Template selection
template_type = st.sidebar.selectbox(
    "Select number of applicants:",
    ["1–2 Applicants", "3+ Applicants"],
    key="template_type_selector"
)

# Load existing holder
df_holder = pd.DataFrame()
if os.path.exists(EXTRACTED_DATA_PATH):
    df_holder = pd.read_excel(EXTRACTED_DATA_PATH)
    st.sidebar.markdown(f"\U0001F4C4 File loaded. Rows: **{len(df_holder)}**")
    selected_indices = st.sidebar.multiselect(
        "Select applicant(s) to write to tenant template:",
        options=df_holder.index,
        format_func=lambda i: f"{df_holder.at[i, 'FullName']} - {df_holder.at[i, 'Property Address']}",
        key="applicant_selector"
    )

# --- Save to Tenant Template ---
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
                # ✅ Write to Tenant Template (final)
                if template_type == "1–2 Applicants":
                    flat_data = selected_df.iloc[0].to_dict()
                    output_bytes, download_filename = write_flattened_to_template(flat_data, template_to_use)
                else:
                    output_bytes, download_filename = write_multiple_applicants_to_template(selected_df, template_to_use)

                st.session_state["final_output_bytes"] = output_bytes
                st.session_state["final_filename"] = download_filename

                # ✅ Ensure directory exists for summary
                os.makedirs(os.path.dirname(SUMMARY_TEMPLATE_PATH), exist_ok=True)

                # ✅ Write Summary Template directly
                first_applicant = selected_df.iloc[0].to_dict()
                write_to_summary_template(
                    flat_data=first_applicant,
                    output_path=SUMMARY_TEMPLATE_PATH,
                    summary_template_path=SUMMARY_TEMPLATE_PATH
                )

                # ✅ Load summary as BytesIO for consistent handling
                with open(SUMMARY_TEMPLATE_PATH, "rb") as f:
                    summary_bytes = BytesIO(f.read())

                # ✅ Filename
                address = str(first_applicant.get("Property Address", "tenant")).strip()
                address_clean = "_".join(re.sub(r"[^\w\s]", "", address).split()[:3]) or "tenant"
                date_str = datetime.now().strftime("%Y%m%d")
                summary_filename = f"{address_clean}_{date_str}_summary.xlsx".lower()

                # ✅ Store to session
                st.session_state["summary_output_bytes"] = summary_bytes
                st.session_state["summary_filename"] = summary_filename
                st.session_state["trigger_validation"] = True

            except Exception as e:
                st.sidebar.error(f"\u274C Failed to write to tenant template: {e}")


# ✅ Final Tenant Template Download Button
if (
    "final_output_bytes" in st.session_state 
    and isinstance(st.session_state["final_output_bytes"], BytesIO)
    and "final_filename" in st.session_state
):
    st.sidebar.download_button(
        label="⬇️ Download Final Tenant Template",
        data=st.session_state["final_output_bytes"].getvalue(),
        file_name=st.session_state["final_filename"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ✅ Summary Template Download Button
if (
    "summary_output_bytes" in st.session_state 
    and isinstance(st.session_state["summary_output_bytes"], BytesIO)
    and "summary_filename" in st.session_state
):
    st.sidebar.download_button(
        label="⬇️ Download Summary Template",
        data=st.session_state["summary_output_bytes"].getvalue(),
        file_name=st.session_state["summary_filename"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# === Upload PDF Files ===
uploaded_pdfs = st.file_uploader(
    "Upload Tenant Application PDFs",
    type=["pdf"],
    accept_multiple_files=True,
    key="tenant_pdf_uploader"
)

# --- Extraction and Save All Logic ---
if "batch_extracted" not in st.session_state:
    st.session_state.batch_extracted = {}
if "saved_applicants" not in st.session_state:
    st.session_state.saved_applicants = []

if uploaded_pdfs:
    if st.button("Extract Data"):
        for uploaded_file in uploaded_pdfs:
            filename = uploaded_file.name
            temp_path = os.path.join("temp", filename)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.read())
           
            # === Form recognition + extraction routing ===
            images = extract_images_from_pdf(temp_path)
            text = extract_text_from_first_page(temp_path)
            ocr_used = len(text.strip()) < 50
            form_type = detect_form_type(text, ocr_used=ocr_used)

            if form_type in ["standard_form", "Form_A_2022", "Form_B_2024"]:
                extracted_data = extract_standard_form(images)
            elif form_type == "handwritten_form":
                extracted_data = extract_handwritten_form(images)
            else:
                st.warning(f"{filename}: Unknown or unsupported form type.")
                continue

            if "error" in extracted_data:
                st.warning(f"{filename}: {extracted_data['error']}")
                continue

            st.session_state.batch_extracted[filename] = extracted_data

        st.success("✅ All applications extracted.")

    if st.button("Save Extracted Data"):
        saved_records = []
        for filename, data in st.session_state.batch_extracted.items():
            try:
                parsed = parse_gpt_output(data)
                flat = flatten_extracted_data(parsed)
                saved_records.append(flat)
            except Exception as e:
                st.warning(f"{filename}: Failed to parse – {e}")

        if saved_records:
            df = pd.DataFrame(saved_records)
            df.to_excel(EXTRACTED_DATA_PATH, index=False)
            st.success("✅ All extracted records saved.")
            st.session_state.trigger_validation = True


# === Validation and Email Notification ===
def is_missing(value):
    try:
        if pd.isna(value):
            return True
        return str(value).strip().lower() in {"", "n/a", "-", "none", "null", "nan"}
    except Exception:
        return True

if st.session_state.get("trigger_validation", False) and not st.session_state.get("email_validation_done", False):
    st.caption("Validating Missing Info + Sending Emails...")

    any_missing = False
    all_missing_summary = []
    df_check = pd.read_excel(EXTRACTED_DATA_PATH)

    for idx, row in df_check.iterrows():
        email = str(row.get("Email", "") or "").strip()
        full_name = str(row.get("FullName", "") or "Applicant").strip()
        missing_fields = []

        required_fields = {
            "Full Name": row.get("FullName", ""),
            "Phone Number": row.get("PhoneNumber", ""),
            "SSN": row.get("SSN", ""),
            "DOB": row.get("DOB", ""),
            "Current Employer": row.get("Applicant's Current Employer", ""),
        }

        for field_name, value in required_fields.items():
            if is_missing(value):
                missing_fields.append(field_name)

        if missing_fields:
            any_missing = True
            key_suffix = f"{idx}_{email.replace('@', '_').replace('.', '_') if email else f'no_email_{idx}'}"

            result = render_email_ui(
                email=email,
                missing_fields=missing_fields,
                full_name=full_name,
                key_suffix=key_suffix,
                email_user=EMAIL_USER,
                email_pass=EMAIL_PASS
            )

            if isinstance(result, tuple) and len(result) == 2:
                updated_full_name, updated_email = result
            else:
                updated_full_name, updated_email = full_name, email       

    if not any_missing:
        st.success("✅ All applicants have complete required fields.")
        st.session_state["trigger_validation"] = False
    else:
        st.info("\n".join(all_missing_summary))
