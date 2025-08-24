from flask import Blueprint, request, jsonify, current_app
import jwt
from functools import wraps

user_management_bp = Blueprint('user_management', __name__)

def token_required(f):
    """ديكوريتر للتحقق من الرمز المميز"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from src.main import User
        
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'الرمز المميز مطلوب'
            }), 401
        
        try:
            # إزالة "Bearer " من بداية الرمز
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(payload['user_id'])
            
            if not current_user:
                return jsonify({
                    'success': False,
                    'message': 'المستخدم غير موجود'
                }), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'انتهت صلاحية الرمز المميز'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'الرمز المميز غير صحيح'
            }), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

@user_management_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """الحصول على معلومات المستخدم"""
    from src.main import VIPLevel
    
    try:
        # جلب معلومات مستوى VIP
        vip_level = VIPLevel.query.filter_by(level_id=current_user.vip_level).first()
        
        user_data = current_user.to_dict()
        user_data['vip_info'] = vip_level.to_dict() if vip_level else None
        
        # حساب التقدم للمستوى التالي
        next_vip = VIPLevel.query.filter(VIPLevel.level_id > current_user.vip_level).order_by(VIPLevel.level_id).first()
        if next_vip:
            user_data['next_vip'] = next_vip.to_dict()
            user_data['progress_to_next'] = min(current_user.total_spent / next_vip.min_spent, 1.0)
        
        return jsonify({
            'success': True,
            'data': user_data
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب معلومات المستخدم: {str(e)}'
        }), 500

@user_management_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """تحديث معلومات المستخدم"""
    from src.main import db, User
    
    try:
        data = request.get_json()
        
        # تحديث الحقول المسموح بتعديلها
        if data.get('username'):
            # التحقق من عدم وجود مستخدم آخر بنفس الاسم
            existing_user = User.query.filter(
                User.username == data['username'],
                User.user_id != current_user.user_id
            ).first()
            
            if existing_user:
                return jsonify({
                    'success': False,
                    'message': 'اسم المستخدم مستخدم بالفعل'
                }), 400
            
            current_user.username = data['username']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تحديث المعلومات بنجاح',
            'data': current_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تحديث المعلومات: {str(e)}'
        }), 500

@user_management_bp.route('/balance', methods=['GET'])
@token_required
def get_balance(current_user):
    """الحصول على رصيد المستخدم"""
    try:
        return jsonify({
            'success': True,
            'data': {
                'balance': current_user.balance,
                'total_spent': current_user.total_spent,
                'vip_level': current_user.vip_level
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب الرصيد: {str(e)}'
        }), 500

@user_management_bp.route('/vip-levels', methods=['GET'])
def get_vip_levels():
    """الحصول على جميع مستويات VIP"""
    from src.main import VIPLevel
    
    try:
        vip_levels = VIPLevel.query.order_by(VIPLevel.level_id).all()
        
        return jsonify({
            'success': True,
            'data': [level.to_dict() for level in vip_levels]
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في جلب مستويات VIP: {str(e)}'
        }), 500

@user_management_bp.route('/calculate-discount', methods=['POST'])
@token_required
def calculate_discount(current_user):
    """حساب الخصم المتاح للمستخدم"""
    from src.main import VIPLevel
    
    try:
        data = request.get_json()
        amount = data.get('amount', 0)
        
        if amount <= 0:
            return jsonify({
                'success': False,
                'message': 'المبلغ يجب أن يكون أكبر من صفر'
            }), 400
        
        # جلب معلومات مستوى VIP الحالي
        vip_level = VIPLevel.query.filter_by(level_id=current_user.vip_level).first()
        
        if not vip_level:
            discount_percentage = 0
        else:
            discount_percentage = vip_level.discount_percentage
        
        discount_amount = amount * (discount_percentage / 100)
        final_amount = amount - discount_amount
        
        return jsonify({
            'success': True,
            'data': {
                'original_amount': amount,
                'discount_percentage': discount_percentage,
                'discount_amount': discount_amount,
                'final_amount': final_amount,
                'vip_level': current_user.vip_level
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في حساب الخصم: {str(e)}'
        }), 500

def update_user_vip_level(user):
    """تحديث مستوى VIP للمستخدم بناءً على إجمالي الإنفاق"""
    from src.main import db, VIPLevel
    
    try:
        # جلب أعلى مستوى VIP يستحقه المستخدم
        eligible_vip = VIPLevel.query.filter(
            VIPLevel.min_spent <= user.total_spent
        ).order_by(VIPLevel.level_id.desc()).first()
        
        if eligible_vip and eligible_vip.level_id > user.vip_level:
            old_level = user.vip_level
            user.vip_level = eligible_vip.level_id
            db.session.commit()
            
            # يمكن إضافة إشعار هنا للمستخدم بالترقية
            return {
                'upgraded': True,
                'old_level': old_level,
                'new_level': user.vip_level,
                'vip_name': eligible_vip.level_name
            }
        
        return {'upgraded': False}
        
    except Exception as e:
        db.session.rollback()
        return {'upgraded': False, 'error': str(e)}

@user_management_bp.route('/add-balance', methods=['POST'])
@token_required
def add_balance(current_user):
    """إضافة رصيد للمستخدم (للاختبار فقط - في الواقع يتم عبر طلبات الدفع)"""
    from src.main import db
    
    try:
        data = request.get_json()
        amount = data.get('amount', 0)
        
        if amount <= 0:
            return jsonify({
                'success': False,
                'message': 'المبلغ يجب أن يكون أكبر من صفر'
            }), 400
        
        current_user.balance += amount
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'تم إضافة {amount} ريال إلى رصيدك',
            'data': {
                'new_balance': current_user.balance
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إضافة الرصيد: {str(e)}'
        }), 500

