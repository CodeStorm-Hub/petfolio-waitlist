# Quick Start: PetFolio Email Integration

## 1️⃣ Get Resend API Key
- Go to [resend.com](https://resend.com) and sign up (free tier available)
- Generate an API key from the dashboard

## 2️⃣ Add API Key to `.env`
```bash
RESEND_API_KEY=your_key_here
```

## 3️⃣ Verify Sender Email
- In Resend dashboard, add `welcome@petfolio.social` (or your preferred sender email)
- **Sandbox mode**: Skip verification, send test emails immediately
- **Production**: Verify domain via DNS

## 4️⃣ Test It
```bash
source venv/bin/activate  # Activate virtual environment
python app.py              # Start Flask app
```

Then fill out the waitlist form → check your email for the thank-you message! 🎉

## What Happens
✅ User signs up on the waitlist  
✅ Data saved to Supabase  
✅ Thank-you email sent automatically with:
- Personalized greeting
- Their pet details
- What to expect next
- Social media links

## Customize
Edit `templates/email/thank_you.html` to:
- Change colors/branding
- Update social media links
- Modify company info
- Add/remove content sections

## Need Help?
See [EMAIL_SETUP.md](EMAIL_SETUP.md) for full documentation and troubleshooting.
