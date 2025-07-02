# 🏠 TenantApp Assistant

**TenantApp Assistant** is a secure, end-to-end automation solution built with **Streamlit** to streamline the processing of rental application PDFs. It leverages **OpenAI GPT-4o Vision** to extract structured applicant data, validate key fields (e.g., SSN, employer, income), auto-fill standardized Excel templates, and notify applicants via email when required information is missing.

It is designed for **property managers, tenant screeners, and real estate operations teams** that want to automate applicant processing, improve data accuracy, and eliminate repetitive manual validation.

---

## 🚀 Key Features & Functionalities

### 🔐 Secure Access Control
- Enforces authentication using username/password stored in `.streamlit/secrets.toml`.
- Blocks unauthorized access to applicant data.

### 📤 Batch PDF Uploads
- Upload and process **multiple tenant applications at once**.
- Each PDF is read, parsed, and handled as an individual submission.

### 🧠 GPT-4o Vision Data Extraction
- Uses OpenAI’s Vision API to extract structured text and form data from scanned PDFs and image-based pages.
- Handles hybrid files containing both text-based and scanned content.

### 📄 Flattened Excel Export
- Extracted data is cleaned and flattened into a structured format.
- Appends to a persistent holder file: `Template_Data_Holder.xlsx` for cumulative processing and tracking.

### 📋 Auto-Generate Formatted Excel Templates
- Supports single and multiple applicant templates (`Tenant_Template.xlsx`, `Tenant_Template_Multiple.xlsx`).
- Field-level accuracy ensures compatibility with downstream systems (e.g., CRM, applicant screening software).

### 🧾 Field Validation and Completeness Checks
- Flags missing or malformed key fields:
  - Social Security Number (SSN)
  - Date of Birth
  - Employer name
  - Monthly income
- Validation report is shown in-app and optionally emailed to applicant.

### 📧 Automated Follow-Up Emails
- Applicants with missing info receive auto-generated email notifications.
- Email content is customized with field-level feedback.

### 🧹 Automatic File Cleanup
- Cleans up residual data from previous runs upon each new batch upload.
- Ensures workspace is fresh and avoids stale data issues.

---

## 🧰 Tech Stack

| Component        | Description                          |
|------------------|--------------------------------------|
| **Streamlit**     | Frontend & control flow UI           |
| **Python 3.13**   | Core backend logic                   |
| **OpenAI GPT-4o** | Vision-based OCR + NLP processing    |
| **PyMuPDF**       | PDF parsing and image rendering      |
| **Pillow**        | Image preprocessing                  |
| **Pandas**        | Data wrangling and Excel handling    |
| **smtplib/email** | Sending transactional email notices  |

---

## 🛠️ Setup Instructions

### 🔐 1. Configure Secrets

Create a `.streamlit/secrets.toml` file with:

'''
APP_USERNAME = "your_username"
APP_PASSWORD = "your_password"
EMAIL_USER = "your_email@example.com"
EMAIL_PASS = "your_email_password"
OPENAI_API_KEY = "sk-..."
'''

Note: Never commit this file to source control. Use Streamlit Cloud's built-in secrets manager for deployment.

**📦 2. Install Requirements**
Install dependencies using:

pip install -r requirements.txt

Your requirements.txt should include:

- streamlit
- openai
- pymupdf
- Pillow
- pandas

**▶️ 3. Run the Application**
Launch the app with:

streamlit run app.py
Visit http://localhost:8501 to interact with the UI.

**📸 Screenshots**
<p align="center"> <img src="https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/login_screen.png?raw=true" alt="Login" width="220"> <img src="https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/load_screen.png?raw=true" alt="Load Screen" width="220"> <img src="https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/full_ui.png?raw=true" alt="Full UI" width="220"> <img src="https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/main_ui.png?raw=true" alt="Main UI" width="220"> <img src="https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/sidebar_buttons.png?raw=true" alt="Sidebar" width="220"> <img src="https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/email_notif.png?raw=true" alt="Email Notification" width="220"> </p>

**✅ Usage Flow**
- Login with configured credentials.
- Upload PDF applications (multiple allowed).
- Extract data and auto-save to persistent Excel holder.
- View validation status for missing/invalid fields.
- Trigger email notices to applicants with incomplete data.
- Download formatted Excel files per applicant for final review.

**📌 Notes**
- The file Template_Data_Holder.xlsx is auto-cleared before every new upload batch.
- If required fields are missing, the app flags them and sends a follow-up email.
- If all data is complete, it proceeds silently to final output.
- GPT results are schema-enforced to ensure consistency across batches.

**🎯 Benefits**
- Reduces manual effort in data extraction, validation, and email handling.
- Improves accuracy in form field parsing using AI and schema enforcement.
- Standardizes outputs for use in downstream tools or business workflows.
- Scales seamlessly to handle multiple applicants per session.
- Enables audit trail by maintaining centralized Excel data holder.
- Improves applicant experience through timely email feedback.

**🧑‍💻 Developer Notes**
- Use st.session_state to track current UI state and avoid re-processing on rerun.
- Validate OpenAI Vision output against a consistent schema before Excel write.
- Ensure PDF files are in correct layout before extraction for best results.
- Build retry logic for OCR+Vision calls to handle API limits or latency.

**📃 License**
- MIT License © 2025
- Developed by Rhanny Urbis / BEST | Evercrest Homes
