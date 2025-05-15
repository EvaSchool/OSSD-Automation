from flask import Blueprint, jsonify, request
from app.models import OperationLog, OperationType, TargetTable, User
from app import db
from datetime import datetime
from sqlalchemy import and_
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps

bp = Blueprint('operation_logs', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin:
            return jsonify({'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/operation-logs', methods=['GET'])
@jwt_required()
@admin_required
def get_operation_logs():
    """获取操作日志列表，支持分页和筛选"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    user_id = request.args.get('user_id', type=int)
    operation_type = request.args.get('operation_type')
    target_table = request.args.get('target_table')
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    query = OperationLog.query
    
    # 应用筛选条件
    if user_id:
        query = query.filter(OperationLog.user_id == user_id)
    if operation_type:
        query = query.filter(OperationLog.operation_type == OperationType(operation_type))
    if target_table:
        query = query.filter(OperationLog.target_table == TargetTable(target_table))
    if start_time:
        start_time = datetime.fromisoformat(start_time)
        query = query.filter(OperationLog.operation_time >= start_time)
    if end_time:
        end_time = datetime.fromisoformat(end_time)
        query = query.filter(OperationLog.operation_time <= end_time)
    
    # 按时间倒序排序
    query = query.order_by(OperationLog.operation_time.desc())
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'items': [log.to_dict() for log in pagination.items]
    })

@bp.route('/operation-logs/<int:log_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_operation_log(log_id):
    """获取单个操作日志详情"""
    log = OperationLog.query.get_or_404(log_id)
    return jsonify(log.to_dict())

@bp.route('/operation-logs/user/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user_operation_logs(user_id):
    """获取指定用户的操作日志"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = OperationLog.query.filter_by(user_id=user_id)
    query = query.order_by(OperationLog.operation_time.desc())
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'items': [log.to_dict() for log in pagination.items]
    })

@bp.route('/operation-logs/time-range', methods=['GET'])
@jwt_required()
@admin_required
def get_operation_logs_by_time_range():
    """按时间范围查询操作日志"""
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    
    if not start_time or not end_time:
        return jsonify({'error': '必须提供开始时间和结束时间'}), 400
    
    try:
        start_time = datetime.fromisoformat(start_time)
        end_time = datetime.fromisoformat(end_time)
    except ValueError:
        return jsonify({'error': '时间格式无效'}), 400
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    query = OperationLog.query.filter(
        and_(
            OperationLog.operation_time >= start_time,
            OperationLog.operation_time <= end_time
        )
    )
    query = query.order_by(OperationLog.operation_time.desc())
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'per_page': per_page,
        'items': [log.to_dict() for log in pagination.items]
    }) 