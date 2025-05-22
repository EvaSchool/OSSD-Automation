from flask import Blueprint, jsonify, request
from app.models.student import Student, Month, GraduationStatus
from app import db
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from app.utils import parse_enum 

bp = Blueprint('students', __name__)

@bp.route('', methods=['GET'])
@jwt_required()
def get_students():
    query = Student.query

    # 筛选参数
    keyword = request.args.get('keyword', '').strip()
    grade = request.args.get('grade')
    enrollment_year = request.args.get('enrollment_year', type=int)
    enrollment_month = request.args.get('enrollment_month')

    if keyword:
        query = query.filter(or_(
            Student.first_name.ilike(f'%{keyword}%'),
            Student.last_name.ilike(f'%{keyword}%'),
            Student.OEN.ilike(f'%{keyword}%')
        ))

    if grade:
        query = query.filter(Student.grade == grade)

    if enrollment_year:
        query = query.filter(Student.enrollment_year == enrollment_year)

    if enrollment_month:
        try:
            month_enum = parse_enum(enrollment_month, Month)
            query = query.filter(Student.enrollment_month == month_enum)
        except Exception:
            return jsonify({'error': f'Invalid enrollment_month: {enrollment_month}'}), 400

    # 分页
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'total': pagination.total,
            'list': [s.to_dict() for s in pagination.items]
        }
    })

@bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_student(id):
    student = Student.query.get_or_404(id)
    return jsonify(student.to_dict())

@bp.route('', methods=['POST'])
@jwt_required()
def create_student():
    data = request.get_json()
    try:
        student = Student(
            last_name=data['last_name'],
            first_name=data['first_name'],
            OEN=data['OEN'],
            birth_year=data['birth_year'],
            birth_month=parse_enum(Month, data['birth_month']),
            birth_day=data['birth_day'],
            enrollment_year=data['enrollment_year'],
            enrollment_month=parse_enum(Month, data['enrollment_month']),
            enrollment_day=data['enrollment_day'],
            expected_graduation_year=data['expected_graduation_year'],
            expected_graduation_month=parse_enum(Month, data.get('expected_graduation_month', 'JUN')),
            expected_graduation_day=data.get('expected_graduation_day', 30),
            address=data.get('address'),
            graduation_status=parse_enum(GraduationStatus, data.get('graduation_status', 'IN_PROGRESS')),
            volunteer_hours=data.get('volunteer_hours', 0),
            grade=data.get('grade', '9'),
            remark=data.get('remark')
        )

        db.session.add(student)
        db.session.commit()
        return jsonify(student.to_dict()), 201

    except KeyError as e:
        return jsonify({'error': f'Missing field: {str(e)}'}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': 'OEN must be unique'}), 400

@bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_student(id):
    student = Student.query.get_or_404(id)
    data = request.get_json()

    for field in [
        'last_name', 'first_name', 'OEN', 'birth_year', 'birth_month', 'birth_day',
        'enrollment_year', 'enrollment_month', 'enrollment_day',
        'expected_graduation_year', 'expected_graduation_month', 'expected_graduation_day',
        'address', 'graduation_status', 'volunteer_hours', 'grade', 'remark'
    ]:
        if field in data:
            value = data[field]
            if field in ['birth_month', 'enrollment_month', 'expected_graduation_month']:
                setattr(student, field, parse_enum(Month, value))
            elif field == 'graduation_status':
                setattr(student, field, parse_enum(GraduationStatus, value))
            else:
                setattr(student, field, value)

    db.session.commit()
    return jsonify(student.to_dict())

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    return '', 204
