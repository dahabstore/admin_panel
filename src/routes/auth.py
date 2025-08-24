from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import check_password_hash
import jwt
import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """تسجيل دخول المستخدم"""
    try:
        from src.main import db, User
        
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'البريد الإلكتروني وكلمة المرور مطلوبان'
            }), 400
        
        # البحث عن المستخدم
        user = User.query.filter_by(email=data['email']).first()
        
        if not user:
            return jsonify({
                'success': False,
                'message': 'البريد الإلكتروني أو كلمة المرور غير صحيحة'
            }), 401
        
        # التحقق من كلمة المرور
        if not check_password_hash(user.password_hash, data['password']):
            return jsonify({
                'success': False,
                'message': 'البريد الإلكتروني أو كلمة المرور غير صحيحة'
            }), 401
        
        # التحقق من حالة المستخدم
        if user.status != 'نشط':
            return jsonify({
                'success': False,
                'message': 'حسابك محظور، يرجى التواصل مع الدعم الفني'
            }), 403
        
        # إنشاء رمز JWT
        token_payload = {
            'user_id': user.user_id,
            'email': user.email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        
        token = jwt.encode(token_payload, current_app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': 'تم تسجيل الدخول بنجاح',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في تسجيل الدخول: {str(e)}'
        }), 500

@auth_bp.route('/register', methods=['POST'])
def register():
    """تسجيل مستخدم جديد"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        # التحقق من عدم وجود مستخدم بنفس البريد الإلكتروني
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'يوجد حساب بهذا البريد الإلكتروني بالفعل'
            }), 400
        
        # التحقق من عدم وجود مستخدم بنفس اسم المستخدم
        existing_username = User.query.filter_by(username=data['username']).first()
        if existing_username:
            return jsonify({
                'success': False,
                'message': 'اسم المستخدم مستخدم بالفعل'
            }), 400
        
        # التحقق من طول كلمة المرور
        if len(data['password']) < 6:
            return jsonify({
                'success': False,
                'message': 'كلمة المرور يجب أن تكون 6 أحرف على الأقل'
            }), 400
        
        # إنشاء المستخدم الجديد
        new_user = User(
            username=data['username'],
            email=data['email'],
            balance=0.0,
            vip_level=1,
            total_spent=0.0,
            status='نشط'
        )
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم إنشاء الحساب بنجاح',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في إنشاء الحساب: {str(e)}'
        }), 500

@auth_bp.route('/verify-token', methods=['POST'])
def verify_token():
    """التحقق من صحة الرمز المميز"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'الرمز المميز مطلوب'
            }), 400
        
        # فك تشفير الرمز
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        
        # البحث عن المستخدم
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({
                'success': False,
                'message': 'المستخدم غير موجود'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'الرمز صحيح',
            'user': user.to_dict()
        }), 200
        
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
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'خطأ في التحقق من الرمز: {str(e)}'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """تغيير كلمة المرور"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات المطلوبة
        required_fields = ['email', 'current_password', 'new_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'الحقل {field} مطلوب'
                }), 400
        
        # البحث عن المستخدم
        user = User.query.filter_by(email=data['email']).first()
        if not user:
            return jsonify({
                'success': False,
                'message': 'المستخدم غير موجود'
            }), 404
        
        # التحقق من كلمة المرور الحالية
        if not check_password_hash(user.password_hash, data['current_password']):
            return jsonify({
                'success': False,
                'message': 'كلمة المرور الحالية غير صحيحة'
            }), 401
        
        # التحقق من طول كلمة المرور الجديدة
        if len(data['new_password']) < 6:
            return jsonify({
                'success': False,
                'message': 'كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل'
            }), 400
        
        # تحديث كلمة المرور
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'تم تغيير كلمة المرور بنجاح'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'خطأ في تغيير كلمة المرور: {str(e)}'
        }), 500

