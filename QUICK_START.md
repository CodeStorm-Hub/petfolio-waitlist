# Quick Start: Zoho Mail + Waitlist

## 1. Zoho SMTP

1. Open [Zoho Mail](https://mail.zoho.com) → **Settings** → **Mail Accounts** → your address → **Server configuration** and note **SMTP host** and port (**465** SSL or **587** TLS).
2. Use your **full email** as the SMTP user. With **2FA**, create an [application-specific password](https://www.zoho.com/mail/help/adminconsole/two-factor-authentication.html#alink5).

Docs: [Zoho SMTP](https://www.zoho.com/mail/help/zoho-smtp.html) · [Limits](https://www.zoho.com/mail/help/adminconsole/rates-and-limits.html)

## 2. `.env`

Configure Supabase (`SUPABASE_URL`, `SUPABASE_KEY`) plus:

```bash
ZOHO_MAIL_ADDRESS=welcome@yourdomain.com
ZOHO_MAIL_PASSWORD=your_app_specific_password_if_needed
# Optional — defaults shown:
# ZOHO_SMTP_HOST=smtp.zoho.com
# ZOHO_SMTP_PORT=465
# Use ZOHO_SMTP_PORT=587 for STARTTLS if you prefer TLS on 587
```

## 3. Run

```bash
source .venv/bin/activate   # after python3 -m venv .venv && pip install -r requirements.txt
python app.py
```

Submit the waitlist form → check inbox and logs.

## 4. Customize

Edit `templates/email/thank_you.html` for HTML branding; plain text is built in `app.py`.

Full detail: [EMAIL_SETUP.md](EMAIL_SETUP.md).
