from flask import Blueprint, jsonify, request
from app.models.student import Student
from app import db
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

bp = Blueprint('students', __name__)

# 获取所有学生
@bp.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    students = Student.query.all()
    return jsonify([student.to_dict() for student in students])

# 获取单个学生
@bp.route('/students/<int:id>', methods=['GET'])
@jwt_required()
def get_student(id):
    student = Student.query.get_or_404(id)
    return jsonify(student.to_dict())

# 创建新学生
@bp.route('/students', methods=['POST'])
@jwt_required()
def create_student():
    data = request.get_json()
    try:
        student = Student(
            last_name=data['last_name'],
            first_name=data['first_name'],
            OEN=data['OEN'],
            birth_year=data['birth_year'],
            birth_month=data['birth_month'],
            birth_day=data['birth_day'],
            enrollment_year=data['enrollment_year'],
            enrollment_month=data['enrollment_month'],
            enrollment_day=data['enrollment_day'],
            expected_graduation_year=data['expected_graduation_year'],
            expected_graduation_month=data.get('expected_graduation_month', 'Jun'),
            expected_graduation_day=data.get('expected_graduation_day', 30),
            address=data.get('address'),
            graduation_status=data.get('graduation_status', 'In Progress'),
            volunteer_hours=data.get('volunteer_hours', 0)
        )
        db.session.add(student)
        db.session.commit()
        return jsonify(student.to_dict()), 201

    except KeyError as e:
        return jsonify({'error': f'Missing field: {str(e)}'}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'OEN must be unique'}), 400

# 更新学生信息
@bp.route('/students/<int:id>', methods=['PUT'])
@jwt_required()
def update_student(id):
    student = Student.query.get_or_404(id)
    data = request.get_json()
    
    for field in [
        'last_name', 'first_name', 'OEN', 'birth_year', 'birth_month', 'birth_day',
        'enrollment_year', 'enrollment_month', 'enrollment_day',
        'expected_graduation_year', 'expected_graduation_month', 'expected_graduation_day',
        'address', 'graduation_status', 'volunteer_hours'
    ]:
        if field in data:
            setattr(student, field, data[field])
    
    db.session.commit()
    return jsonify(student.to_dict())

# 删除学生
@bp.route('/students/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    return '', 204
