import streamlit as st
import os
import pandas as pd
import json
import base64
from datetime import datetime
import re
from io import BytesIO
from extract_tenant_data import flatten_extracted_data, parse_gpt_output, process_pdf, extract_images_from_pdf, call_gpt_vision_api, normalize_all_dates, normalize_date_string
from extract_utils import detect_form_type, extract_text_from_first_page, extract_data_by_form_type,extract_handwritten_form, extract_standard_form
from write_to_excel_template import write_multiple_applicants_to_template, write_flattened_to_template, write_to_summary_template
from write_template_holder import write_to_template_holder
from email.message import EmailMessage
from email_ui import render_email_ui
import smtplib

st.set_page_config(page_title="Tenant App Dashboard", layout="wide")
os.makedirs("temp", exist_ok=True)

import streamlit as st

# ── Optional: Other imports
import pandas as pd
from datetime import datetime

# ── Insert CSS to hide toolbar elements
custom_css = """
    <style>
    /* Hide Share, Star, Pencil, and 3-dot Menu */
    .stActionButton {display: none;}
    .viewerBadge_container__1QSob svg[title="Open in Streamlit"] {display: none;}
    .viewerBadge_container__1QSob svg[title="Edit"] {display: none;}
    .viewerBadge_container__1QSob svg[title="Save"] {display: none;}
    .viewerBadge_container__1QSob + div {display: none;}  /* Hides the vertical 3-dots menu */

    /* Keep the Stop/progress icon */
    .viewerBadge_container__1QSob {visibility: visible;}
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

def get_base64_image(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception as e:
        print(f"⚠️ Failed to load logo image: {e}")
        return ""

img_base64 = get_base64_image("assets/medical-history.png")

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

USERNAME = st.secrets["app"].get("APP_USERNAME", "admin")
PASSWORD = st.secrets["app"].get("APP_PASSWORD", "password")
EMAIL_USER = st.secrets["email"].get("EMAIL_USER", "")
EMAIL_PASS = st.secrets["email"].get("EMAIL_PASS", "")

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

EXTRACTED_DATA_PATH = "templates/Template_Data_Holder.xlsx"
SINGLE_TEMPLATE_PATH = "templates/Tenant_Template.xlsx"
MULTIPLE_TEMPLATE_PATH = "templates/Tenant_Template_Multiple.xlsx"
SUMMARY_TEMPLATE_PATH ="templates/App_Summary_Template.xlsx"

st.sidebar.title("Navigation")
st.title(" TenantApp Assistant")
st.markdown("This tool extracts and validates tenant application data.")

template_type = st.sidebar.selectbox("Select number of applicants:", ["1–2 Applicants", "3+ Applicants"], key="template_type_selector")

df_holder = pd.DataFrame()
if os.path.exists(EXTRACTED_DATA_PATH):
    try:
        df_holder = pd.read_excel(EXTRACTED_DATA_PATH)
        st.sidebar.markdown(f"📄 File loaded. Rows: **{len(df_holder)}**")
    except Exception as e:
        st.sidebar.error(f"❌ Failed to load extracted data: {e}")

try:
    selected_indices = st.sidebar.multiselect(
        "Select applicant(s) to write to tenant template:",
        options=df_holder.index,
        format_func=lambda i: f"{df_holder.at[i, 'FullName']} - {df_holder.at[i, 'Property Address']}" if 'FullName' in df_holder.columns and 'Property Address' in df_holder.columns else str(i),
        key="applicant_selector"
    )
except Exception as e:
    st.sidebar.warning(f"⚠️ Error displaying applicant selector: {e}")

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
                if template_type == "1–2 Applicants":
                    if len(selected_df) == 1:
                        flat_data = selected_df.iloc[0].to_dict()
                        output_bytes, download_filename = write_flattened_to_template(flat_data, template_to_use)
                    elif len(selected_df) == 2:
                        output_bytes, download_filename = write_multiple_applicants_to_template(
                            selected_df,
                            template_path=MULTIPLE_TEMPLATE_PATH
                        )
                    else:
                        st.sidebar.warning("Selected more than 2 applicants — please switch to multi-applicant template.")
                        st.stop()
                else:
                    output_bytes, download_filename = write_multiple_applicants_to_template(selected_df, template_path=template_to_use)

                st.session_state["final_output_bytes"] = output_bytes
                st.session_state["final_filename"] = download_filename

                os.makedirs(os.path.dirname(SUMMARY_TEMPLATE_PATH), exist_ok=True)

                first_applicant = selected_df.iloc[0].to_dict()
                write_to_summary_template(
                    flat_data=first_applicant,
                    output_path=SUMMARY_TEMPLATE_PATH,
                    summary_template_path=SUMMARY_TEMPLATE_PATH
                )

                with open(SUMMARY_TEMPLATE_PATH, "rb") as f:
                    summary_bytes = BytesIO(f.read())

                address = str(first_applicant.get("Property Address", "tenant")).strip()
                address_clean = "_".join(re.sub(r"[^\w\s]", "", address).split()[:3]) or "tenant"
                date_str = datetime.now().strftime("%Y%m%d")
                summary_filename = f"{address_clean}_{date_str}_summary.xlsx".lower()

                st.session_state["summary_output_bytes"] = summary_bytes
                st.session_state["summary_filename"] = summary_filename
                st.session_state["trigger_validation"] = True

            except Exception as e:
                st.sidebar.error(f"❌ Failed to write to tenant template: {e}")

if "final_output_bytes" in st.session_state and isinstance(st.session_state["final_output_bytes"], BytesIO) and "final_filename" in st.session_state:
    st.sidebar.download_button(
        label="⬇️ Download Final Tenant Template",
        data=st.session_state["final_output_bytes"].getvalue(),
        file_name=st.session_state["final_filename"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if "summary_output_bytes" in st.session_state and isinstance(st.session_state["summary_output_bytes"], BytesIO) and "summary_filename" in st.session_state:
    st.sidebar.download_button(
        label="⬇️ Download Summary Template",
        data=st.session_state["summary_output_bytes"].getvalue(),
        file_name=st.session_state["summary_filename"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

uploaded_pdfs = st.file_uploader("Upload Tenant Application PDFs", type=["pdf"], accept_multiple_files=True, key="tenant_pdf_uploader")

if "batch_extracted" not in st.session_state:
    st.session_state.batch_extracted = {}
if "saved_applicants" not in st.session_state:
    st.session_state.saved_applicants = []

if uploaded_pdfs:
    if st.button("Extract Data"):
        for uploaded_file in uploaded_pdfs:
            filename = uploaded_file.name
            temp_path = os.path.join("temp", filename)
            try:
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.read())
            except Exception as e:
                st.warning(f"{filename}: Failed to save uploaded file – {e}")
                continue

            try:
                images = extract_images_from_pdf(temp_path)
                text = extract_text_from_first_page(temp_path)
                ocr_used = len(text.strip()) < 50
                form_type = detect_form_type(text, ocr_used=ocr_used)
            except Exception as e:
                st.warning(f"{filename}: Error during form recognition – {e}")
                continue

            try:
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
            except Exception as e:
                st.warning(f"{filename}: Extraction failed – {e}")
                continue

        st.success("✅ All applications extracted.")

    import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import traceback

def render_email_ui(email, missing_fields, full_name="Applicant", key_suffix="", email_user=None, email_pass=None):
    if not email_user or not email_pass:
        st.error("❌ Email credentials missing in secrets.")
        return False

    sent_flag_key = f"email_sent_success_{key_suffix}"
    if st.session_state.get(sent_flag_key):
        st.success(f"✅ Email already sent to {full_name}")
        return True

    with st.expander(f"{full_name} – Missing Fields", expanded=True):
        with st.form(f"form_email_{key_suffix}"):
            default_subject = "Missing Information in Your Application"
            default_body = (
                f"Dear {full_name},\n\n"
                f"We reviewed your rental application and noticed the following missing information:\n\n"
                f"{', '.join(missing_fields)}\n\n"
                f"Please provide the missing details at your earliest convenience.\n\n"
                f"Thank you,\nEvercrest Homes Property Management Team"
            )

            # Editable fields
            applicant_name = st.text_input("Applicant Name", value=full_name, key=f"name_{key_suffix}")
            to_email = st.text_input("Recipient Email", value=email, key=f"email_{key_suffix}")
            subject = st.text_input("Subject", value=default_subject, key=f"subject_{key_suffix}")
            body = st.text_area("Email Body", value=default_body, height=200, key=f"body_{key_suffix}")

            submitted = st.form_submit_button("Send Email")  # ✅ This survives rerun and works

            if submitted:
                if not to_email or "@" not in to_email:
                    st.error("❌ Invalid recipient email.")
                    return False
                if not subject.strip() or not body.strip():
                    st.error("❌ Subject and body are required.")
                    return False

                try:
                    message = MIMEMultipart()
                    message["From"] = email_user
                    message["To"] = to_email
                    message["Subject"] = subject
                    message.attach(MIMEText(body, "plain"))

                    with smtplib.SMTP("smtp.gmail.com", 587) as server:
                        server.starttls()
                        server.login(email_user, email_pass)
                        server.sendmail(email_user, to_email, message.as_string())

                    st.success(f"📧 Email sent successfully to {to_email}")
                    st.session_state[sent_flag_key] = True
                    return True

                except smtplib.SMTPAuthenticationError:
                    st.error("❌ SMTP Authentication failed. Check your Gmail app password.")
                except smtplib.SMTPException as smtp_err:
                    st.error("❌ SMTP error occurred.")
                    st.code(str(smtp_err))
                except Exception:
                    st.error("❌ Unexpected error occurred.")
                    st.code(traceback.format_exc())

    return False
