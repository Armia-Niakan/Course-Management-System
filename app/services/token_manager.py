import json
import secrets
import datetime
from typing import Optional, Tuple
from flask import current_app


class TokenManager:
    @staticmethod
    def load_tokens():
        path = current_app.config['TOKEN_DATA_FILE']
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @staticmethod
    def save_tokens(tokens):
        path = current_app.config['TOKEN_DATA_FILE']
        with open(path, 'w') as f:
            json.dump(tokens, f, indent=4)

    @staticmethod
    def generate_token(email: str) -> str:
        token = secrets.token_urlsafe(32)
        tokens = TokenManager.load_tokens()
        tokens[token] = {
            'email': email,
            'created_at': datetime.datetime.now().isoformat(),
            'expires_at': (datetime.datetime.now() + datetime.timedelta(hours=1)).isoformat()
        }
        TokenManager.save_tokens(tokens)
        return token

    @staticmethod
    def validate_token(token: str) -> Tuple[bool, Optional[str]]:
        tokens = TokenManager.load_tokens()
        if token not in tokens:
            return False, None
        token_data = tokens[token]
        expires = datetime.datetime.fromisoformat(token_data['expires_at'])
        if datetime.datetime.now() > expires:
            del tokens[token]
            TokenManager.save_tokens(tokens)
            return False, None
        return True, token_data['email']

    @staticmethod
    def delete_token(token: str):
        tokens = TokenManager.load_tokens()
        if token in tokens:
            del tokens[token]
            TokenManager.save_tokens(tokens)
