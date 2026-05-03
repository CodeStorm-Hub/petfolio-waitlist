# PetFolio Email Setup Guide

## Overview
Your PetFolio waitlist app now sends personalized thank-you emails to new signups! Emails are sent immediately after someone joins and include:
- Personalized greeting with their name
- Pet profile details they provided
- "What's next?" timeline
- Links to follow PetFolio on social media
- Modern UI matching PetFolio's brand colors (blue & coral)

## Setup Steps

### 1. Get a Resend Account
- Go to [resend.com](https://resend.com) and sign up (free tier available)
- Verify your email address
- Navigate to **API Keys** in the dashboard
- Copy your API key

### 2. Verify Your Sender Email
In Resend:
- Go to **Domains** or **From Addresses**
- Add `welcome@petfolio.social` (or your preferred sender email)
- **Sandbox mode**: You can skip verification and send test emails right away
- **Production**: You'll need to verify the domain via DNS records

### 3. Update Your `.env` File
Copy `.env.example` to `.env` and add:
```bash
RESEND_API_KEY=your_actual_api_key_here
```

### 4. Install Dependencies
Dependencies are already in `requirements.txt`, but make sure they're installed:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 5. Test It Out
1. Start your Flask app: `python app.py`
2. Go to your waitlist form and sign up with a test email
3. Check the inbox for the thank-you email
4. You'll see a success message in the terminal: `✅ Thank you email sent successfully to...`

## Email Template Customization

The email template is in `templates/email/thank_you.html`. To customize:
- **Brand colors**: Search for hex codes (#2979FF, #5BA3F5, etc.)
- **Social links**: Update Twitter, Instagram, Discord URLs
- **Company info**: Change "The PetFolio Team" to your actual team name
- **Links**: Update `https://petfolio.social` to your actual domain

### Template Variables Available
- `{{ name }}` - User's name
- `{{ pet_kind }}` - Type of pet (Dog, Cat, etc.)
- `{{ pet_count }}` - Number of pets
- `{{ unsubscribe_url }}` - Link to unsubscribe (configure in `app.py`)

## Error Handling
- ✅ Emails won't break user signups if they fail to send
- ⚠️ Failed email attempts are logged to the terminal
- All email errors are gracefully handled

## Troubleshooting

**"Import 'resend' could not be resolved"**
- Make sure virtual environment is activated
- Run: `pip install resend`

**Email not sending in production**
- Verify your sender email is verified in Resend dashboard
- Check API key is correctly set in `.env`
- Check Resend dashboard for delivery logs

**Template rendering errors**
- Make sure `templates/email/thank_you.html` file exists
- Verify file path in `send_thank_you_email()` function matches your setup

## Next Steps

### Scale Up Emails
When you're ready to send more complex emails:
- Use Resend's template feature for pre-built templates
- Add multiple email types (signup, beta access notification, etc.)
- Create a background task queue (Celery/RQ) to handle email batches

### Advanced Features
- Track email opens and clicks in Resend dashboard
- Create email sequences (welcome → education → CTA)
- A/B test different email subject lines
- Add webhook handlers for email bounces/complaints

### Production Checklist
- [ ] Verify sender domain in Resend (not just sandbox)
- [ ] Test emails on mobile devices
- [ ] Add unsubscribe link logic to your backend
- [ ] Monitor Resend dashboard for bounce/complaint rates
- [ ] Consider rate limiting for email sends

## Files Modified
- `app.py` - Added Resend initialization and email sending function
- `requirements.txt` - Added `resend==2.1.0`
- `templates/email/thank_you.html` - Modern HTML email template (NEW)
- `.env.example` - Template for environment variables (NEW)

---

Need help? Check Resend documentation: https://resend.com/docs
