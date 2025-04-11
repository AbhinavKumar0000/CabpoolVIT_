import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config


def send_email(recipient_email, subject, message_html):
    """Helper function to send emails"""
    try:
        if not Config.SMTP_USERNAME or not Config.SMTP_PASSWORD:
            print("Email credentials not configured, skipping email")
            return False

        msg = MIMEMultipart('alternative')
        msg['From'] = Config.SMTP_USERNAME
        msg['To'] = recipient_email
        msg['Subject'] = subject

        html_part = MIMEText(message_html, 'html')
        msg.attach(html_part)

        server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
        server.starttls()
        server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()

        print(f"Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False
