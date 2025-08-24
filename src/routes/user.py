from flask import Blueprint, jsonify, request
from src.models.user import User, db

user_bp = Blueprint('user', __name__)

# دالة مساعدة لتوحيد الردود
def make_response(message, status=200, data=None):
    response = {'message': message}
    if data:
        response['data'] = data
    return jsonify(response), status

# دالة للتحقق من البيانات المطلوبة
def validate_user_data(data):
    required_fields = ['uid', 'username', 'email']
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return f"الحقول التالية مطلوبة: {', '.join(missing)}"
    return None

# [GET] جلب جميع المستخدمين
@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return make_response('قائمة المستخدمين', 200, [user.to_dict() for user in users])

# [POST] إنشاء مستخدم جديد
@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    error = validate_user_data(data)
    if error:
        return make_response(error, 400)

    uid = data['uid']
    username = data['username']
    email = data['email']

    # تحقق من عدم وجود uid أو username أو email مكرر
    if User.query.filter_by(uid=uid).first():
        return make_response('المستخدم موجود مسبقًا (uid)', 409)
    if User.query.filter_by(username=username).first():
        return make_response('اسم المستخدم مستخدم مسبقًا', 409)
    if User.query.filter_by(email=email).first():
        return make_response('البريد الإلكتروني مستخدم مسبقًا', 409)

    user = User(uid=uid, username=username, email=email)
    db.session.add(user)
    db.session.commit()

    return make_response('تم إنشاء المستخدم بنجاح', 201, user.to_dict())

# [GET] جلب مستخدم واحد حسب ID
@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return make_response('بيانات المستخدم', 200, user.to_dict())

# [PUT] تحديث بيانات مستخدم
@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)

    db.session.commit()
    return make_response('تم تحديث المستخدم', 200, user.to_dict())

# [DELETE] حذف مستخدم
@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return make_response('تم حذف المستخدم', 200)