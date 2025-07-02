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
- 🧹 Automatic cleanup of previous session data and template files on new upload batch  

---

## 🧰 Tech Stack

- [Streamlit](https://streamlit.io/)  
- [Python 3.13](https://www.python.org/)  
- [OpenAI GPT-4o (Vision)](https://platform.openai.com/)  
- [PyMuPDF](https://pymupdf.readthedocs.io/)  
- [Pillow](https://pypi.org/project/Pillow/)  
- [Pandas](https://pandas.pydata.org/)  
- [smtplib / email](https://docs.python.org/3/library/email.html)  

---

## 🛠️ Setup Instructions

**🔐 1. Set Secrets (Recommended)**
<br>
Create a file at .streamlit/secrets.toml:

- APP_USERNAME = "your_username"</br>
- APP_PASSWORD = "your_password"</br>
- EMAIL_USER = "your_email@example.com"</br>
- EMAIL_PASS = "your_email_password"</br>
- OPENAI_API_KEY = "sk-..."</br>

Never commit real credentials to GitHub. Use Streamlit Cloud’s Secrets Manager in production.

**📦 2. Install Requirements**

pip install -r requirements.txt
Ensure the following packages are in your requirements.txt:

- streamlit
- openai
- pymupdf
- Pillow
- pandas

**▶️ 3. Run the App**

streamlit run app.py
Then open http://localhost:8501 in your browser.

**📸 Screenshots**
<p>
<img src="https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/login_screen.png?raw=true" alt="Login" width="550" height = "400"> 
<img src="https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/full_ui.png?raw=true" alt="Full UI" width="400" height = "400"> 
<img src="https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/main_ui.png?raw=true" alt="Main UI" width="400" height = "400"> 
<img src="https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/email_notif.png?raw=true" alt="Email Notification" width="400" height ="400"> 
<img src="https://github.com/rnx2024/AppScreener-Assistant/blob/main/screenshots/sidebar_buttons.png?raw=true" alt="Sidebar" height = "400"> </p>

**✅ Usage Flow**
- Login using your configured credentials.
- Upload PDF applications (multiple allowed).
- Extract and save each form to Excel holder.
- Review validation results.
- Send email to applicants missing info (auto-generated).
- Download final templates with clean data.

**📌 Notes**
- Template_Data_Holder.xlsx is automatically cleared upon new batch uploads.
- A notification is shown if an applicant has missing required info and email is sent.
- A message is shown if all required info is present.
- GPT output is strictly parsed and flattened — schema enforced.

**📃 License**
- MIT License © 2025
- Developed by Rhanny Urbis / BEST | Evercrest Homes
