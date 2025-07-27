import datetime
from flask import current_app
import smtplib
from email.mime.text import MIMEText


def datetimeformat(value, format='%B %d, %Y'):
    try:
        dt = datetime.datetime.fromisoformat(value)
        return dt.strftime(format)
    except Exception:
        return value


def send_reset_email(email: str, token: str) -> bool:
    reset_url = f"{current_app.config['APP_URL']}/reset_password/{token}"
    message = MIMEText(
        f"""Hello,

You requested a password reset for your account. Please click the following link to reset your password:
{reset_url}

This link will expire in 1 hour. If you didn't request this, please ignore this email."""
    )
    message['Subject'] = 'Password Reset Request'
    message['From'] = current_app.config['EMAIL_ADDRESS']
    message['To'] = email

    try:
        with smtplib.SMTP(current_app.config['SMTP_SERVER'], current_app.config['SMTP_PORT']) as server:
            server.starttls()
            server.login(current_app.config['EMAIL_ADDRESS'], current_app.config['EMAIL_PASSWORD'])
            server.sendmail(current_app.config['EMAIL_ADDRESS'], email, message.as_string())
        current_app.logger.info(f"Password reset email sent to {email}")
        return True
    except Exception as e:
        current_app.logger.error(f"Error sending password reset email to {email}: {e}")
        return False


def is_time_in_range(time_str: str, time_range: str) -> bool:
    hour = int(time_str.split(':')[0])
    if time_range == 'morning':
        return 8 <= hour < 12
    elif time_range == 'afternoon':
        return 12 <= hour < 17
    elif time_range == 'evening':
        return 17 <= hour < 21
    return False
