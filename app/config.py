import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
    
    COURSES_FILE = 'data/courses.json'
    ENROLLMENTS_FILE = 'data/enrollments.json'
    USER_DATA_FILE = 'data/users.json'
    TOKEN_DATA_FILE = 'data/reset_tokens.json'
    LOG_FILE = 'app.log'

    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    APP_URL = 'http://localhost:5000'

    VALID_ROLES = {"student", "teacher", "admin"}
