from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    notification_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # NULL for global notifications
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Notification {self.title}>'

class AppSettings(db.Model):
    __tablename__ = 'app_settings'
    
    setting_id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'setting_id': self.setting_id,
            'key': self.key,
            'value': self.value
        }
    
    def __repr__(self):
        return f'<AppSettings {self.key}>'

class TelegramSettings(db.Model):
    __tablename__ = 'telegram_settings'
    
    setting_id = db.Column(db.Integer, primary_key=True)
    bot_token = db.Column(db.String(255))
    chat_id = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'setting_id': self.setting_id,
            'bot_token': self.bot_token,
            'chat_id': self.chat_id,
            'is_active': self.is_active
        }
    
    def __repr__(self):
        return f'<TelegramSettings {self.setting_id}>'

class AnimatedAsset(db.Model):
    __tablename__ = 'animated_assets'
    
    asset_id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'صورة', 'نص'
    content = db.Column(db.Text, nullable=False)  # URL or text content
    location = db.Column(db.String(100), nullable=False)  # Location in app
    is_active = db.Column(db.Boolean, default=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'asset_id': self.asset_id,
            'type': self.type,
            'content': self.content,
            'location': self.location,
            'is_active': self.is_active,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None
        }
    
    def __repr__(self):
        return f'<AnimatedAsset {self.type}>'

