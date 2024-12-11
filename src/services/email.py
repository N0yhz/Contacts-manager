"""
Email Service Module

This module provides functionality for sending verification and password reset emails.

Dependencies:
    - os: For environment variable access
    - logging: For logging information and errors
    - dotenv: For loading environment variables
    - pydantic: For email validation
    - fastapi_mail: For email sending functionality
    - jinja2: For email template rendering

Functions:
    - validate_email_config: Validate required email configuration variables
    - send_verification_email: Send a verification email to a user
    - send_password_reset_email: Send a password reset email to a user

Configuration:
    - Loads email configuration from environment variables
    - Sets up Jinja2 environment for email templates

"""
import os 
import logging
from dotenv import load_dotenv

from pydantic import EmailStr
from fastapi_mail import FastMail, MessageType, MessageSchema, ConnectionConfig
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)
load_dotenv()


def validate_email_config():
    """
    Validate that all required email configuration variables are set.

    :raises ValueError: If any required configuration variable is missing
    
    """
    required_vars = [
        "MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_FROM",
        "MAIL_PORT", "MAIL_SERVER", "MAIL_FROM_NAME"
    ]

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            raise ValueError(f"Missing required email configuration: {var}")
        logger.info(f"{var} is set")

    logger.info("All required email configuration variables are set")

try:
    validate_email_config()
    mail_conf = ConnectionConfig(
        MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
        MAIL_FROM = os.getenv("MAIL_FROM"),
        MAIL_SERVER = os.getenv("MAIL_SERVER"),
        MAIL_PORT = int(os.getenv("MAIL_PORT", 587)),
        MAIL_FROM_NAME= os.getenv("MAIL_FROM_NAME"),
        MAIL_STARTTLS = True,
        MAIL_SSL_TLS = False,
        USE_CREDENTIALS = True,
        VALIDATE_CERTS = True,
    )
    logger.info("Email configuration loaded successfully")
except Exception as e:
    logger.error(f"Error in email configuration: {str(e)}")
    raise

template_dir = os.path.join(os.path.dirname(__file__), "templates")
jinja_env = Environment(loader=FileSystemLoader(template_dir))

async def send_verification_email(email: EmailStr, token: str):
    """
    Send a verification email to the user.

    :param email: The recipient's email address
    :type email: EmailStr
    :param token: The verification token
    :type token: str
    :raises Exception: If there's an error sending the email
    
    """
    try:
        logger.info(f"Attemping to send verification email to {email}")

        template = jinja_env.get_template("verify_email.html")
        verification_link = f"http://localhost:8000/api/auth/verify/{token}"
        html_content = template.render(verification_link=verification_link)

        message = MessageSchema(
            subject="Verify your email for Contact manager",
            recipients=[email],
            body= html_content,
            subtype= MessageType.html
        )

        fm = FastMail(mail_conf)
        await fm.send_message(message)
        logger.info(f"Verification email sent successfully to {email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {str(e)}")
        raise

async def send_password_reset_email(email: EmailStr, token: str):
    """
    Send a password reset email to the user.

    :param email: The recipient's email address
    :type email: EmailStr
    :param token: The password reset token
    :type token: str
    :raises Exception: If there's an error sending the email
    
    """
    try:
        logger.info(f"Attemping to send password reset email to {email}")

        template = jinja_env.get_template("password_reset_email.html")
        reset_link = f"http://localhost:8000/api/auth/reset-password/{token}"
        html_content = template.render(reset_link=reset_link)

        message = MessageSchema(
            subject="Reset your password for Contact manager",
            recipients=[email],
            body= html_content,
            subtype= MessageType.html
        )

        fm = FastMail(mail_conf)
        await fm.send_message(message)
        logger.info(f"Password reset email sent successfully to {email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        raise