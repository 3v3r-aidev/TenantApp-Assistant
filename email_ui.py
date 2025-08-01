import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import traceback

def render_email_ui(email, missing_fields, full_name="Applicant", key_suffix="", email_user=None, email_pass=None):
    if not email_user or not email_pass:
        st.error("❌ Email credentials not provided.")
        return False

    sent_flag_key = f"email_sent_success_{key_suffix}"
    if st.session_state.get(sent_flag_key):
        st.success("✅ Email already sent.")
        return True

    with st.expander(f"Review & Send Email to {email or '[No Email]'}", expanded=True):
        with st.form(f"email_form_{key_suffix}"):

            # Live editable fields
            to_email = st.text_input("Recipient Email", value=email, key=f"email_{key_suffix}")
            subject = st.text_input("Subject", value="Missing Information in Your Application", key=f"subject_{key_suffix}")

            # Use session state to persist modified content on rerun
            default_body = (
                f"We reviewed your rental application and noticed the following missing information:\n\n"
                f"{', '.join(missing_fields)}\n\n"
                f"Please provide the missing details so we can continue processing your application.\n\n"
                f"Thank you,\nEvercrest Homes Property Management Team"
            )

            if f"body_{key_suffix}" not in st.session_state:
                st.session_state[f"body_{key_suffix}"] = default_body

            body = st.text_area("Email Body", value=st.session_state[f"body_{key_suffix}"], height=200, key=f"body_{key_suffix}")

            send_clicked = st.form_submit_button("Send Email")

            if send_clicked:
                if not to_email or "@" not in to_email:
                    st.error("❌ Invalid recipient email address.")
                    return False
                if not subject.strip() or not body.strip():
                    st.error("❌ Subject and Body are required.")
                    return False

                try:
                    # Construct MIME email
                    msg = MIMEMultipart()
                    msg["From"] = email_user
                    msg["To"] = to_email
                    msg["Subject"] = subject
                    msg.attach(MIMEText(body, "plain"))

                    # ✅ IONOS SMTP Configuration
                    with smtplib.SMTP("smtp.ionos.com", 587, timeout=15) as server:
                        server.starttls()
                        server.login(email_user, email_pass)
                        server.sendmail(email_user, to_email, msg.as_string())

                    st.success(f"📧 Email successfully sent to {to_email}")
                    st.session_state[sent_flag_key] = True
                    return True

                except smtplib.SMTPAuthenticationError:
                    st.error("❌ Authentication failed. Check your IONOS email credentials.")
                except smtplib.SMTPRecipientsRefused:
                    st.error(f"❌ Recipient rejected: {to_email}")
                except smtplib.SMTPConnectError:
                    st.error("❌ Connection to IONOS SMTP server failed.")
                except smtplib.SMTPException as smtp_err:
                    st.error("❌ SMTP error.")
                    st.code(str(smtp_err))
                except Exception:
                    st.error("❌ Unexpected error during email send.")
                    st.code(traceback.format_exc())

    return False
