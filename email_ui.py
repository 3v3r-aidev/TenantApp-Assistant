import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import traceback

def render_email_ui(email, missing_fields, full_name="Applicant", key_suffix="", email_user=None, email_pass=None):
    if not email_user or not email_pass:
        st.error("❌ Missing email credentials.")
        return False

    name_key = f"name_{key_suffix}"
    email_key = f"email_{key_suffix}"
    subject_key = f"subject_{key_suffix}"
    body_key = f"body_{key_suffix}"
    send_flag_key = f"send_flag_{key_suffix}"
    sent_flag_key = f"sent_flag_{key_suffix}"

    if name_key not in st.session_state:
        st.session_state[name_key] = full_name
    if email_key not in st.session_state:
        st.session_state[email_key] = email or ""
    if subject_key not in st.session_state:
        st.session_state[subject_key] = "Missing Information in Your Application"
    if body_key not in st.session_state:
        st.session_state[body_key] = (
            f"Dear {full_name},\n\n"
            f"We reviewed your rental application and noticed missing info: {', '.join(missing_fields)}.\n\n"
            "Please provide them at your earliest convenience.\n\nThanks,\nTeam"
        )

    with st.expander(f"📧 Email to {email or '[No Email]'}", expanded=True):
        with st.form(f"form_{key_suffix}"):
            st.text_input("Applicant Name", key=name_key)
            st.text_input("Recipient Email", key=email_key)
            st.text_input("Subject", key=subject_key)
            st.text_area("Email Body", key=body_key, height=200)
            if st.form_submit_button("Send Email"):
                st.session_state[send_flag_key] = True

    # Handle sending *after* rerun
    if st.session_state.get(send_flag_key):
        try:
            msg = MIMEMultipart()
            msg["From"] = email_user
            msg["To"] = st.session_state[email_key]
            msg["Subject"] = st.session_state[subject_key]
            msg.attach(MIMEText(st.session_state[body_key], "plain"))

            with smtplib.SMTP("smtp.ionos.com", 587) as server:
                server.starttls()
                server.login(email_user, email_pass)
                server.sendmail(email_user, st.session_state[email_key], msg.as_string())

            st.success(f"✅ Email sent to {st.session_state[email_key]}")
            st.session_state[sent_flag_key] = True
        except smtplib.SMTPAuthenticationError:
            st.error("❌ SMTP Authentication failed.")
        except Exception as e:
            st.error("❌ Sending failed.")
            st.code(traceback.format_exc())
        finally:
            st.session_state[send_flag_key] = False

    # Show message if already sent
    if st.session_state.get(sent_flag_key):
        st.info(f"📨 Email already sent to {st.session_state[email_key]}")

    return st.session_state.get(sent_flag_key, False)
