import streamlit as st
import os
import pandas as pd
import json
import smtplib
from email.message import EmailMessage
from extract_tenant_data import process_pdf
from extract_tenant_data import flatten_extracted_data, parse_gpt_output
from write_template_holder import append_to_template_holder, write_multiple_applicants_to_template
from dotenv import load_dotenv

# --- Page Config MUST be first ---
st.set_page_config(page_title="Tenant App Dashboard", layout="wide")

# Load credentials from .env
load_dotenv()
USERNAME = os.getenv("APP_USERNAME")
PASSWORD = os.getenv("APP_PASSWORD")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# --- Login Logic ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.form("Login"):
        st.subheader("🔐 Tenant App Login")
        username_input = st.text_input("Username")
        password_input = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button:
            if username_input == USERNAME and password_input == PASSWORD:
                st.session_state.logged_in = True
                st.experimental_rerun()
            else:
                st.error("❌ Invalid credentials")
    st.stop()
else:
    st.sidebar.success(f"🔓 Logged in as {USERNAME}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- Main App Logic ---
APPLICANTS_FOLDER = "./applicants"
EXTRACTED_DATA_PATH = "Template_Holder.xlsx"

st.sidebar.title("Navigation")
st.title(" Tenant Application Assistant")
st.markdown("This tool extracts, previews, edits, and validates tenant application data.")

# Sidebar: Choose applicants and write selected data to tenant template
if os.path.exists(EXTRACTED_DATA_PATH):
    df_holder = pd.read_excel(EXTRACTED_DATA_PATH)
    if not df_holder.empty:
        selected_indices = st.sidebar.multiselect(
            "Select applicant(s) to write to tenant template:",
            options=df_holder.index,
            format_func=lambda i: f"{df_holder.at[i, 'FullName']} - {df_holder.at[i, 'Property Address']}"
        )

        if st.sidebar.button("Save to Tenant Template"):
            try:
                selected_df = df_holder.loc[selected_indices] if selected_indices else pd.DataFrame()
                if selected_df.empty:
                    st.sidebar.warning("Please select at least one applicant.")
                else:
                    output_path = write_multiple_applicants_to_template(selected_df)
                    st.sidebar.success(f"✅ Written to {output_path}")
            except Exception as e:
                st.sidebar.error(f"❌ Failed to write to tenant template: {e}")
else:
    st.sidebar.warning("No Template_Holder.xlsx found. Save data first.")

# Loop through all PDFs
pdf_files = [f for f in os.listdir(APPLICANTS_FOLDER) if f.lower().endswith(".pdf")]

if not pdf_files:
    st.warning("No PDF files found in the applicants folder.")
else:
    for filename in pdf_files:
        pdf_path = os.path.join(APPLICANTS_FOLDER, filename)
        key_prefix = filename.replace(".", "_").replace(" ", "_")

        with st.expander(f"{filename}"):
            if st.button(f"Extract: {filename}", key=f"extract_{key_prefix}"):
                with st.spinner("Extracting data from application..."):
                    extracted, _ = process_pdf(pdf_path)
                    st.session_state[f"form_data_{key_prefix}"] = extracted

            if f"form_data_{key_prefix}" in st.session_state:
                form_data = st.session_state[f"form_data_{key_prefix}"]

                st.subheader("Data extracted.")

                try:
                    parsed_data = parse_gpt_output(form_data)
                    flat_data = flatten_extracted_data(parsed_data)

                    # Check for missing critical fields
                    missing_fields = []
                    for field in ["SSN", "DriverLicenseNumber", "DOB"]:
                        if not flat_data.get(field):
                            missing_fields.append(field)

                    if missing_fields:
                        st.warning(f"⚠️ Missing information: {', '.join(missing_fields)}")

                        if flat_data.get("Email"):
                            with st.expander("✉️ Send Email to Applicant"):
                                default_message = f"Hello {flat_data.get('FullName', 'Applicant')},\n\nWe noticed your application is missing the following required information: {', '.join(missing_fields)}.\n\nPlease reply with the missing details so we can continue processing your application.\n\nThank you!"
                                email_body = st.text_area("Edit Email Message", value=default_message, height=200)
                                if st.button("📤 Send Email"):
                                    try:
                                        msg = EmailMessage()
                                        msg["Subject"] = "Missing Information in Your Application"
                                        msg["From"] = EMAIL_USER
                                        msg["To"] = flat_data.get("Email")
                                        msg.set_content(email_body)

                                        with smtplib.SMTP_SSL("smtp.ionos.com", 465) as smtp:
                                            smtp.login(EMAIL_USER, EMAIL_PASS)
                                            smtp.send_message(msg)
                                        st.success("📧 Email sent successfully!")
                                    except Exception as e:
                                        st.error(f"❌ Failed to send email: {e}")
                        else:
                            st.error("❌ Cannot send email — no email address found.")

                    # Save button after check
                    if st.button(f"Save {filename} to Excel", key=f"save_{key_prefix}"):
                        try:
                            append_to_template_holder(flat_data)
                            st.session_state[f"flattened_data_{key_prefix}"] = flat_data
                            st.success("✅ Saved to Template_Holder.xlsx")
                        except Exception as e:
                            st.error(f"❌ Failed to save data: {e}")

                except Exception as e:
                    st.error(f"❌ Failed to parse extracted data: {e}")
