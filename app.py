import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
from email_validator import validate_email, EmailNotValidError
from jinja2 import Template

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Initialize Supabase client
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY")
)

# Zoho Mail configuration
ZOHO_MAIL_ADDRESS = os.environ.get("ZOHO_MAIL_ADDRESS")
ZOHO_MAIL_PASSWORD = os.environ.get("ZOHO_MAIL_PASSWORD")
ZOHO_SMTP_HOST = os.environ.get("ZOHO_SMTP_HOST", "smtp.zohomail.com")
ZOHO_SMTP_PORT = int(os.environ.get("ZOHO_SMTP_PORT", "465"))

def send_thank_you_email(name: str, email: str, pet_kind: str, pet_count: str):
    """
    Send a personalized thank you email to a new waitlist member via Zoho Mail.
    Gracefully handles failures without blocking signup.
    """
    try:
        # Read and render the email template
        with open('templates/email/thank_you.html', 'r') as f:
            email_template = f.read()
        
        # Render template with variables
        template = Template(email_template)
        html_content = template.render(
            name=name,
            pet_kind=pet_kind,
            pet_count=pet_count,
            unsubscribe_url="https://petfolio.social/unsubscribe"
        )
        
        # Create MIME message
        message = MIMEMultipart("alternative")
        message["Subject"] = "🐾 Welcome to PetFolio! You're In! 🐾"
        message["From"] = ZOHO_MAIL_ADDRESS
        message["To"] = email
        
        # Attach HTML content
        message.attach(MIMEText(html_content, "html"))
        
        # Send email via Zoho SMTP
        with smtplib.SMTP_SSL(ZOHO_SMTP_HOST, ZOHO_SMTP_PORT) as server:
            server.login(ZOHO_MAIL_ADDRESS, ZOHO_MAIL_PASSWORD)
            server.sendmail(ZOHO_MAIL_ADDRESS, email, message.as_string())
        
        print(f"✅ Thank you email sent successfully to {email}")
        return True
    except Exception as e:
        # Log error but don't fail the signup
        print(f"⚠️  Failed to send thank you email to {email}: {str(e)}")
        return False

@app.route('/')
def home():
    # Main PetFolio landing page
    return render_template('index.html')

@app.route('/api/join', methods=['POST'])
def join_waitlist():
    data = request.json
    try:
        # Validate email using the open-source library
        try:
            valid_email = validate_email(data.get("email", ""), check_deliverability=False)
            normalized_email = valid_email.normalized
        except EmailNotValidError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        # 1. Define the full data set, ensuring no null values for required columns
        pet_kind_val = data.get("pet_type")
        if not pet_kind_val:
            pet_kind_val = "Not specified"
            
        pet_count_val = data.get("pet_count")
        if not pet_count_val:
            pet_count_val = "1"  # Default to 1 if not provided

        signup_data = {
            "name": data.get("name"),
            "email": normalized_email,
            "pet_kind": pet_kind_val,
            "pet_count": pet_count_val
        }

        # Try to save everything
        supabase.table('waitlist').insert(signup_data).execute()

        # Send thank you email (non-blocking)
        send_thank_you_email(
            name=data.get("name"),
            email=normalized_email,
            pet_kind=pet_kind_val,
            pet_count=pet_count_val
        )

        # 2. Get the total count of signups to determine the "spot in line"
        count_result = supabase.table('waitlist').select("id", count="exact").execute()
        position = count_result.count or 0

        return jsonify({
            "success": True, 
            "position": position,
            "total_signups": position
        })

    except Exception as e:
        error_msg = str(e)
        print(f"!!! Signup error details: {error_msg}")
        
        # User-friendly error messages
        user_message = "Something went wrong. Please try again."
        if "waitlist_email_format_check" in error_msg:
            user_message = "Supabase is rejecting your email due to the 'waitlist_email_format_check' rule. Please run the SQL command in your dashboard to remove this rule."
        elif "23505" in error_msg or "unique constraint" in error_msg.lower():
            user_message = "This email is already on the waitlist!"

        return jsonify({
            "success": False, 
            "message": user_message
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        # Get the total count of signups
        count_result = supabase.table('waitlist').select("id", count="exact").execute()
        return jsonify({
            "success": True, 
            "total_signups": count_result.count or 0
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/todos')
def index():
    # Existing test route
    try:
        response = supabase.table('todos').select("*").execute()
        todos = response.data

        html = '<h1>Todos</h1><ul>'
        for todo in todos:
            html += f'<li>{todo["name"]}</li>'
        html += '</ul>'
        html += '<br><a href="/">Back to Landing Page</a>'
        return html
    except Exception as e:
        return f"Error connecting to Supabase: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
