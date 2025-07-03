## 🚀 Deployment to Streamlit Cloud

You can deploy **TenantApp Assistant** to [Streamlit Community Cloud](https://streamlit.io/cloud) for secure, browser-based access with no server setup.

---

### ✅ Prerequisites

Before deploying, make sure you have:

1. A **GitHub repository** containing your project code.
2. A working **`app.py`** at the root or properly referenced as the main entry point.
3. A complete `requirements.txt` listing all Python dependencies.
4. A `.streamlit/secrets.toml` file (for local use) or configured **Secrets in Streamlit Cloud**.

---

### 📦 Required Files Checklist

Your repo should include:
```
TenantAppAssistant/
├── app.py
├── extract_tenant_data.py
├── write_to_excel_template.py
├── write_template_holder.py
├── email_ui.py
├── templates/
│ └── [Your Excel Templates]
├── .streamlit/
│ └── config.toml (optional UI settings)
├── requirements.txt
└── README.md
```
---

### 📋 Step-by-Step Deployment

#### 1. Push Your Code to GitHub

Make sure your repository is public or private (you’ll be prompted to authorize it later).

#### 2. Create a Streamlit Account

Go to [https://streamlit.io/cloud](https://streamlit.io/cloud) and sign up using your GitHub credentials.

#### 3. Deploy Your App

- Click **"New App"**
- Choose your GitHub repo and branch
- Set the main file path to `app.py`
- Click **"Deploy"**

#### 4. Configure Secrets

Instead of pushing `.streamlit/secrets.toml` to GitHub (which is insecure), configure secrets via the **Streamlit Cloud UI**.

Click `⋮` > **Settings** > **Secrets**, then paste:

```
APP_USERNAME = "your_username"
APP_PASSWORD = "your_password"
EMAIL_USER = "your_email@example.com"
EMAIL_PASS = "your_email_password"
OPENAI_API_KEY = "sk-..."
```

#### Customize App UI
```
[theme]
primaryColor = "#3F8CFF"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#000000"
font = "sans serif"
```

[server]
headless = true
enableCORS = false

**🧪 Validate Deployment**
Once deployed:
- Visit your app URL (e.g., https://<username>-<repo>.streamlit.app)
- Login using your configured credentials
- Upload PDFs, trigger processing, and validate outputs

🔁 Updates
- Every time you push changes to your GitHub repo:
- Streamlit Cloud automatically redeploys your app.
- You can force a redeploy by clicking "Rerun" in the app UI or the cloud dashboard.

**🧩 Tips**
- Use st.cache_data or st.session_state for performance.
- Use file name uniqueness or timestamps to avoid Excel overwrite issues.
- Avoid storing large binary files in GitHub (e.g., uploaded PDFs); use cloud storage if scaling.

**🧑‍💻 Support**
- If you hit deployment issues, check the logs in the Streamlit Cloud Logs tab or validate your requirements.txt and app entrypoint.
- For advanced hosting (e.g., Docker + private server), request a separate setup guide.
