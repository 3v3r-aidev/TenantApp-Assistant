def render_email_ui(email, missing_fields, full_name="Applicant", key_suffix="", email_user=None, email_pass=None):
    if not email:
        st.error("❌ No valid email address available.")
        return

    if not email_user or not email_pass:
        st.error("❌ Email credentials missing.")
        return

    sent_flag_key = f"email_sent_success_{key_suffix}"
    status_msg_key = f"email_status_msg_{key_suffix}"

    with st.expander(f"Review & Send Email to {email}", expanded=True):
        default_subject = "Missing Information in Your Application"
        default_body = f"""Dear {full_name},\n\nWe reviewed your rental application and noticed the following missing information:\n\n{', '.join(missing_fields)}\n\nPlease provide the missing details at your earliest convenience so we can continue processing your application.\n\nThank you,\nEvercrest Homes Property Management Team"""

        applicant_name = st.text_input("Applicant Name", value=full_name, key=f"input_name_{key_suffix}")
        to_email = st.text_input("Recipient Email", value=email, key=f"input_email_{key_suffix}")
        subject = st.text_input("Subject", value=default_subject, key=f"subject_{key_suffix}")
        body = st.text_area("Email Body", value=default_body, height=200, key=f"body_{key_suffix}")

        send = st.button("Send Email", key=f"send_button_{key_suffix}")

        if send:
            if not to_email or "@" not in to_email:
                st.error("❌ Please enter a valid recipient email address.")
            elif not subject.strip() or not body.strip():
                st.error("❌ Subject and Body cannot be empty.")
            else:
                try:
                    message = MIMEMultipart()
                    message["From"] = email_user
                    message["To"] = to_email
                    message["Subject"] = subject
                    message.attach(MIMEText(body, "plain"))

                    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=15) as server:
                        server.starttls()
                        server.login(email_user, email_pass)
                        server.sendmail(email_user, to_email, message.as_string())

                    st.session_state[sent_flag_key] = True
                    st.session_state[status_msg_key] = f"✅ Email successfully sent to {to_email}"

                except smtplib.SMTPAuthenticationError:
                    st.session_state[status_msg_key] = "❌ SMTP Authentication failed."
                except smtplib.SMTPRecipientsRefused:
                    st.session_state[status_msg_key] = f"❌ Recipient address rejected: {to_email}"
                except smtplib.SMTPConnectError:
                    st.session_state[status_msg_key] = "❌ Could not connect to SMTP server."
                except smtplib.SMTPException as smtp_err:
                    st.session_state[status_msg_key] = f"❌ SMTP Error: {smtp_err}"
                except Exception:
                    st.session_state[status_msg_key] = traceback.format_exc()

        # Show current status (after send or resend)
        if st.session_state.get(status_msg_key):
            msg = st.session_state[status_msg_key]
            if msg.startswith("✅"):
                st.success(msg)
            else:
                st.error("❌ Failed to send email.")
                st.code(msg)

    return applicant_name, to_email
