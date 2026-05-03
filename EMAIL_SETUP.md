# PetFolio Email Setup (Zoho Mail SMTP)

## Overview

After someone joins the waitlist, the Flask app sends a personalized thank-you email using **Zoho Mail SMTP** (`smtplib`). Signups still succeed if SMTP fails.

Official references:

- [Zoho Mail SMTP configuration](https://www.zoho.com/mail/help/zoho-smtp.html)
- [Rates, limits, and policies](https://www.zoho.com/mail/help/adminconsole/rates-and-limits.html)

## SMTP server names (confirm in your account)

Zoho says the **exact** hostname for your mailbox is shown under **Mail → Settings → Mail Accounts → Server configuration**. Typical values:

| Account type | Outgoing server | Ports |
|--------------|-----------------|-------|
| Personal `@zohomail.com` and **Free Organization** | `smtp.zoho.com` | **465** (SSL) or **587** (STARTTLS) |
| **Paid Organization** with domain email (`you@yourdomain.com`) | Often `smtppro.zoho.com` | Same ports |

EU / India datacenters may use different hosts (e.g. `smtp.zoho.eu`). Always match what Zoho shows in your UI.

This app uses **implicit SSL** (`SMTP_SSL`) on port **465** by default. If you use port **587**, it connects with **STARTTLS** automatically.

## Authentication

- Use the **full mailbox address** as the SMTP username (same as `ZOHO_MAIL_ADDRESS`). A mismatch often causes **Relaying disallowed**.
- If **two-factor authentication** is enabled, create an [application-specific password](https://www.zoho.com/mail/help/adminconsole/two-factor-authentication.html#alink5) and use it as `ZOHO_MAIL_PASSWORD`.

## Environment variables

Set these in `.env` (see keys below). Optional values tune SMTP:

| Variable | Required | Description |
|----------|----------|-------------|
| `ZOHO_MAIL_ADDRESS` | Yes (for sending) | Sender login and `From` address |
| `ZOHO_MAIL_PASSWORD` | Yes (for sending) | Mailbox password or app-specific password |
| `ZOHO_SMTP_HOST` | No | Default `smtp.zoho.com` |
| `ZOHO_SMTP_PORT` | No | Default `465` (SSL). Use `587` for STARTTLS |
| `ZOHO_MAIL_REPLY_TO` | No | `Reply-To` header (defaults to `ZOHO_MAIL_ADDRESS`) |
| `PETFOLIO_UNSUBSCRIBE_URL` | No | URL for list unsubscribe header and template link |

If `ZOHO_MAIL_ADDRESS` or `ZOHO_MAIL_PASSWORD` is unset, thank-you emails are **skipped** and a warning is logged; the API response is still successful after Supabase insert.

## Install and run

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Submit the waitlist form and watch the terminal logs for send success or SMTP errors.

## Email content

- Template: `templates/email/thank_you.html` (HTML part).
- A **plain-text** part is generated in code for better client compatibility.
- Customize branding, links, and copy in the HTML template. Optional: align `PETFOLIO_UNSUBSCRIBE_URL` with a real unsubscribe endpoint before promising one-click unsubscribe in marketing channels.

## Troubleshooting

- **Authentication failure**: Wrong password, need app password with 2FA, or wrong datacenter host.
- **Relaying disallowed**: `From` must match the authenticated mailbox or an allowed alias.
- **Connection errors**: Confirm firewall allows outbound **465** or **587**. Try **587** if **465** is blocked.
- **Duplicate messages in Sent**: See Zoho’s note about disabling duplicate “save to Sent” for SMTP clients in [SMTP help](https://www.zoho.com/mail/help/zoho-smtp.html).

## Limits

Sending limits are dynamic (often assessed over rolling windows). Very large bursts may be throttled; monitor logs and consider queues if volume grows.

## Related files

- `app.py` — `send_thank_you_email`, SMTP configuration
- `requirements.txt` — Python dependencies
