import os,json
import sys
import firebase_admin
from firebase_admin import credentials, auth



firebase_src = os.environ.get("FIREBASE_CREDENTIALS", "").strip()
print("DEBUG ▶︎ source:", repr(firebase_src))

# لو بتستخدم Secret File، نطبع محتويات المجلد للتأكد من المونت:
if not firebase_src and os.path.isdir("/etc/secrets"):
    print("DEBUG ▶︎ /etc/secrets contains:", os.listdir("/etc/secrets"))

# بقية الكود كما في آخر نسخة:
if os.path.isfile(firebase_src):
    print("DEBUG ▶︎ using file path")
    cred = credentials.Certificate(firebase_src)
else:
    try:
        creds_dict = json.loads(firebase_src)
        print("DEBUG ▶︎ parsed JSON successfully")
        cred = credentials.Certificate(creds_dict)
    except Exception as e:
        print("ERROR ▶︎ failed to load creds:", e)
        raise

initialize_app(cred)
print("✔ Firebase initialized!")

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# إنشاء التطبيق
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# تمكين CORS للسماح بطلبات من Flutter
CORS(app)

# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إنشاء مجلد قاعدة البيانات إذا لم يكن موجوداً
os.makedirs(os.path.join(os.path.dirname(__file__), 'database'), exist_ok=True)

# تهيئة قاعدة البيانات
db = SQLAlchemy(app)

@app.before_request
def verify_firebase_token():
    public_paths = ['/', '/api/health']
    if request.path in public_paths or request.path.startswith('/static'):
        return
    id_token = request.headers.get('Authorization')
    if not id_token:
        return jsonify({'success': False, 'message': 'مطلوب تسجيل الدخول'}), 401
    try:
        decoded_token = auth.verify_id_token(id_token)
        request.user = decoded_token
    except Exception:
        return jsonify({'success': False, 'message': 'رمز الدخول غير صالح'}), 401

# تعريف النماذج
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

class Category(db.Model):
    __tablename__ = 'categories'
    
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            'category_id': self.category_id,
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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
    product_type = db.Column(db.String(50), nullable=False, default='بدون')
    api_linked = db.Column(db.Boolean, default=False)
    api_details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
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

class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    
    method_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            'method_id': self.method_id,
            'name': self.name,
            'details': self.details,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# إنشاء الجداول وإضافة بيانات تجريبية
with app.app_context():
    db.create_all()
    
    # إضافة مستويات VIP الافتراضية
    if VIPLevel.query.count() == 0:
        vip_levels = [
            VIPLevel(level_name='برونزي', min_spent=0, discount_percentage=0),
            VIPLevel(level_name='فضي', min_spent=1000, discount_percentage=5),
            VIPLevel(level_name='ذهبي', min_spent=5000, discount_percentage=10),
            VIPLevel(level_name='بلاتيني', min_spent=10000, discount_percentage=15),
            VIPLevel(level_name='ماسي', min_spent=25000, discount_percentage=20),
        ]
        for level in vip_levels:
            db.session.add(level)
    
    # إضافة طرق دفع افتراضية
    if PaymentMethod.query.count() == 0:
        payment_methods = [
            PaymentMethod(
                name='تحويل بنكي - البنك الأهلي',
                details='رقم الحساب: 1234567890\nاسم المستلم: متجر الألعاب'
            ),
            PaymentMethod(
                name='فودافون كاش',
                details='رقم المحفظة: 01012345678\nاسم المستلم: متجر الألعاب'
            ),
            PaymentMethod(
                name='أورانج موني',
                details='رقم المحفظة: 01112345678\nاسم المستلم: متجر الألعاب'
            ),
            PaymentMethod(
                name='إتصالات كاش',
                details='رقم المحفظة: 01012345678\nاسم المستلم: متجر الألعاب'
            ),
        ]
        for method in payment_methods:
            db.session.add(method)
    
    # إضافة أقسام تجريبية
    if Category.query.count() == 0:
        categories = [
            Category(name='ألعاب الهاتف', description='شحن ألعاب الهاتف المحمول'),
            Category(name='ألعاب الكمبيوتر', description='شحن ألعاب الكمبيوتر'),
            Category(name='بطاقات الألعاب', description='بطاقات شحن متنوعة'),
            Category(name='تطبيقات أخرى', description='شحن التطبيقات المختلفة'),
        ]
        for category in categories:
            db.session.add(category)
    
    # إضافة منتجات تجريبية
    if Product.query.count() == 0:
        products = [
            Product(
                name='شحن PUBG Mobile - 60 UC',
                category_id=1,
                description='شحن 60 UC لـ PUBG Mobile',
                cost_price=5.0,
                sell_price=8.0,
                product_type='بدون'
            ),
            Product(
                name='شحن PUBG Mobile - UC مخصص',
                category_id=1,
                description='شحن UC بالكمية المطلوبة',
                cost_price=0.1,
                sell_price=0.15,
                product_type='عداد'
            ),
            Product(
                name='شحن Free Fire - الماس',
                category_id=1,
                description='شحن الماس لـ Free Fire',
                cost_price=10.0,
                sell_price=15.0,
                product_type='كميات'
            ),
        ]
        for product in products:
            db.session.add(product)
    
    db.session.commit()

# المسارات
@app.route('/api/health', methods=['GET'])
def health_check():
    """فحص صحة الخادم"""
    return jsonify({
        'success': True,
        'message': 'الخادم يعمل بشكل طبيعي',
        'version': '1.0.0'
    })

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """الحصول على جميع الأقسام"""
    try:
        categories = Category.query.all()
        return jsonify({
            'success': True,
            'data': [category.to_dict() for category in categories]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب الأقسام: {str(e)}'
        }), 500

@app.route('/api/products', methods=['GET'])
def get_products():
    """الحصول على جميع المنتجات"""
    try:
        category_id = request.args.get('category_id', type=int)
        
        query = Product.query
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        products = query.all()
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب المنتجات: {str(e)}'
        }), 500

@app.route('/api/payment-methods', methods=['GET'])
def get_payment_methods():
    """الحصول على طرق الدفع المتاحة"""
    try:
        methods = PaymentMethod.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [method.to_dict() for method in methods]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب طرق الدفع: {str(e)}'
        }), 500

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

