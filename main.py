import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import uvicorn

load_dotenv()

SENDER_EMAIL = os.environ.get('GMAIL_USER')
SENDER_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD')
RECEIVER_EMAIL = os.environ.get('SENDING_MAIL')

# Check if credentials are set
if not SENDER_EMAIL or not SENDER_PASSWORD:
    print("Error: GMAIL_USER and GMAIL_APP_PASSWORD environment variables not set.")
    print("Please set them before running the server.")

# --- FASTAPI APP SETUP ---
app = FastAPI(title="Portfolio Contact API", version="1.0.0")

# CORS Configuration
# For local testing, allow all origins
# For production, replace ["*"] with ["https://your-portfolio-domain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains in production
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# --- THE CONTACT ENDPOINT ---
@app.post('/contact')
async def handle_contact_form(
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    """
    Handle contact form submissions from portfolio website.
    
    - **name**: Sender's name
    - **email**: Sender's email address
    - **message**: Message content
    """
    
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="Server error: Email credentials not configured."
        )
    
    try:
        print(f"Received form submission:\nName: {name}\nEmail: {email}")
        
        # Validation (Basic)
        if not name.strip() or not email.strip() or not message.strip():
            raise HTTPException(
                status_code=400,
                detail="Missing required fields."
            )
        
        # Setup Email Content
        msg = MIMEMultipart()
        msg['From'] = f"Portfolio Alert <{SENDER_EMAIL}>"
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = f"New work call from {name}"
        
        # Reply-To header for easy responses
        msg.add_header('Reply-To', email)
        
        body = f'''
You received a new message from your portfolio:

Name: {name}
Email: {email}

Message:
{message}
'''
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send the Email (using Gmail's SMTP server)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        
        print("Message sent successfully!")
        
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Message sent successfully!"}
        )
        
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Server error: Could not send email."
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected server error occurred."
        )

# Health check endpoint
@app.get('/')
async def root():
    """Root endpoint for health checks"""
    return {"status": "ok", "message": "Portfolio Contact API is running"}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",  # Change "main" to your filename if different
        host="0.0.0.0",
        port=port,
        reload=True  # Auto-reload on code changes (disable in production)
    )
