from app import db
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash

class UserRole(Enum):
    ADMIN = 'ADMIN'
    USER = 'USER'

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='User ID')
    username = db.Column(db.String(50), unique=True, nullable=False, comment='Username')
    password_hash = db.Column(db.String(255), nullable=False, comment='Password hash')
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.USER, comment='User role')
    
    # Relationships
    operation_logs = db.relationship('OperationLog', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role.value
        } 