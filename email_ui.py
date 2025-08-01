import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import traceback

# Constants
EMAIL_HOST = "smtp.ionos.com"
EMAIL_PORT = 587

def render_email_ui(
    email: str,
    missing_fields: list,
    full_name="Applicant",
    key_suffix="",
    email_user=None,
    email_pass=None
):
    if not email_user or not email_pass:
        st.error("❌ Email credentials missing.")
        return

    if not email or "@" not in email:
        st.error(""❌ Missing applicant email. Ask applicant to re-submit with their email.")
        return

    # ----- Unique keys -----
    name_key = f"name_{key_suffix}"
    email_key = f"email_{key_suffix}"
    subject_key = f"subject_{key_suffix}"
    body_key = f"body_{key_suffix}"
    result_key = f"result_{key_suffix}"

    # ----- Default content -----
    default_subject = "Missing Information in Your Application"
    default_body = (
        f"Dear {full_name},\n\n"
        f"We reviewed your rental application and noticed the following missing information:\n\n"
        f"{', '.join(missing_fields)}\n\n"
        "Please provide the missing details at your earliest convenience.\n\n"
        "Thank you,\nEvercrest Homes Property Management Team"
    )

    # ----- Input Fields (Pre-filled, Editable) -----
    st.markdown("### 📧 Compose Email")
    st.text_input("Applicant Name", value=full_name, key=name_key)
    st.text_input("Recipient Email", value=email, key=email_key)
    st.text_input("Subject", value=default_subject, key=subject_key)
    st.text_area("Email Body", value=default_body, key=body_key, height=200)

    # ----- Send Email Button -----
    if st.button("Send Email", key=f"send_{key_suffix}"):
        try:
            msg = MIMEMultipart()
            msg["From"] = email_user
            msg["To"] = st.session_state[email_key]
            msg["Subject"] = st.session_state[subject_key]
            msg.attach(MIMEText(st.session_state[body_key], "plain"))

            with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=15) as server:
                server.starttls()
                server.login(email_user, email_pass)
                server.sendmail(
                    email_user,
                    st.session_state[email_key],
                    msg.as_string()
                )

            st.session_state[result_key] = f"✅ Email sent to {st.session_state[email_key]}"

        except Exception:
            st.session_state[result_key] = f"❌ Failed to send email:\n{traceback.format_exc()}"

    # ----- Show Result -----
    if result_key in st.session_state:
        msg = st.session_state[result_key]
        if msg.startswith("✅"):
            st.success(msg)
        else:
            st.error("❌ Email failed to send.")
            st.code(msg)

# Example call:
# render_email_ui(
#     email="applicant@example.com",
#     missing_fields=["proof of income", "ID copy"],
#     full_name="Juan Dela Cruz",
#     key_suffix="abc1",
#     email_user=st.secrets["email"]["EMAIL_USER"],
#     email_pass=st.secrets["email"]["EMAIL_PASS"]
# )
