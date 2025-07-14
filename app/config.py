import os

class Config:
    SECRET_KEY = os.urandom(24)
    
    COURSES_FILE = 'data/courses.json'
    ENROLLMENTS_FILE = 'data/enrollments.json'
    USER_DATA_FILE = 'data/users.json'
    TOKEN_DATA_FILE = 'data/reset_tokens.json'
    LOG_FILE = 'app.log'

    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    EMAIL_ADDRESS = 'coursemanagementsystem1403@gmail.com'
    EMAIL_PASSWORD = 'natm cmet bspn gvci'
    APP_URL = 'http://localhost:5000'

    VALID_ROLES = {"student", "teacher", "admin"}
