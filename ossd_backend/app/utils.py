from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask import jsonify
from app.models import User, UserRole  # ✅ 确保导入 UserRole

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()  # ✅ 确保请求里带了 JWT
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        # ✅ 用 role 判断是否为 ADMIN
        if not user or user.role != UserRole.ADMIN:
            return jsonify({
                'code': 403,
                'message': '需要管理员权限'
            }), 403

        return fn(*args, **kwargs)
    return wrapper
