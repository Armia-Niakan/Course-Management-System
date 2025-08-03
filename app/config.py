import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24))
    
    COURSES_FILE = 'data/courses.json'
    ENROLLMENTS_FILE = 'data/enrollments.json'
    USER_DATA_FILE = 'data/users.json'
    DATA_FOLDER = os.path.join(basedir, '..', 'data')
    TOKEN_DATA_FILE = 'data/reset_tokens.json'
    LOG_FILE = 'app.log'
    EXAMS_FILE = 'data/exams.json'
    SUBMISSIONS_FILE = 'data/submissions.json'

    UPLOAD_FOLDER = os.path.join(basedir, '..', 'uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'mp4', 'mov', 'avi', 'mkv', 'jpg', 'png', 'mp3', 'wav'}
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024

    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    APP_URL = 'http://localhost:5000'

    VALID_ROLES = {"student", "teacher", "admin"}
