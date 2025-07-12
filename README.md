# 🏠 TenantApp Assistant

**TenantApp Assistant** is a secure, end-to-end automation solution built with **Streamlit** to streamline the processing of rental application PDFs. It leverages **OpenAI GPT-4o Vision** to extract structured applicant data, validate key fields (e.g., SSN, employer, income), auto-fill standardized Excel templates, and notify applicants via email when required information is missing.

It is designed for **property managers, tenant screeners, and real estate operations teams** that want to automate applicant processing, improve data accuracy, and eliminate repetitive manual validation.

---

## 🚀 Key Features & Functionalities

### 🔐 Secure Access Control

* Enforces authentication using username/password stored in streamlit secrets.
* Blocks unauthorized access to applicant data.

### 🧐 GPT-4o Vision Data Extraction

* Uses OpenAI’s Vision API to extract structured text and form data from scanned PDFs and image-based pages.
* Handles hybrid files containing both text-based and scanned content.
* Dynamically flattens nested sections like: Co-applicants, Vehicle Info, Occupants.

### 📅 Flattened Excel Holder with Field Cleaning

* Extracted data is cleaned and flattened into a structured format.
* Appends to a persistent file `Template_Data_Holder.xlsx` for staging, batch preview, and Excel output.
* All dates normalized to mm/dd/yyyy. All currency fields cleaned of `$`.

### 📈 Auto-Generate Excel Templates (Single/Multiple)

* Supports both `Tenant_Template.xlsx` and `Tenant_Template_Multiple.xlsx`.
* Multiple applicants are written to offset columns; vehicle entries are wrapped per row.
* Monthly vehicle payments are summed across vehicles.

### 📊 Field Validation + Email Trigger

* Auto-flags missing or malformed fields like:

  * Date of Birth
  * SSN
  * Phone
    
* Sends follow-up emails for incomplete fields via your configured SMTP.

### 📧 Optional Automated Email Notifications

* Missing fields trigger email option to request applicants for missing required info
* Emails are formatted from template and dispatched securely.

### 🚮 Auto Data Cleanup

* Cleans previous records in the template holder before writing a new batch.
* Ensures stale values never appear in final Excel outputs.

---

## 🧰 Tech Stack

| Component         | Description                         |
| ----------------- | ----------------------------------- |
| **Streamlit**     | Frontend & control flow UI          |
| **Python 3.13**   | Core backend logic                  |
| **OpenAI GPT-4o** | Vision-based OCR + NLP processing   |
| **PyMuPDF**       | PDF parsing and image rendering     |
| **Pillow**        | Image preprocessing                 |
| **Pandas**        | Data wrangling and Excel handling   |
| **smtplib/email** | Sending transactional email notices |

---

## 🛠️ Setup Instructions

### 🔐 1. Configure Secrets

Create a `.streamlit/secrets.toml` file with:

```
APP_USERNAME = "your_username"
APP_PASSWORD = "your_password"
EMAIL_USER = "your_email@example.com"
EMAIL_PASS = "your_email_password"
OPENAI_API_KEY = "sk-..."
```

Note: Never commit this file to source control. Use Streamlit Cloud's built-in secrets manager for deployment.

### 📦 2. Install Requirements

Install dependencies using:

```
pip install -r requirements.txt
```

Your `requirements.txt` should include:

* streamlit
* openai
* pymupdf
* Pillow
* pandas

### ▶️ 3. Run the Application

Launch the app with:

```
streamlit run app.py
```

Visit [http://localhost:8501](http://localhost:8501) to interact with the UI.

---

## 📸 Screenshots

<p>
  <img src="https://github.com/3v3r-aidev/TenantApp-Assistant/blob/main/screenshots/full_ui.png" alt="Full UI" width="500" height="500"> 
</p>

---

## ✅ Usage Flow

1. Login with configured credentials.
2. Upload multiple PDF applications for a single property
3. Save to `Template_Data_Holder.xlsx` for preview.
4. Review validation results for missing/invalid data.
5. Has email option to request applicants to submit required missing info
6. Generate final Excel files for downstream review or import.

---

## 📌 Notes

* `Template_Data_Holder.xlsx` is the live working file across batches.
* Vehicle entries are parsed line-by-line, summed, and formatted as multi-line.
* Dates are normalized (`MM/DD/YYYY`) and `$` symbols are stripped.
* Co-applicants are counted toward total occupants but not treated as dependents.

---

## 🌟 Benefits

* ✅ Reduces manual errors and copy-paste.
* ✅ Ensures field completeness and consistency.
* ✅ Leverages GPT Vision for complex document OCR.
* ✅ Streamlines form-to-Excel transformation.
* ✅ Enables automated communication with applicants.

---

## 👨‍💼 Developer Notes

* Uses `st.session_state` to persist extraction state.
* Excel write logic supports variable vehicle count and multi-applicant forms.
* GPT schema is enforced to avoid hallucinated fields.
* Date and currency fields are always normalized before writing.

---

## 📃 License

MIT License © 2025
Developed by Rhanny Urbis / BEST | Evercrest Homes
