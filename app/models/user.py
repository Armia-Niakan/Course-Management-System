from dataclasses import dataclass, asdict
from typing import Dict
from werkzeug.security import check_password_hash
from flask import current_app


@dataclass
class User:
    email: str
    username: str
    password_hash: str
    role: str
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict):
        if not all(k in data for k in ("email", "username", "password_hash", "role", "created_at")):
            raise ValueError("Missing required fields")
        
        if data["role"] not in current_app.config['VALID_ROLES']:
            raise ValueError(f"Invalid role. Must be one of: {current_app.config['VALID_ROLES']}")        

        return cls(
            email=data['email'],
            username=data['username'],
            password_hash=data['password_hash'],
            role=data['role'],
            created_at=data['created_at'],
        )
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def verify_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
