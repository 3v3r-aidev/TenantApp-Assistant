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
EMAIL_USER = st.secrets["email"] ["EMAIL_USER"]
EMAIL_PASS = st.secrets["email"] ["EMAIL_PASS"]

# --- Constants ---
EXTRACTED_DATA_PATH = "templates/Template_Data_Holder.xlsx"
EMAIL_HOST = "smtp.ionos.com"
EMAIL_PORT = 587  # STARTTLS port

# --- Function to render email UI ---
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback
import sys

import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import traceback
import os
import pandas as pd
from dotenv import load_dotenv

# --- Constants ---
EXTRACTED_DATA_PATH = "templates/Template_Data_Holder.xlsx"
EMAIL_HOST = "smtp.ionos.com"
EMAIL_PORT = 587  # STARTTLS port

# --- Load environment ---
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")



# --- Constants ---
EXTRACTED_DATA_PATH = "templates/Template_Data_Holder.xlsx"
EMAIL_HOST = "smtp.ionos.com"
EMAIL_PORT = 587  # STARTTLS port

# --- Load environment ---
load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# --- Function to render email UI ---
def render_email_ui(email, missing_fields, full_name="Applicant", key_suffix="", email_user=None, email_pass=None):
    if not email:
        st.error("❌ No valid email address available.")
        return

    sent_flag_key = f"email_sent_success_{key_suffix}"

    # ✅ Skip rendering the form if already sent
    if st.session_state.get(sent_flag_key):
        st.success(f"✅ Email requesting missing info already sent to {full_name} at {email}")
        return

    with st.expander(f"📧 Email for {email} (Missing: {', '.join(missing_fields)})", expanded=True):
        subject = "Missing Information in Your Application"
        body = f"""Dear {full_name},

We reviewed your rental application and noticed the following missing information:

{', '.join(missing_fields)}

Please provide the missing details at your earliest convenience so we can continue processing your application.

Thank you,
Evercrest Homes Property Management Team"""

        try:
            # Auto-send once when form is rendered
            message = MIMEMultipart()
            message["From"] = email_user
            message["To"] = email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))

            with smtplib.SMTP("smtp.ionos.com", 587) as server:
                server.starttls()
                server.login(email_user, email_pass)
                server.sendmail(email_user, email, message.as_string())

            st.success(f"📧 Email successfully sent to {email}")
            st.session_state[sent_flag_key] = True

        except smtplib.SMTPAuthenticationError:
            st.error("❌ SMTP Authentication failed. Check your credentials.")
        except Exception as e:
            st.error(f"❌ Failed to send email to {email}")
            st.code(traceback.format_exc())

