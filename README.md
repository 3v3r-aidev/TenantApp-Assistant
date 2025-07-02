# 🏠 TenantApp Assistant
**TenantApp Assistant** is a secure, end-to-end Streamlit app designed to process rental application PDFs, extract applicant data using OpenAI GPT-4o Vision, validate key fields, auto-generate Excel templates, and email applicants if required information is missing.

---

## 🚀 Features

- 🔐 Secure login with credential control
- 📤 Upload multiple tenant application PDFs
- 🧠 Extract structured data using GPT-4o Vision API
- 📄 Flatten and save extracted data to a persistent Excel holder (`Template_Data_Holder.xlsx`)
- 📋 Generate downloadable Excel-based application templates (single/multiple applicants)
- 🧾 Auto-validate missing fields such as SSN, Employer, Income, etc.
- 📧 Send follow-up emails to applicants requesting missing information
 🧹 Automatic cleanup of previous session data and template files on new upload batch

---

## 🧰 Tech Stack

- [Streamlit](https://streamlit.io/)
- [Python 3.9+](https://www.python.org/)
- [OpenAI GPT-4o (Vision)](https://platform.openai.com/)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [Pillow](https://pypi.org/project/Pillow/)
- [Pandas](https://pandas.pydata.org/)
- [smtplib / email](https://docs.python.org/3/library/email.html)

---

## 📂 Folder Structure

```bash
TenantAppAssistant/
├── app.py
├── extract_tenant_data.py
├── write_to_excel_template.py
├── write_template_holder.py
├── email_ui.py
├── templates/
│   ├── Tenant_Template.xlsx
│   ├── Tenant_Template_Multiple.xlsx
│   └── Template_Data_Holder.xlsx
├── assets/
│   └── medical-history.png
├── .streamlit/
│   └── secrets.toml
├── .env  # (Optional, if using local env vars)
└── requirements.txt

🛠️ Setup Instructions
🔐 1. Set Secrets (Recommended)
Create a file at .streamlit/secrets.toml:

APP_USERNAME = "your_username"
APP_PASSWORD = "your_password"
EMAIL_USER = "your_email@example.com"
EMAIL_PASS = "your_email_password"
OPENAI_API_KEY = "sk-..."

Never commit real credentials to GitHub. Use Streamlit Cloud’s Secrets Manager in production.

📦 2. Install Requirements
pip install -r requirements.txt
Ensure the following packages are in your requirements.txt:

streamlit
openai
pymupdf
Pillow
pandas

▶️ 3. Run the App

streamlit run app.py

Then open http://localhost:8501 in your browser.

📸 Screenshots

![Login](https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/email_notif.png)
![Full UI](https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/full_ui.png)
![Main UI](https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/main_ui.png?)
![Sidebar](https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/sidebar_buttons.png)
![Email](https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/email_notif.png)

✅ Usage Flow
Login using your configured credentials.
Upload PDF applications (multiple allowed).
Extract and Save each form to Excel holder.
Review validation results.
Send email to applicants missing info (auto-generated).
Download final templates with clean data.

📌 Notes
Template holder (Template_Data_Holder.xlsx) is automatically cleared upon new batch uploads.
A notification of missing info and sent email is shown if applicant has missing required info.
A message is shown if all required info are available.
GPT output is strictly parsed and flattened — schema enforced.

🧑‍💻 Developer Tips
Add logging during parsing to capture GPT issues.
Ensure correct field matching in flatten_extracted_data.
Use st.session_state flags to control UI visibility and prevent duplicates.

📃 License
MIT License © 2025
Developed by [Rhanny Urbis / BEST | Evercrest Homes]
