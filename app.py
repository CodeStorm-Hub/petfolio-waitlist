import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from email_validator import EmailNotValidError, validate_email
from flask import Flask, jsonify, render_template, request
from jinja2 import Template
from supabase import Client, create_client

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global mock waitlist for development/preview when Supabase is not configured
mock_waitlist = []

# Try to initialize Supabase; fallback to Mock mode if not configured or credentials are placeholders
supabase = None
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or "your-project-ref" in supabase_url or not supabase_key or "your_supabase_anon_jwt" in supabase_key:
    logger.warning("Supabase URL or Key is not configured. Running in mock/development mode with in-memory database.")
else:
    try:
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.warning("Failed to initialize Supabase client: %s. Falling back to mock/development mode.", e)


# Zoho Mail SMTP — verify host/port against Mail → Settings → Mail Accounts → Server configuration
ZOHO_MAIL_ADDRESS = os.environ.get("ZOHO_MAIL_ADDRESS")
ZOHO_MAIL_PASSWORD = os.environ.get("ZOHO_MAIL_PASSWORD")
# Personal / free org: smtp.zoho.com; paid org custom domain: often smtppro.zoho.com (see Zoho docs)
ZOHO_SMTP_HOST = os.environ.get("ZOHO_SMTP_HOST", "smtp.zoho.com")
ZOHO_SMTP_PORT = int(os.environ.get("ZOHO_SMTP_PORT", "465"))
ZOHO_MAIL_REPLY_TO = os.environ.get("ZOHO_MAIL_REPLY_TO")
DEFAULT_UNSUBSCRIBE_URL = os.environ.get(
    "PETFOLIO_UNSUBSCRIBE_URL", "https://petfolio.social/unsubscribe"
)


def _smtp_send(mail_from: str, mail_to: str, message: str) -> None:
    """Send raw message via Zoho-compatible SMTP (SSL on 465 or STARTTLS on 587)."""
    if ZOHO_SMTP_PORT == 587:
        with smtplib.SMTP(ZOHO_SMTP_HOST, ZOHO_SMTP_PORT, timeout=60) as server:
            server.starttls()
            server.login(ZOHO_MAIL_ADDRESS, ZOHO_MAIL_PASSWORD)
            server.sendmail(mail_from, mail_to, message)
    else:
        with smtplib.SMTP_SSL(ZOHO_SMTP_HOST, ZOHO_SMTP_PORT, timeout=60) as server:
            server.login(ZOHO_MAIL_ADDRESS, ZOHO_MAIL_PASSWORD)
            server.sendmail(mail_from, mail_to, message)


def send_thank_you_email(name: str, email: str, pet_kind: str, pet_count: str) -> bool:
    """
    Send a personalized thank-you email via Zoho SMTP.
    Failures are logged and do not affect signup success.
    """
    if not ZOHO_MAIL_ADDRESS or not ZOHO_MAIL_PASSWORD:
        logger.warning(
            "Skipping thank-you email (missing ZOHO_MAIL_ADDRESS or ZOHO_MAIL_PASSWORD)"
        )
        return False

    unsubscribe_url = DEFAULT_UNSUBSCRIBE_URL
    try:
        with app.open_resource("templates/email/thank_you.html") as f:
            email_template = f.read().decode("utf-8")

        template = Template(email_template)
        html_content = template.render(
            name=name or "there",
            pet_kind=pet_kind,
            pet_count=pet_count,
            unsubscribe_url=unsubscribe_url,
        )

        plain_lines = [
            f"Hey {name or 'there'}!",
            "",
            "Welcome to the PetFolio beta waitlist. We're thrilled you're here.",
            "",
            "Your pet profile:",
            f"  Pet type: {pet_kind}",
            f"  Number of pets: {pet_count}",
            "",
            "What's next: we'll invite beta testers in waves and notify you when it's your turn.",
            "",
            f"Visit https://petfolio.social",
            "",
            f"Unsubscribe: {unsubscribe_url}",
            "",
            "— The PetFolio Team",
        ]
        plain_body = "\n".join(plain_lines)

        message = MIMEMultipart("alternative")
        message["Subject"] = "🐾 Welcome to PetFolio! You're In! 🐾"
        message["From"] = ZOHO_MAIL_ADDRESS
        message["To"] = email
        message["MIME-Version"] = "1.0"
        reply_to = ZOHO_MAIL_REPLY_TO or ZOHO_MAIL_ADDRESS
        message["Reply-To"] = reply_to
        message["List-Unsubscribe"] = f"<{unsubscribe_url}>"

        message.attach(MIMEText(plain_body, "plain", "utf-8"))
        message.attach(MIMEText(html_content, "html", "utf-8"))

        _smtp_send(ZOHO_MAIL_ADDRESS, email, message.as_string())
        logger.info("Thank-you email sent successfully to %s", email)
        return True
    except smtplib.SMTPException as e:
        logger.warning(
            "Failed to send thank-you email to %s: SMTP error %s: %s",
            email,
            type(e).__name__,
            e,
        )
        return False
    except OSError as e:
        logger.warning(
            "Failed to send thank-you email to %s: network/OS error %s: %s",
            email,
            type(e).__name__,
            e,
        )
        return False
    except Exception as e:
        logger.warning(
            "Failed to send thank-you email to %s: %s: %s",
            email,
            type(e).__name__,
            e,
        )
        return False


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/join", methods=["POST"])
def join_waitlist():
    data = request.json
    try:
        try:
            valid_email = validate_email(data.get("email", ""), check_deliverability=False)
            normalized_email = valid_email.normalized
        except EmailNotValidError as e:
            return jsonify({"success": False, "message": str(e)}), 400

        pet_kind_val = data.get("pet_type")
        if not pet_kind_val:
            pet_kind_val = "Not specified"

        pet_count_val = data.get("pet_count")
        if not pet_count_val:
            pet_count_val = "1"

        signup_data = {
            "name": data.get("name"),
            "email": normalized_email,
            "pet_kind": pet_kind_val,
            "pet_count": pet_count_val,
        }

        if supabase:
            supabase.table("waitlist").insert(signup_data).execute()
        else:
            # Check for duplicate email in mock waitlist
            if any(item["email"] == normalized_email for item in mock_waitlist):
                raise ValueError("unique constraint")
            mock_waitlist.append(signup_data)

        send_thank_you_email(
            name=data.get("name"),
            email=normalized_email,
            pet_kind=pet_kind_val,
            pet_count=pet_count_val,
        )

        if supabase:
            count_result = supabase.table("waitlist").select("id", count="exact").execute()
            position = count_result.count or 0
        else:
            position = len(mock_waitlist)

        return jsonify(
            {"success": True, "position": position, "total_signups": position}
        )

    except Exception as e:
        error_msg = str(e)
        logger.exception("Signup error: %s", error_msg)

        user_message = "Something went wrong. Please try again."
        if "waitlist_email_format_check" in error_msg:
            user_message = (
                "Supabase is rejecting your email due to the 'waitlist_email_format_check' rule. "
                "Please run the SQL command in your dashboard to remove this rule."
            )
        elif "23505" in error_msg or "unique constraint" in error_msg.lower():
            user_message = "This email is already on the waitlist!"

        return jsonify({"success": False, "message": user_message}), 500


@app.route("/api/stats", methods=["GET"])
def get_stats():
    try:
        if supabase:
            count_result = supabase.table("waitlist").select("id", count="exact").execute()
            total_signups = count_result.count or 0
        else:
            total_signups = len(mock_waitlist)
        return jsonify({"success": True, "total_signups": total_signups})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/todos")
def index():
    try:
        if supabase:
            response = supabase.table("todos").select("*").execute()
            todos = response.data
        else:
            todos = [
                {"name": "[Development Mock Mode] Setup real Supabase credentials in your .env file to enable persistent storage!"},
                {"name": "Check out the gorgeous landing page at the root route!"}
            ]

        html = "<h1>Todos</h1><ul>"
        for todo in todos:
            html += f'<li>{todo["name"]}</li>'
        html += "</ul>"
        html += '<br><a href="/">Back to Landing Page</a>'
        return html
    except Exception as e:
        return f"Error connecting to Supabase: {str(e)}"


if __name__ == "__main__":
    app.run(debug=True)
