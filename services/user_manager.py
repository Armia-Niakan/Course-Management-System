import os
import json
import datetime
from typing import Dict, Optional
from werkzeug.security import generate_password_hash
from flask import current_app

from app.models.user import User


class UserManager:
    @staticmethod
    def load_users() -> Dict[str, User]:
        path = current_app.config['USER_DATA_FILE']
        try:
            with open(path, 'r') as f:
                users_data = json.load(f)
                users = {email: User.from_dict(data) for email, data in users_data.items()}
                if not any(user.role == 'admin' for user in users.values()):
                    default_admin = UserManager.create_default_admin()
                    users[default_admin.email] = default_admin
                    UserManager.save_users(users)
                    current_app.logger.info("Created default admin user")
                return users
        except (FileNotFoundError, json.JSONDecodeError):
            default_admin = UserManager.create_default_admin()
            users = {default_admin.email: default_admin}
            UserManager.save_users(users)
            current_app.logger.info("Created new user file with default admin")
            return users
        
    @staticmethod
    def create_default_admin() -> User:
        email = os.getenv('DEFAULT_ADMIN_EMAIL', 'admin@example.com')
        username = os.getenv('DEFAULT_ADMIN_USERNAME', 'admin')
        password = os.getenv('DEFAULT_ADMIN_PASSWORD', '123456789')

        if not all([email, username, password]):
            current_app.logger.warning(
                "Missing one or more default admin environment variables. "
                "Using fallback credentials."
            )
            email = 'admin@example.com'
            username = 'admin'
            password = '123456789'

        return User(
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            role='admin',
            created_at=str(datetime.datetime.now())
        )
    
    @staticmethod
    def save_users(users: Dict[str, User]):
        path = current_app.config['USER_DATA_FILE']
        users_data = {email: user.to_dict() for email, user in users.items()}
        with open(path, 'w') as f:
            json.dump(users_data, f, indent=4)

    @staticmethod
    def get_user(email: str) -> Optional[User]:
        return UserManager.load_users().get(email)

    @staticmethod
    def add_user(user: User):
        users = UserManager.load_users()
        users[user.email] = user
        UserManager.save_users(users)

    @staticmethod
    def update_user(email: str, **kwargs) -> bool:
        users = UserManager.load_users()
        if email not in users:
            return False
        user = users[email]
        allowed_fields = {'username', 'password_hash'}
        updated = False
        for key, value in kwargs.items():
            if key in allowed_fields and hasattr(user, key):
                setattr(user, key, value)
                updated = True
        if updated:
            UserManager.save_users(users)
        return updated

    @staticmethod
    def delete_user(email: str) -> bool:
        users = UserManager.load_users()
        if email in users:
            del users[email]
            UserManager.save_users(users)
            return True
        return False

    @staticmethod
    def email_exists(email: str) -> bool:
        return email in UserManager.load_users()
