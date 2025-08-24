from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    vip_level = db.Column(db.Integer, default=1)
    total_spent = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='نشط')  # 'نشط', 'محظور'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    # orders = db.relationship('Order', backref='user', lazy=True)
    # payment_transactions = db.relationship('PaymentTransaction', backref='user', lazy=True)
    # notifications = db.relationship('Notification', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'balance': self.balance,
            'vip_level': self.vip_level,
            'total_spent': self.total_spent,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class VIPLevel(db.Model):
    __tablename__ = 'vip_levels'
    
    level_id = db.Column(db.Integer, primary_key=True)
    level_name = db.Column(db.String(50), nullable=False)
    min_spent = db.Column(db.Float, nullable=False)
    discount_percentage = db.Column(db.Float, nullable=False)
    
    def to_dict(self):
        return {
            'level_id': self.level_id,
            'level_name': self.level_name,
            'min_spent': self.min_spent,
            'discount_percentage': self.discount_percentage
        }
    
    def __repr__(self):
        return f'<VIPLevel {self.level_name}>'

