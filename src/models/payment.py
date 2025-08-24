from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    
    method_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)  # Account details, phone number, etc.
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    # transactions = db.relationship('PaymentTransaction', backref='payment_method', lazy=True)
    
    def to_dict(self):
        return {
            'method_id': self.method_id,
            'name': self.name,
            'details': self.details,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<PaymentMethod {self.name}>'

class PaymentTransaction(db.Model):
    __tablename__ = 'payment_transactions'
    
    transaction_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.method_id'), nullable=False)
    status = db.Column(db.String(20), default='معلق')  # 'معلق', 'مكتمل', 'مرفوض'
    proof_image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'amount': self.amount,
            'method_id': self.method_id,
            'status': self.status,
            'proof_image_url': self.proof_image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<PaymentTransaction {self.transaction_id}>'

