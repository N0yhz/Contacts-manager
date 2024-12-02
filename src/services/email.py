import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pathlib import Path
from pydantic import EmailStr

from src.services.auth import auth_service

mail_conf = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD"),
    MAIL_FROM = os.getenv("MAIL_FROM"),
    MAIL_SERVER = os.getenv("MAIL_SERVER"),
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587)),
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME"),
    MAIL_STARTTLS = os.getenv("MAIL_STARTTLS", "False").lower() == "true",
    MAIL_SSL_TLS = os.getenv("MAIL_SSL_TLS", "True").lower() == "true",
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True,
    TEMPLATE_FOLDER= Path(__file__).parent / 'templates',
)

async def send_verification_email(email: EmailStr, username: str, host: str):
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject = "Verify your email",
            recipients = [email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype = MessageType.html
        )

        fm = FastMail(mail_conf)
        await fm.send_message(message, template_name = "verify_email.html")
    except ConnectionErrors as err:
        print(err)