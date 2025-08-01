import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import traceback

def render_email_ui(email, missing_fields, full_name="Applicant", key_suffix="", email_user=None, email_pass=None):
    if not email_user or not email_pass:
        st.error("❌ Missing email credentials.")
        return False

    # Keys for session storage
    name_key = f"name_{key_suffix}"
    email_key = f"email_{key_suffix}"
    subject_key = f"subject_{key_suffix}"
    body_key = f"body_{key_suffix}"
    sent_flag_key = f"sent_success_{key_suffix}"

    # Initialize session state if not set
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

    with st.expander(f"📤 Review & Send Email to {email or '[No Email]'}", expanded=True):
        with st.form(f"email_form_{key_suffix}"):
            st.session_state[name_key] = st.text_input("Applicant Name", value=st.session_state[name_key], key=f"input_name_{key_suffix}")
            st.session_state[email_key] = st.text_input("Recipient Email", value=st.session_state[email_key], key=f"input_email_{key_suffix}")
            st.session_state[subject_key] = st.text_input("Subject", value=st.session_state[subject_key], key=f"input_subject_{key_suffix}")
            st.session_state[body_key] = st.text_area("Email Body", value=st.session_state[body_key], height=200, key=f"input_body_{key_suffix}")

            send_clicked = st.form_submit_button("Send Email")

    # After form submission, send email using session values
    if send_clicked:
        try:
            message = MIMEMultipart()
            message["From"] = email_user
            message["To"] = st.session_state[email_key]
            message["Subject"] = st.session_state[subject_key]
            message.attach(MIMEText(st.session_state[body_key], "plain"))

            with smtplib.SMTP("smtp.ionos.com", 587) as server:
                server.starttls()
                server.login(email_user, email_pass)
                server.sendmail(
                    email_user,
                    st.session_state[email_key],
                    message.as_string()
                )

            st.session_state[sent_flag_key] = True
            st.success(f"✅ Email successfully sent to {st.session_state[email_key]}")
            return True

        except smtplib.SMTPAuthenticationError:
            st.error("❌ SMTP Authentication failed.")
        except Exception as e:
            st.error("❌ Failed to send email.")
            st.code(traceback.format_exc())
        return False

    # Optional message if already sent
    if st.session_state.get(sent_flag_key):
        st.info(f"✅ Email already sent to {st.session_state[email_key]}")
        return True

    return False
