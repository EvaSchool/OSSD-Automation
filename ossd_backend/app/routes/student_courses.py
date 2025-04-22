from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required
from app.utils import admin_required
from app import db
from app.models import StudentCourse, Student, Course, CourseStatus, Month

bp = Blueprint('student_courses', __name__, url_prefix='/api/v1/student_courses')

# --------------------------------------------------
# GET /student_courses
# --------------------------------------------------
@bp.route('', methods=['GET'])
@jwt_required()
def list_student_courses():
    """分页+过滤：student_id, course_code, status"""
    q = StudentCourse.query
    student_id  = request.args.get('student_id',  type=int)
    course_code = request.args.get('course_code')
    status      = request.args.get('status')  # REGISTERED / IN_PROGRESS / COMPLETED
    page        = request.args.get('page', 1, type=int)
    page_size   = request.args.get('page_size', 10, type=int)

    if student_id:
        q = q.filter_by(student_id=student_id)
    if course_code:
        q = q.filter_by(course_code=course_code)
    if status:
        try:
            q = q.filter_by(status=CourseStatus[status.upper()])
        except KeyError:
            return jsonify({'code':400,'message':'Invalid status'}),400

    pagination = q.order_by(StudentCourse.id.desc()).paginate(page, page_size, error_out=False)
    return jsonify({
        'code': 200,
        'data': {
            'total': pagination.total,
            'list': [sc.to_dict() for sc in pagination.items]
        }
    })

# --------------------------------------------------
# POST /student_courses
# --------------------------------------------------
@bp.route('', methods=['POST'])
@jwt_required()
def create_student_course():
    """学生选课（不允许重复）"""
    data = request.get_json()
    try:
        sc = StudentCourse(
            student_id  = data['student_id'],
            course_code = data['course_code'],
            start_year  = data['start_year'],
            start_month = Month[data['start_month'].upper()],
            start_day   = data['start_day'],
        )
        db.session.add(sc)
        db.session.commit()
        return jsonify({'code':201,'data':sc.to_dict(),'message':'Enrolled successfully'}),201
    except IntegrityError:
        db.session.rollback()
        return jsonify({'code':400,'message':'Student has already enrolled this course'}),400
    except KeyError as e:
        return jsonify({'code':400,'message':f'Missing field: {e.args[0]}'}),400

# --------------------------------------------------
# PUT /student_courses/<int:id>
# --------------------------------------------------
@bp.route('/<int:sc_id>', methods=['PUT'])
@jwt_required()
def update_student_course(sc_id):
    """录入/修改成绩"""
    sc = StudentCourse.query.get_or_404(sc_id)
    data = request.get_json()
    try:
        if 'midterm_grade' in data:
            sc.set_midterm(int(data['midterm_grade']))
        if 'final_grade' in data:
            sc.set_final(int(data['final_grade']))
        db.session.commit()
        return jsonify({'code':200,'data':sc.to_dict(),'message':'Updated'}),200
    except ValueError as ve:
        db.session.rollback()
        return jsonify({'code':400,'message':str(ve)}),400

# --------------------------------------------------
# DELETE /student_courses/<int:id>  (管理员)
# --------------------------------------------------
@bp.route('/<int:sc_id>', methods=['DELETE'])
@admin_required
def delete_student_course(sc_id):
    sc = StudentCourse.query.get_or_404(sc_id)
    db.session.delete(sc)
    db.session.commit()
    return jsonify({'code':200,'message':'Deleted'}),200
