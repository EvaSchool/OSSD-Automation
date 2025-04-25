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

def parse_enum(enum_class, value, default=None):
    """
    通用枚举解析函数，将字符串转换为指定的 Enum 实例。
    支持简写值（如 '11'）或枚举名（如 'GRADE_11'）。
    """
    print(f"[parse_enum] Trying to parse value: {value} for enum {enum_class.__name__}")
    
    if value is None:
        print(f"[parse_enum] Value is None, returning default: {default}")
        return default

    value_str = str(value).strip().upper().replace(' ', '_')

    for member in enum_class:
        if member.value.upper() == value_str or member.name.upper() == value_str:
            print(f"[parse_enum] Matched {value_str} to {member}")
            return member

    print(f"[parse_enum] No match for: {value_str}")
    raise ValueError(f"Invalid value '{value}' for enum {enum_class.__name__}")

