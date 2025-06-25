# 🏘️ Tenant Application Assistant

A secure, end-to-end Streamlit-based document processor for tenant applications. This app extracts structured data from uploaded tenant PDF forms using OpenAI Vision (GPT-4o), stores and edits the data, and generates preformatted Excel outputs for property management workflows.

---
## 🚀 Features

- 🔐 **Password-protected login** using Streamlit secrets
- 📄 **PDF form upload** with image-based OCR extraction (via GPT-4o Vision)
- 🧠 **Structured data parsing** of tenant forms and ID documents
- 📊 **Preview and edit extracted data** before saving
- 📁 **Save applicants to template holder** Excel
- 🧾 **Auto-fill Excel templates** for 1–10 applicants (single or multi-layout)
- ⬇️ **Download formatted Excel sheets** for official use
- 🖼️ **Custom logo branding** with persistent sidebar and footer
---

## 📁 Project Structure
---

## 🛠️ Local Setup

1. **Clone the repo:**

git clone https://github.com/your-org/tenantappassistant.git
cd tenantappassistant
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

2. **Install requirements**
pip install -r requirements.txt

3. **Run the app**
streamlit run app.py

5. **License**
This project is internal to Evercrest. For licensing or use outside of organization scope, contact project maintainers.

7. 👤 **Author**
Developed by R.B. Urbis – AI Specialist @ Evercrest
Powered by OpenAI GPT-4o
