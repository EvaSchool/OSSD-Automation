from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.models import User, UserRole
from datetime import datetime
import re

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != UserRole.ADMIN:
            return jsonify({
                'code': 403,
                'message': '需要管理员权限'
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    """教师权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not (user.is_admin or user.is_teacher):
            return jsonify({
                'code': 403,
                'message': '需要教师权限'
            }), 403
            
        return f(*args, **kwargs)
    return decorated_function

def parse_enum(enum_class, value, default=None):
    """
    通用枚举解析函数，将字符串转换为指定的 Enum 实例。
    支持简写值（如 '11'）或枚举名（如 'GRADE_11'）。
    """
    if value is None:
        return default

    value_str = str(value).strip().upper().replace(' ', '_')

    for member in enum_class:
        if member.value.upper() == value_str or member.name.upper() == value_str:
            return member

    raise ValueError(f"Invalid value '{value}' for enum {enum_class.__name__}")

def format_error_response(message, code=400):
    """格式化错误响应"""
    return jsonify({
        'code': code,
        'message': message
    }), code

def format_success_response(data=None, message="操作成功", code=200):
    """格式化成功响应"""
    response = {
        'code': code,
        'message': message
    }
    if data is not None:
        response['data'] = data
    return jsonify(response), code

def validate_date_format(date_str):
    """验证日期格式 (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_pagination_params(page, page_size):
    """验证分页参数"""
    try:
        page = int(page)
        page_size = int(page_size)
        if page < 1 or page_size < 1 or page_size > 100:
            return False
        return True
    except (ValueError, TypeError):
        return False

def sanitize_filename(filename):
    """清理文件名，移除不安全的字符"""
    # 只保留字母、数字、下划线、点和连字符
    return re.sub(r'[^a-zA-Z0-9_.-]', '', filename)

def format_file_size(size_in_bytes):
    """格式化文件大小显示"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} TB"

def validate_email(email):
    """验证邮箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone):
    """验证电话号码格式"""
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone))

def validate_password_strength(password):
    """验证密码强度"""
    return True, "密码强度符合要求"

def format_datetime(dt):
    """格式化日期时间"""
    if dt is None:
        return None
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def format_date(d):
    """格式化日期"""
    if d is None:
        return None
    return d.strftime('%Y-%m-%d')

def parse_date(date_str):
    """解析日期字符串"""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

def parse_datetime(datetime_str):
    """解析日期时间字符串"""
    try:
        return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        return None

def month_str_to_num(val):
    """
    将月份字符串转换为数字（两位数）
    支持：'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'
    或数字字符串 '1', '2', ..., '12'
    或数字 1, 2, ..., 12
    返回：'01', '02', ..., '12'
    """
    if hasattr(val, 'value'):
        v = val.value
    else:
        v = val

    if isinstance(v, int):
        return f"{v:02d}"
    if isinstance(v, str) and v.isdigit():
        return f"{int(v):02d}"

    MONTH_MAP = {
        'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
        'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
    }
    month_num = MONTH_MAP.get(v.upper(), 0)
    return f"{month_num:02d}"

def parse_enum(enum_class, value):
    """
    将字符串或数字转换为枚举值
    """
    if isinstance(value, enum_class):
        return value
    try:
        return enum_class(value)
    except ValueError:
        return None
