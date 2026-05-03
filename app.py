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

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_KEY"),
)

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

        supabase.table("waitlist").insert(signup_data).execute()

        send_thank_you_email(
            name=data.get("name"),
            email=normalized_email,
            pet_kind=pet_kind_val,
            pet_count=pet_count_val,
        )

        count_result = supabase.table("waitlist").select("id", count="exact").execute()
        position = count_result.count or 0

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
        count_result = supabase.table("waitlist").select("id", count="exact").execute()
        return jsonify({"success": True, "total_signups": count_result.count or 0})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/todos")
def index():
    try:
        response = supabase.table("todos").select("*").execute()
        todos = response.data

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
