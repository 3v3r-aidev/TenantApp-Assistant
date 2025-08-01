import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import traceback

def render_email_ui(email, missing_fields, full_name="Applicant", key_suffix="", email_user=None, email_pass=None):
    if not email_user or not email_pass:
        st.error("❌ Missing email credentials.")
        return False

    # Define session keys
    form_prefix = f"{key_suffix}_form"
    name_key = f"{form_prefix}_name"
    email_key = f"{form_prefix}_email"
    subject_key = f"{form_prefix}_subject"
    body_key = f"{form_prefix}_body"
    sent_key = f"{form_prefix}_sent"
    trigger_key = f"{form_prefix}_trigger"

    # Set initial values
    if name_key not in st.session_state:
        st.session_state[name_key] = full_name
    if email_key not in st.session_state:
        st.session_state[email_key] = email or ""
    if subject_key not in st.session_state:
        st.session_state[subject_key] = "Missing Information in Your Application"
    if body_key not in st.session_state:
        st.session_state[body_key] = (
            f"Dear {full_name},\n\n"
            f"We reviewed your rental application and noticed the following missing information:\n\n"
            f"{', '.join(missing_fields)}\n\n"
            f"Please provide the missing details at your earliest convenience so we can continue processing your application.\n\n"
            f"Thank you,\nEvercrest Homes Property Management Team"
        )

    # Email form
    with st.expander(f"📧 Email to {st.session_state[email_key] or '[No Email]'}", expanded=True):
        with st.form(f"email_form_{key_suffix}"):
            st.text_input("Applicant Name", key=name_key)
            st.text_input("Recipient Email", key=email_key)
            st.text_input("Subject", key=subject_key)
            st.text_area("Email Body", key=body_key, height=200)
            submit = st.form_submit_button("Send Email")
            if submit:
                st.session_state[trigger_key] = True

    # Trigger actual email sending after form rerun
    if st.session_state.get(trigger_key):
        try:
            message = MIMEMultipart()
            message["From"] = email_user
            message["To"] = st.session_state[email_key]
            message["Subject"] = st.session_state[subject_key]
            message.attach(MIMEText(st.session_state[body_key], "plain"))

            with smtplib.SMTP("smtp.ionos.com", 587) as server:
                server.starttls()
                server.login(email_user, email_pass)
                server.sendmail(email_user, st.session_state[email_key], message.as_string())

            st.success(f"✅ Email sent to {st.session_state[email_key]}")
            st.session_state[sent_key] = True
        except smtplib.SMTPAuthenticationError:
            st.error("❌ SMTP Authentication failed.")
        except Exception as e:
            st.error("❌ Failed to send email.")
            st.code(traceback.format_exc())
        finally:
            st.session_state[trigger_key] = False

    # Show already sent info
    if st.session_state.get(sent_key):
        st.info(f"📨 Email already sent to {st.session_state[email_key]}")

    return st.session_state.get(sent_key, False)
