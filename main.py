import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv


load_dotenv()

SENDER_EMAIL = os.environ.get('GMAIL_USER')
SENDER_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')

RECEIVER_EMAIL = os.environ.get('SENDING_MAIL')

# Check if credentials are set
if not SENDER_EMAIL or not SENDER_PASSWORD:
    print("Error: GMAIL_USER and GMAIL_APP_PASSWORD environment variables not set.")
    print("Please set them before running the server.")


# --- FLASK APP SETUP ---

app = Flask(__name__)

# Use CORS to allow your portfolio (on a different domain) to send requests here.
# For local testing, '*' is fine.
# For production, lock it down:
# CORS(app, resources={r"/contact": {"origins": "https://your-portfolio-domain.com"}})
CORS(app, resources={r"/contact": {"origins": "*"}})


# --- THE CONTACT ENDPOINT ---
# This must match the URL in your HTML file's "form-endpoint"
@app.route('/contact', methods=['POST'])
def handle_contact_form():
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        return jsonify({"success": False, "message": "Server error: Email credentials not configured."}), 500

    try:
        # Get data from the form (sent by your 'fetch' script)
        # The JS script sends FormData, which Flask parses into 'request.form'
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')

        print(f"Received form submission:\nName: {name}\nEmail: {email}")

        # 1. Validation (Basic)
        if not name or not email or not message:
            return jsonify({"success": False, "message": "Missing required fields."}), 400

        # 2. Setup Email Content
        msg = MIMEMultipart()
        msg['From'] = f"Portfolio Alert <{SENDER_EMAIL}>"
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"New work call from {name}"

        # This 'Reply-To' header is very useful!
        msg.add_header('Reply-To', email)

        body =f'''
        You received a new message from your portfolio:

        Name: {name}
        Email: {email}

        Message:
        {message}'''

        # --- THIS IS THE FIX ---
        # This line is now *outside* the f-string block
        msg.attach(MIMEText(body, 'plain'))

        # 3. Send the Email (using Gmail's SMTP server)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

        print("Message sent successfully!")

        # Send a success response back to the frontend
        return jsonify({"success": True, "message": "Message sent successfully!"}), 200

    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
        return jsonify({"success": False, "message": "Server error: Could not send email."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"success": False, "message": "An unexpected server error occurred."}), 500


if __name__ == '__main__':

    app.run(debug=True)
