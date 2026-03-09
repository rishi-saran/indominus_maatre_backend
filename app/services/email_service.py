# /app/services/email_service.py

import smtplib
from email.mime.text import MIMEText
from app.core.config import settings


class EmailService:
    @staticmethod
    def send_html_email(
        to_email: str,
        subject: str,
        html_body: str
    ):
        msg = MIMEText(html_body, "html")
        msg["Subject"] = subject
        msg["From"] = settings.SES_FROM_EMAIL
        msg["To"] = to_email

        with smtplib.SMTP(
            settings.SES_SMTP_HOST,
            settings.SES_SMTP_PORT
        ) as server:
            server.starttls()
            server.login(
                settings.SES_SMTP_USERNAME,
                settings.SES_SMTP_PASSWORD
            )
            server.sendmail(
                settings.SES_FROM_EMAIL,
                [to_email],
                msg.as_string()
            )