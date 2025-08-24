from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'
    
    product_id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    currency = db.Column(db.String(10), nullable=False, default='ريال')
    cost_price = db.Column(db.Float, nullable=False)
    sell_price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(255))
    is_available = db.Column(db.Boolean, default=True)
    product_type = db.Column(db.String(50), nullable=False, default='بدون')  # 'بدون', 'عداد', 'كميات', 'خيارات مخصصة'
    api_linked = db.Column(db.Boolean, default=False)
    api_details = db.Column(db.Text)  # JSON string for API configuration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    # orders = db.relationship('Order', backref='product', lazy=True)
    custom_options = db.relationship('ProductCustomOption', backref='product', lazy=True, cascade='all, delete-orphan')
    inventory = db.relationship('ProductInventory', backref='product', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'product_id': self.product_id,
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'currency': self.currency,
            'cost_price': self.cost_price,
            'sell_price': self.sell_price,
            'image_url': self.image_url,
            'is_available': self.is_available,
            'product_type': self.product_type,
            'api_linked': self.api_linked,
            'api_details': self.api_details,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Product {self.name}>'

class ProductCustomOption(db.Model):
    __tablename__ = 'product_custom_options'
    
    option_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    option_name = db.Column(db.String(100), nullable=False)
    option_values = db.Column(db.Text)  # JSON string for option values
    
    def to_dict(self):
        return {
            'option_id': self.option_id,
            'product_id': self.product_id,
            'option_name': self.option_name,
            'option_values': self.option_values
        }

class ProductInventory(db.Model):
    __tablename__ = 'product_inventory'
    
    inventory_id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    
    def to_dict(self):
        return {
            'inventory_id': self.inventory_id,
            'product_id': self.product_id,
            'quantity': self.quantity
        }

