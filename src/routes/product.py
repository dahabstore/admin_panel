from flask import Blueprint, request, jsonify
from src.models.product import db, Product, ProductCustomOption, ProductInventory
from src.models.category import Category
import json

product_bp = Blueprint('product', __name__)

@product_bp.route('/products', methods=['GET'])
def get_products():
    """الحصول على جميع المنتجات"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        category_id = request.args.get('category_id', type=int)
        search = request.args.get('search', '')
        
        query = Product.query
        
        # تصفية حسب القسم
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        # البحث في اسم المنتج أو الوصف
        if search:
            query = query.filter(
                Product.name.contains(search) | 
                Product.description.contains(search)
            )
        
        # ترتيب حسب تاريخ الإنشاء
        query = query.order_by(Product.created_at.desc())
        
        # تقسيم الصفحات
        products = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': products.total,
                'pages': products.pages,
                'has_next': products.has_next,
                'has_prev': products.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب المنتجات: {str(e)}'
        }), 500

@product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """الحصول على منتج محدد"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # جلب الخيارات المخصصة والمخزون
        custom_options = ProductCustomOption.query.filter_by(product_id=product_id).all()
        inventory = ProductInventory.query.filter_by(product_id=product_id).first()
        
        product_data = product.to_dict()
        product_data['custom_options'] = [option.to_dict() for option in custom_options]
        product_data['inventory'] = inventory.to_dict() if inventory else None
        
        return jsonify({
            'success': True,
            'data': product_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب المنتج: {str(e)}'
        }), 500

@product_bp.route('/products', methods=['POST'])
def create_product():
    """إنشاء منتج جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['name', 'category_id', 'cost_price', 'sell_price', 'product_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        # التحقق من وجود القسم
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({
                'success': False,
                'message': 'القسم المحدد غير موجود'
            }), 400
        
        # التحقق من صحة نوع المنتج
        valid_types = ['بدون', 'عداد', 'كميات', 'خيارات مخصصة']
        if data['product_type'] not in valid_types:
            return jsonify({
                'success': False,
                'message': 'نوع المنتج غير صحيح'
            }), 400
        
        # إنشاء المنتج الجديد
        product = Product(
            name=data['name'],
            category_id=data['category_id'],
            description=data.get('description', ''),
            currency=data.get('currency', 'ريال'),
            cost_price=float(data['cost_price']),
            sell_price=float(data['sell_price']),
            image_url=data.get('image_url'),
            is_available=data.get('is_available', True),
            product_type=data['product_type'],
            api_linked=data.get('api_linked', False),
            api_details=data.get('api_details')
        )
        
        db.session.add(product)
        db.session.flush()  # للحصول على product_id
        
        # إضافة الخيارات المخصصة إذا كان النوع "خيارات مخصصة"
        if data['product_type'] == 'خيارات مخصصة' and data.get('custom_options'):
            for option_data in data['custom_options']:
                option = ProductCustomOption(
                    product_id=product.product_id,
                    option_name=option_data['option_name'],
                    option_values=json.dumps(option_data['option_values'])
                )
                db.session.add(option)
        
        # إضافة المخزون إذا كان النوع "كميات"
        if data['product_type'] == 'كميات' and data.get('quantity') is not None:
            inventory = ProductInventory(
                product_id=product.product_id,
                quantity=int(data['quantity'])
            )
            db.session.add(inventory)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء المنتج بنجاح',
            'data': product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء المنتج: {str(e)}'
        }), 500

@product_bp.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """تحديث منتج موجود"""
    try:
        product = Product.query.get_or_404(product_id)
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['name', 'category_id', 'cost_price', 'sell_price', 'product_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        # التحقق من وجود القسم
        if data['category_id'] != product.category_id:
            category = Category.query.get(data['category_id'])
            if not category:
                return jsonify({
                    'success': False,
                    'message': 'القسم المحدد غير موجود'
                }), 400
        
        # تحديث البيانات الأساسية
        product.name = data['name']
        product.category_id = data['category_id']
        product.description = data.get('description', product.description)
        product.currency = data.get('currency', product.currency)
        product.cost_price = float(data['cost_price'])
        product.sell_price = float(data['sell_price'])
        product.image_url = data.get('image_url', product.image_url)
        product.is_available = data.get('is_available', product.is_available)
        product.product_type = data['product_type']
        product.api_linked = data.get('api_linked', product.api_linked)
        product.api_details = data.get('api_details', product.api_details)
        
        # تحديث الخيارات المخصصة
        if data['product_type'] == 'خيارات مخصصة':
            # حذف الخيارات القديمة
            ProductCustomOption.query.filter_by(product_id=product_id).delete()
            
            # إضافة الخيارات الجديدة
            if data.get('custom_options'):
                for option_data in data['custom_options']:
                    option = ProductCustomOption(
                        product_id=product_id,
                        option_name=option_data['option_name'],
                        option_values=json.dumps(option_data['option_values'])
                    )
                    db.session.add(option)
        
        # تحديث المخزون
        if data['product_type'] == 'كميات':
            inventory = ProductInventory.query.filter_by(product_id=product_id).first()
            if inventory:
                inventory.quantity = int(data.get('quantity', inventory.quantity))
            elif data.get('quantity') is not None:
                inventory = ProductInventory(
                    product_id=product_id,
                    quantity=int(data['quantity'])
                )
                db.session.add(inventory)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث المنتج بنجاح',
            'data': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث المنتج: {str(e)}'
        }), 500

@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """حذف منتج"""
    try:
        product = Product.query.get_or_404(product_id)
        
        # التحقق من وجود طلبات لهذا المنتج
        from src.models.order import Order
        orders_count = Order.query.filter_by(product_id=product_id).count()
        if orders_count > 0:
            return jsonify({
                'success': False,
                'message': f'لا يمكن حذف المنتج لأنه مرتبط بـ {orders_count} طلب'
            }), 400
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف المنتج بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في حذف المنتج: {str(e)}'
        }), 500

@product_bp.route('/products/<int:product_id>/toggle-availability', methods=['PATCH'])
def toggle_product_availability(product_id):
    """تبديل حالة توفر المنتج"""
    try:
        product = Product.query.get_or_404(product_id)
        product.is_available = not product.is_available
        
        db.session.commit()
        
        status = 'متاح' if product.is_available else 'غير متاح'
        return jsonify({
            'success': True,
            'message': f'تم تغيير حالة المنتج إلى {status}',
            'data': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تغيير حالة المنتج: {str(e)}'
        }), 500

