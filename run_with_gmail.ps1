# Run Sentinel Mesh with Gmail enabled.
# 1. Edit the two lines below: put your Gmail and App Password (from https://myaccount.google.com/apppasswords)
# 2. Save this file.
# 3. In PowerShell run: .\run_with_gmail.ps1

$GmailAddress = "sentinelmesh594@gmail.com"      # <-- Change this
$GmailAppPassword = "fzxablfkysnqyokb"   # <-- Change this (no spaces)

Set-Location $PSScriptRoot
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
}
$env:EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
$env:EMAIL_HOST_USER = $GmailAddress
$env:EMAIL_HOST_PASSWORD = $GmailAppPassword
Write-Host "Starting server with Gmail. Open http://127.0.0.1:8000/" -ForegroundColor Green
python manage.py runserver
