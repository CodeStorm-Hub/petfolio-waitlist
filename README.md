# petfolio-waitlist

PetFolio landing page and waitlist (Flask + Supabase + Zoho SMTP).

## Local development

See [QUICK_START.md](QUICK_START.md) and [EMAIL_SETUP.md](EMAIL_SETUP.md).

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Configure `.env` (gitignored); copy from `.env.example`.
python app.py
```

## Deploy on Vercel

This repo uses [`app.py`](app.py) with a Flask instance named `app`, which [Vercel detects automatically](https://vercel.com/docs/frameworks/backend/flask).

### Prerequisites

- Install/use CLI (minimum **48.2.10**): `npx vercel@latest --version`
- Authenticate once (opens browser/device flow): `npx vercel@latest login`
- Link the repo directory to a Vercel project: `npx vercel@latest link`

### Environment variables (never commit values)

Configure secrets in the [Vercel project settings](https://vercel.com/docs/environment-variables) (and/or `vercel env add <NAME>`) for **Production** and **Preview** at minimum:

| Name | Purpose |
|------|---------|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon JWT (server-side only in this app) |
| `ZOHO_MAIL_ADDRESS` | SMTP login / From |
| `ZOHO_MAIL_PASSWORD` | Mailbox or Zoho app-specific password |
| `ZOHO_SMTP_HOST` | Optional; default `smtp.zoho.com` in code |
| `ZOHO_SMTP_PORT` | Optional; default `465` |
| `ZOHO_MAIL_REPLY_TO` | Optional |
| `PETFOLIO_UNSUBSCRIBE_URL` | Optional unsubscribe URL |

To mirror Dashboard vars locally without committing secrets, use **`vercel env pull .env.local`** after linking (writes `.env.local`, covered by `.gitignore`). Flask does not load `.env.local` automatically—either merge needed keys into your local `.env` or export them before `python app.py`.

### Commands

```bash
# Preview deployment (safe default)
npx vercel@latest deploy

# Production (only after env vars are set and you intend to go live)
npx vercel@latest deploy --prod
```

Connect the Git **`main`** branch in the Vercel dashboard for continuous deployments from `main` after the first successful link.
