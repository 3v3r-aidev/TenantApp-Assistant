import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import traceback
import sys
import os
import pandas as pd

# --- Constants ---
EXTRACTED_DATA_PATH = "templates/Template_Data_Holder.xlsx"
EMAIL_HOST = "smtp.ionos.com"
EMAIL_PORT = 587  # STARTTLS port

# --- Load credentials ---
EMAIL_USER = st.secrets["email"]["EMAIL_USER"]
EMAIL_PASS = st.secrets["email"]["EMAIL_PASS"]

# --- Function to render email UI ---
def render_email_ui(email, missing_fields, full_name="Applicant", key_suffix="", email_user=None, email_pass=None):
    if not email:
        st.error("\u274C No valid email address available.")
        return

    sent_flag_key = f"email_sent_success_{key_suffix}"

    # ✅ Skip rendering the form if already sent
    if st.session_state.get(sent_flag_key):
        st.info(f"Missing Info: {', '.join(missing_fields)}")
        st.success(f"\u2705 Email requesting missing info already sent to {full_name} at {email}")
        return

    with st.expander(f"\ud83d\udce7 Review & Send Email to {email}", expanded=True):
        default_subject = "Missing Information in Your Application"
        default_body = f"""Dear {full_name},\n\nWe reviewed your rental application and noticed the following missing information:\n\n{', '.join(missing_fields)}\n\nPlease provide the missing details at your earliest convenience so we can continue processing your application.\n\nThank you,\nEvercrest Homes Property Management Team"""

        to_email = st.text_input("Recipient Email", value=email, key=f"input_email_{key_suffix}")
        subject = st.text_input("Subject", value=default_subject, key=f"subject_{key_suffix}")
        body = st.text_area("Email Body", value=default_body, height=200, key=f"body_{key_suffix}")

        if st.button("Send Email", key=f"send_button_{key_suffix}"):
            try:
                message = MIMEMultipart()
                message["From"] = email_user
                message["To"] = to_email
                message["Subject"] = subject
                message.attach(MIMEText(body, "plain"))

                with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
                    server.starttls()
                    server.login(email_user, email_pass)
                    server.sendmail(email_user, to_email, message.as_string())

                st.success(f"\u2709\ufe0f Email successfully sent to {to_email}")
                st.session_state[sent_flag_key] = True

            except smtplib.SMTPAuthenticationError:
                st.error("\u274C SMTP Authentication failed. Check your credentials.")
            except Exception as e:
                st.error(f"\u274C Failed to send email to {to_email}")
                st.code(traceback.format_exc())
