import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import traceback

def render_email_ui(email, missing_fields, full_name="Applicant", key_suffix="", email_user=None, email_pass=None):
    if not email:
        st.error("❌ No valid email address available.")
        return None, None

    sent_flag_key = f"email_sent_success_{key_suffix}"

    if st.session_state.get(sent_flag_key):
        st.info(f"Missing Info: {', '.join(missing_fields)}")
        st.success(f"✅ Email already sent to {full_name} at {email}")
        return full_name, email

    with st.expander(f"Review & Send Email to {email}", expanded=True):
        with st.form(f"email_form_{key_suffix}"):  # ✅ Use form to preserve state across reruns
            default_subject = "Missing Information in Your Application"
            default_body = (
                f"Dear {full_name},\n\n"
                f"We reviewed your rental application and noticed the following missing information:\n\n"
                f"{', '.join(missing_fields)}\n\n"
                f"Please provide the missing details at your earliest convenience so we can continue processing your application.\n\n"
                f"Thank you,\nEvercrest Homes Property Management Team"
            )

            applicant_name = st.text_input("Applicant Name", value=full_name, key=f"input_name_{key_suffix}")
            to_email = st.text_input("Recipient Email", value=email, key=f"input_email_{key_suffix}")
            subject = st.text_input("Subject", value=default_subject, key=f"subject_{key_suffix}")
            body = st.text_area("Email Body", value=default_body, height=200, key=f"body_{key_suffix}")

            send_clicked = st.form_submit_button("Send Email")  # ✅ form-safe button

            if send_clicked:
                try:
                    message = MIMEMultipart()
                    message["From"] = email_user
                    message["To"] = to_email
                    message["Subject"] = subject
                    message.attach(MIMEText(body, "plain"))

                    with smtplib.SMTP("smtp.ionos.com", 587) as server:
                        server.starttls()
                        server.login(email_user, email_pass)
                        server.sendmail(email_user, to_email, message.as_string())

                    st.success(f"📨 Email successfully sent to {to_email}")
                    st.session_state[sent_flag_key] = True

                except smtplib.SMTPAuthenticationError:
                    st.error("❌ SMTP Authentication failed. Check your IONOS credentials.")
                except Exception as e:
                    st.error(f"❌ Failed to send email to {to_email}")
                    st.code(traceback.format_exc())

        return applicant_name, to_email
