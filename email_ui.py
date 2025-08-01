import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import traceback

def render_email_ui(
    email, 
    missing_fields, 
    full_name="Applicant", 
    key_suffix="", 
    email_user=None, 
    email_pass=None
):
    if not email_user or not email_pass:
        st.error("❌ Missing email credentials.")
        return False

    form_prefix = f"{key_suffix}_form"
    name_key = f"{form_prefix}_name"
    email_key = f"{form_prefix}_email"
    subject_key = f"{form_prefix}_subject"
    body_key = f"{form_prefix}_body"
    result_key = f"{form_prefix}_result"

    # Initialize state values if not already
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

    # Email form UI
    with st.expander(f"📧 Email to {st.session_state[email_key] or '[No Email]'}", expanded=True):
        with st.form(f"email_form_{key_suffix}"):
            st.text_input("Applicant Name", key=name_key)
            st.text_input("Recipient Email", key=email_key)
            st.text_input("Subject", key=subject_key)
            st.text_area("Email Body", key=body_key, height=200)
            send = st.form_submit_button("Send Email")

            if send:
                try:
                    msg = MIMEMultipart()
                    msg["From"] = email_user
                    msg["To"] = st.session_state[email_key]
                    msg["Subject"] = st.session_state[subject_key]
                    msg.attach(MIMEText(st.session_state[body_key], "plain"))

                    with smtplib.SMTP("smtp.ionos.com", 587) as server:
                        server.starttls()
                        server.login(email_user, email_pass)
                        server.sendmail(
                            email_user,
                            st.session_state[email_key],
                            msg.as_string()
                        )

                    st.session_state[result_key] = f"✅ Email sent to {st.session_state[email_key]}"

                except Exception as e:
                    st.session_state[result_key] = "❌ Failed to send email:\n" + traceback.format_exc()

    # Show result
    if result_key in st.session_state:
        if st.session_state[result_key].startswith("✅"):
            st.success(st.session_state[result_key])
        else:
            st.error("❌ Email failed:")
            st.code(st.session_state[result_key])

    return st.session_state.get(result_key, "").startswith("✅")
