from flask import Blueprint, request, jsonify
from src.models.category import db, Category
from src.models.product import Product

category_bp = Blueprint('category', __name__)

@category_bp.route('/categories', methods=['GET'])
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

@category_bp.route('/categories/<int:category_id>', methods=['GET'])
def get_category(category_id):
    """الحصول على قسم محدد"""
    try:
        category = Category.query.get_or_404(category_id)
        return jsonify({
            'success': True,
            'data': category.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب القسم: {str(e)}'
        }), 500

@category_bp.route('/categories', methods=['POST'])
def create_category():
    """إنشاء قسم جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'اسم القسم مطلوب'
            }), 400
        
        # التحقق من عدم وجود قسم بنفس الاسم
        existing_category = Category.query.filter_by(name=data['name']).first()
        if existing_category:
            return jsonify({
                'success': False,
                'message': 'يوجد قسم بهذا الاسم بالفعل'
            }), 400
        
        # إنشاء القسم الجديد
        category = Category(
            name=data['name'],
            description=data.get('description', ''),
            image_url=data.get('image_url')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء القسم بنجاح',
            'data': category.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء القسم: {str(e)}'
        }), 500

@category_bp.route('/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """تحديث قسم موجود"""
    try:
        category = Category.query.get_or_404(category_id)
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        if not data.get('name'):
            return jsonify({
                'success': False,
                'message': 'اسم القسم مطلوب'
            }), 400
        
        # التحقق من عدم وجود قسم آخر بنفس الاسم
        existing_category = Category.query.filter(
            Category.name == data['name'],
            Category.category_id != category_id
        ).first()
        if existing_category:
            return jsonify({
                'success': False,
                'message': 'يوجد قسم بهذا الاسم بالفعل'
            }), 400
        
        # تحديث البيانات
        category.name = data['name']
        category.description = data.get('description', category.description)
        category.image_url = data.get('image_url', category.image_url)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث القسم بنجاح',
            'data': category.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث القسم: {str(e)}'
        }), 500

@category_bp.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """حذف قسم"""
    try:
        category = Category.query.get_or_404(category_id)
        
        # التحقق من وجود منتجات في هذا القسم
        products_count = Product.query.filter_by(category_id=category_id).count()
        if products_count > 0:
            return jsonify({
                'success': False,
                'message': f'لا يمكن حذف القسم لأنه يحتوي على {products_count} منتج. يرجى حذف المنتجات أولاً.'
            }), 400
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم حذف القسم بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في حذف القسم: {str(e)}'
        }), 500

@category_bp.route('/categories/<int:category_id>/products', methods=['GET'])
def get_category_products(category_id):
    """الحصول على منتجات قسم محدد"""
    try:
        category = Category.query.get_or_404(category_id)
        products = Product.query.filter_by(category_id=category_id).all()
        
        return jsonify({
            'success': True,
            'data': {
                'category': category.to_dict(),
                'products': [product.to_dict() for product in products]
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب منتجات القسم: {str(e)}'
        }), 500

