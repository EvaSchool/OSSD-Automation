from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User, UserRole
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError

bp = Blueprint('users', __name__)
print("📡 用户蓝图已创建")

# 用户注册
@bp.route('/register', methods=['POST'])
def register():
    print("📡 Processing registration request")
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409

    role = data.get('role', 'User')
    if role not in UserRole._value2member_map_:
        return jsonify({'error': 'Invalid role'}), 400

    user = User(username=data['username'], role=UserRole(role))
    user.set_password(data['password'])

    db.session.add(user)
    try:
        db.session.commit()
        print("✅ User registered successfully")
    except IntegrityError:
        db.session.rollback()
        print("❌ User registration failed")
        return jsonify({'error': 'Registration failed'}), 500

    return jsonify({'message': 'Registration successful'}), 201

# 用户登录
@bp.route('/login', methods=['POST'])
def login():
    print("📡 Processing login request")
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if not user or not user.check_password(data['password']):
        print("❌ Incorrect username or password")
        return jsonify({'error': 'Incorrect username or password'}), 401

    token = create_access_token(identity=user.user_id)
    print("✅ Login successful")
    return jsonify({'access_token': token}), 200
