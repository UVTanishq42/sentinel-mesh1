## Sentinel Mesh – Internship Scam Link Detector

This is a small Django web app that lets you **paste a job / internship link and immediately see whether it looks safe or suspicious**.  
It also **stores every scanned link in a SQL database** so future checks are instant and can be integrated into other platforms.

### Tech stack

- **Backend**: Django (Python, SQLite – DBMS/SQL)
- **Frontend**: HTML, CSS, JavaScript

### How to run the app (PowerShell – exact steps)

1. **Go to the project folder**
   ```powershell
   cd "C:\Users\govar\OneDrive\Desktop\Sentinel Mesh"
   ```

2. **Create and activate virtual environment** (first time only)
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```
   Or: `pip install django`

4. **Optional – enable Gmail so suspicious-link emails are really sent**
   - **Option A (once per project):** Copy `sentinel_mesh/email_config.example.py` to `sentinel_mesh/email_config.py`. Open `email_config.py`, set `USE_GMAIL = True`, and put your Gmail and [App Password](https://myaccount.google.com/apppasswords) in `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`. Save. Then whenever you run the server, Gmail will be used.
   - **Option B (each PowerShell session):** Before `runserver`, run:
   ```powershell
   $env:EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
   $env:EMAIL_HOST_USER = "your_gmail@gmail.com"
   $env:EMAIL_HOST_PASSWORD = "your_gmail_app_password"
   ```

5. **Apply migrations**
   ```powershell
   python manage.py migrate
   ```

6. **Start the server**
   ```powershell
   python manage.py runserver
   ```

7. **Open in browser:** `http://127.0.0.1:8000/`

### How it works (user flow)

- Paste any **internship / job URL** into the input box and click **“Scan link”**.
- The app performs a simple heuristic analysis (suspicious domains, URL length, keywords, etc.).
- It then:
  - Shows **SAFE** (green) or **SUSPICIOUS** (red) with a risk score.
  - **Stores the result** in the `ScannedLink` table (SQLite DB).
  - Updates a **“recently checked links”** list in the UI.
- If you also provide the **official company name and email**, and the link looks unsafe,  
  the app **sends an email notification** to that company (in development this prints to the console).

### Re‑using previous scans (for “click-time” protection)

For integration into an internship/job portal, you can use the **API endpoint**:

```text
GET /api/check-link/?url=FULL_URL_HERE
```

It returns JSON like:

```json
{
  "ok": true,
  "url": "https://example.com/path",
  "is_safe": false,
  "risk_score": 0.83,
  "times_seen": 4
}
```

This lets your main site warn users **as soon as they click a link**, using the saved status in the database.

