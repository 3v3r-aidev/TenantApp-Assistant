import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import traceback

def render_email_ui(email, missing_fields, full_name="Applicant", key_suffix="", email_user=None, email_pass=None):
    if not email_user or not email_pass:
        st.error("❌ Email credentials not provided.")
        return None, None

    # Unique state keys
    name_key = f"name_{key_suffix}"
    email_key = f"email_{key_suffix}"
    subject_key = f"subject_{key_suffix}"
    body_key = f"body_{key_suffix}"
    sent_flag_key = f"email_sent_success_{key_suffix}"

    # Default values
    default_subject = "Missing Information in Your Application"
    default_body = (
        f"Dear {full_name},\n\n"
        f"We reviewed your rental application and noticed the following missing information:\n\n"
        f"{', '.join(missing_fields)}\n\n"
        f"Please provide the missing details at your earliest convenience so we can continue processing your application.\n\n"
        f"Thank you,\nEvercrest Homes Property Management Team"
    )

    # Initialize session state if not set
    if name_key not in st.session_state:
        st.session_state[name_key] = full_name
    if email_key not in st.session_state:
        st.session_state[email_key] = email or ""
    if subject_key not in st.session_state:
        st.session_state[subject_key] = default_subject
    if body_key not in st.session_state:
        st.session_state[body_key] = default_body

    if st.session_state.get(sent_flag_key):
        st.success(f"✅ Email already sent to {st.session_state[email_key]}")
        return st.session_state[name_key], st.session_state[email_key]

    with st.expander(f"✉️ Review & Send Email to {st.session_state[email_key] or '[Missing]'}", expanded=True):
        with st.form(f"email_form_{key_suffix}"):
            st.text_input("Applicant Name", key=name_key)
            st.text_input("Recipient Email", key=email_key)
            st.text_input("Subject", key=subject_key)
            st.text_area("Email Body", key=body_key, height=200)

            send_clicked = st.form_submit_button("Send Email")

            if send_clicked:
                to_email = st.session_state[email_key]
                subject = st.session_state[subject_key]
                body = st.session_state[body_key]
                applicant_name = st.session_state[name_key]

                if not to_email or "@" not in to_email:
                    st.error("❌ Invalid email address.")
                    return applicant_name, to_email

                if not subject.strip() or not body.strip():
                    st.error("❌ Subject and Body are required.")
                    return applicant_name, to_email

                try:
                    msg = MIMEMultipart()
                    msg["From"] = email_user
                    msg["To"] = to_email
                    msg["Subject"] = subject
                    msg.attach(MIMEText(body, "plain"))

                    with smtplib.SMTP("smtp.ionos.com", 587) as server:
                        server.starttls()
                        server.login(email_user, email_pass)
                        server.sendmail(email_user, to_email, msg.as_string())

                    st.success(f"📨 Email sent to {to_email}")
                    st.session_state[sent_flag_key] = True
                    return applicant_name, to_email

                except smtplib.SMTPAuthenticationError:
                    st.error("❌ SMTP authentication failed.")
                except Exception as e:
                    st.error("❌ Email sending failed.")
                    st.code(traceback.format_exc())

    return st.session_state[name_key], st.session_state[email_key]
