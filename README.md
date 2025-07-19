## 🏠 Tenant Application Assistant
A secure, end-to-end PDF parser and Excel generator for tenant applications. Built with Streamlit, this tool extracts structured data from scanned PDF applications, validates fields, and generates formatted Excel outputs for 1–2 or 3+ applicants. It also includes automatic email alerts for missing required fields.

### 🚀 Features
```
🔐 Secure Login System
📤 Batch PDF Upload & Extraction
📄 Form Type Detection (Standard/Handwritten)
🧠 GPT-Vision-based Form Parsing
📊 Flattened Excel Output (Tenant Template + Summary)
📧 Missing Field Validation & Email Notification
🖼️ OCR-based Image Extraction for Handwritten Forms
📁 Persistent Storage of Parsed Records
🧩 Modular Architecture for Extraction, Writing, and Email
```

### 🧰 Technologies Used
```
Streamlit – Web interface
Pandas – Data processing
OpenAI GPT Vision – Form parsing
Tesseract OCR – OCR fallback
OpenPyXL – Excel writing
smtplib, email.message – Email alerts
secrets.toml – Secure credentials handling
```
### 📂 Project Structure
```
├── main_app.py                      # Main Streamlit application
├── extract_tenant_data.py          # GPT parsing, image extraction, flattening logic
├── extract_utils.py                # Form detection and OCR helpers
├── write_to_excel_template.py      # Tenant and Summary Excel writers
├── write_template_holder.py        # Appends parsed records to Template_Data_Holder
├── email_ui.py                     # UI and backend email alert module
├── templates/
│   ├── Tenant_Template.xlsx        # Excel template for 1–2 applicants
│   ├── Tenant_Template_Multiple.xlsx  # Excel template for 3+ applicants
│   └── App_Summary_Template.xlsx   # Summary output
├── assets/
│   └── medical-history.png         # App logo
├── temp/                           # Temporary PDF/image storage
└── secrets.toml                    # Holds credentials (excluded in .gitignore)
```
### 🔒 Login Credentials Setup

**Create a secrets.toml file in the .streamlit folder:**

```
[openai]
OPENAI_API_KEY = "your_api_key"

[app]
APP_USERNAME = "your_username"
APP_PASSWORD = "your_password"

[email]
EMAIL_USER = "your_email@example.com"
EMAIL_PASS = "your_email_app_password"
```
### ▶️ How to Run
**1. Clone the Repository**
```
git clone https://github.com/your-org/tenant-application-assistant.git
cd tenant-application-assistant
```
**2. Install Dependencies**
```
pip install -r requirements.txt
```
Ensure Tesseract OCR is installed and available in your system PATH.

**3. Start the App**
```
streamlit run main_app.py
```
## 📸 Screenshots

<p>
  <img src="https://github.com/3v3r-aidev/TenantApp-Assistant/blob/main/screenshots/full_ui.png" alt="Full UI" width="500" height="500"> 
</p>

### 📌 Usage Workflow
```
Login with credentials from secrets.toml
Upload one or more PDF tenant applications
Click "Extract Data" to parse and convert
Click "Save Extracted Data" to store to Excel holder
Select applicants → "Save to Tenant Template"
Download finalized Excel files or summary
```
If required fields are missing, customizable email message requesting missing information can be sent

## 🧪 Form Support
Supported form types:
```
Form_A_2022, Form_B_2024 (standard typed forms)
handwritten_form (OCR + GPT extraction)
Auto-detection based on 1st-page text content
```

### 🛠️ Extending the App
Modular functions are defined for:

```
Form detection (extract_utils.py)
GPT Vision parsing (extract_tenant_data.py)
Excel generation (write_to_excel_template.py)
Email logic (email_ui.py)
```
**To add a new form type:**
```
Add detection logic to detect_form_type()
Create a new extraction route
Update conditional routing in main_app.py
```

### 📧 Email Alerts
Applicants missing:
```
Full Name
SSN
Phone Number
DOB
Current Employer
```
...will automatically trigger an editable email via UI with built-in send capability.

### 🌟 Benefits

* ✅ Reduces manual errors and copy-paste.
* ✅ Ensures field completeness and consistency.
* ✅ Leverages GPT Vision for complex document OCR.
* ✅ Streamlines form-to-Excel transformation.
* ✅ Enables automated communication with applicants.

### 📃 License

_**Proprietary Software**_
This software was developed by Rhanny Urbis for BEST | Evercrest Homes.
All rights to the source code, design, and functionality are exclusively held by the developer and BEST | Evercrest Homes.
```
🔒 No public redistribution or reuse is allowed without prior written consent.
🛠️ This app is intended solely for internal use by BEST | Evercrest Homes and its authorized users.
📧 For licensing or usage inquiries, contact the developer or BEST administration.
```
_**Developed by Rhanny Urbis / BEST | Evercrest Homes**_
