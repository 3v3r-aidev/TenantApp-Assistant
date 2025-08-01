import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import traceback

def render_email_ui(email, missing_fields, full_name="Applicant", key_suffix="", email_user=None, email_pass=None):
    if not email_user or not email_pass:
        st.error("❌ Email credentials not provided. Please check your Streamlit secrets.")
        return False

    sent_flag_key = f"email_sent_success_{key_suffix}"

    if st.session_state.get(sent_flag_key):
        st.success(f"✅ Email requesting missing info already sent to {full_name}")
        return True

    with st.expander(f"Review & Send Email", expanded=True):
        with st.form(f"email_form_{key_suffix}"):  # ✅ FORM WRAPPING
            default_subject = "Missing Information in Your Application"
            default_body = f"""Dear {full_name},\n\nWe reviewed your rental application and noticed the following missing information:\n\n{', '.join(missing_fields)}\n\nPlease provide the missing details at your earliest convenience so we can continue processing your application.\n\nThank you,\nEvercrest Homes Property Management Team"""

            # INPUT FIELDS (editable)
            applicant_name = st.text_input("Applicant Name", value=full_name, key=f"input_name_{key_suffix}")
            to_email = st.text_input("Recipient Email", value=email, key=f"input_email_{key_suffix}")
            subject = st.text_input("Subject", value=default_subject, key=f"subject_{key_suffix}")
            body = st.text_area("Email Body", value=default_body, height=200, key=f"body_{key_suffix}")

            send_clicked = st.form_submit_button("Send Email")  # ✅ Proper trigger

            if send_clicked:
                if not to_email or "@" not in to_email:
                    st.error("❌ Please enter a valid recipient email address.")
                    return False

                if not subject.strip() or not body.strip():
                    st.error("❌ Subject and Body cannot be empty.")
                    return False

                try:
                    message = MIMEMultipart()
                    message["From"] = email_user
                    message["To"] = to_email
                    message["Subject"] = subject
                    message.attach(MIMEText(body, "plain"))

                    with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
                        server.starttls()
                        server.login(email_user, email_pass)
                        server.sendmail(email_user, to_email, message.as_string())

                    st.success(f"📧 Email successfully sent to {to_email}")
                    st.session_state[sent_flag_key] = True
                    return True

                except smtplib.SMTPAuthenticationError:
                    st.error("❌ SMTP Authentication failed. Please check your email credentials.")
                except smtplib.SMTPRecipientsRefused:
                    st.error(f"❌ Recipient address rejected: {to_email}")
                except smtplib.SMTPConnectError:
                    st.error("❌ Could not connect to SMTP server. Check your network.")
                except smtplib.SMTPException as smtp_err:
                    st.error("❌ SMTP Error occurred.")
                    st.code(str(smtp_err))
                except Exception:
                    st.error(f"❌ Unexpected error occurred while sending email to {to_email}")
                    st.code(traceback.format_exc())

    return False
