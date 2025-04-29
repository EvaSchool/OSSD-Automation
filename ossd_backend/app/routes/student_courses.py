from flask import Blueprint, request, jsonify
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils import admin_required
from app import db
from app.models import StudentCourse, Student, Course, CourseStatus, Month, OperationLog, Template
from datetime import datetime

bp = Blueprint('student_courses', __name__, url_prefix='/api/v1/student_courses')

# --------------------------------------------------
# GET /student_courses
# --------------------------------------------------
@bp.route('', methods=['GET'])
@jwt_required()
def list_student_courses():
    """分页+过滤：学生姓名精确搜索、课程状态、是否必修、是否本校修读、课程代码"""
    try:
        # 获取查询参数
        student_name = request.args.get('student_name')
        course_code = request.args.get('course_code')
        status = request.args.get('status')
        is_compulsory = request.args.get('is_compulsory')
        is_local = request.args.get('is_local')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)

        # 构建查询
        query = StudentCourse.query.join(Student)

        # 学生姓名精确搜索
        if student_name:
            names = student_name.split()
            if len(names) == 2:
                query = query.filter(
                    and_(
                        Student.first_name == names[0],
                        Student.last_name == names[1]
                    )
                )
            else:
                return jsonify({'code': 400, 'message': 'Please provide both first name and last name'}), 400

        # 课程代码过滤
        if course_code:
            query = query.filter(StudentCourse.course_code == course_code)

        # 课程状态过滤
        if status:
            try:
                status_enum = CourseStatus[status.upper()]
                query = query.filter(StudentCourse.status == status_enum)
            except KeyError:
                return jsonify({'code': 400, 'message': 'Invalid course status'}), 400

        # 是否必修过滤
        if is_compulsory is not None:
            query = query.filter(StudentCourse.is_compulsory == (is_compulsory.lower() == 'true'))

        # 是否本校修读过滤
        if is_local is not None:
            query = query.filter(StudentCourse.is_local == (is_local.lower() == 'true'))

        # 分页
        pagination = query.order_by(StudentCourse.id.desc()).paginate(
            page=page, 
            per_page=page_size, 
            error_out=False
        )

        # 构建返回数据
        courses = []
        for sc in pagination.items:
            course_data = sc.to_dict()
            course_data['student_name'] = f"{sc.student.first_name} {sc.student.last_name}"
            course_data['start_date'] = f"{sc.start_year}-{sc.start_month.value}-{sc.start_day}"
            courses.append(course_data)

        return jsonify({
            'code': 200,
            'data': {
                'total': pagination.total,
                'list': courses
            }
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': f'Failed to get student courses list: {str(e)}'}), 500

# --------------------------------------------------
# POST /student_courses
# --------------------------------------------------
@bp.route('', methods=['POST'])
@jwt_required()
def create_student_course():
    """添加学生课程（区分已修、正在修）"""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        # 验证必填字段
        required_fields = ['student_id', 'course_code', 'start_year', 'start_month', 'start_day', 'status', 'is_compulsory', 'is_local']
        for field in required_fields:
            if field not in data:
                return jsonify({'code': 400, 'message': f'Missing required field: {field}'}), 400

        # 验证课程状态
        try:
            status = CourseStatus[data['status'].upper()]
            if status not in [CourseStatus.IN_PROGRESS, CourseStatus.GRADUATED]:
                return jsonify({'code': 400, 'message': 'New course status can only be IN_PROGRESS or GRADUATED'}), 400
        except KeyError:
            return jsonify({'code': 400, 'message': 'Invalid course status'}), 400

        # 验证月份
        try:
            start_month = Month[data['start_month'].upper()]
        except KeyError:
            return jsonify({'code': 400, 'message': 'Invalid month'}), 400

        # 如果是已修课程，验证成绩和完成日期
        if status == CourseStatus.GRADUATED:
            if not all(key in data for key in ['midterm_grade', 'final_grade', 'completion_date']):
                return jsonify({'code': 400, 'message': 'Graduated course must provide midterm grade, final grade and completion date'}), 400

        # 创建学生课程记录
        sc = StudentCourse(
            student_id=data['student_id'],
            course_code=data['course_code'],
            start_year=data['start_year'],
            start_month=start_month,
            start_day=data['start_day'],
            status=status,
            is_compulsory=data['is_compulsory'],
            is_local=data['is_local']
        )

        # 如果是已修课程，设置成绩和完成日期
        if status == CourseStatus.GRADUATED:
            sc.midterm_grade = data['midterm_grade']
            sc.final_grade = data['final_grade']
            sc.completion_date = datetime.strptime(data['completion_date'], '%Y-%m-%d').date()
            sc.report_card_date = datetime.now().date()  # 自动设置成绩单日期

        db.session.add(sc)
        db.session.commit()

        # 记录创建课程日志
        log = OperationLog(
            user_id=current_user_id,
            operation_type='create_student_course',
            operation_detail=f'为学生 {sc.student.first_name} {sc.student.last_name} 添加课程 {sc.course_code}，状态为 {status.value}，是否必修：{sc.is_compulsory}，是否本校：{sc.is_local}',
            target_table='student_courses',
            target_id=sc.id,
            created_at=datetime.now()
        )
        db.session.add(log)
        db.session.commit()

        return jsonify({
            'code': 201,
            'data': sc.to_dict(),
            'message': 'Course added successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'Failed to add course: {str(e)}'}), 500

# --------------------------------------------------
# PUT /student_courses/<int:id>/grades
# --------------------------------------------------
@bp.route('/<int:sc_id>/grades', methods=['PUT'])
@jwt_required()
def update_grades(sc_id):
    """更新学生课程成绩"""
    try:
        sc = StudentCourse.query.get_or_404(sc_id)
        data = request.get_json()
        current_user_id = get_jwt_identity()

        # 验证是否同时提供期中成绩和期末成绩
        if 'final_grade' in data and 'midterm_grade' not in data and sc.midterm_grade is None:
            return jsonify({'code': 400, 'message': 'Midterm grade must be provided before final grade'}), 400

        # 更新成绩
        if 'midterm_grade' in data:
            sc.midterm_grade = data['midterm_grade']
            # 记录期中成绩录入日志
            log = OperationLog(
                user_id=current_user_id,
                operation_type='update_midterm_grade',
                operation_detail=f'更新学生 {sc.student.first_name} {sc.student.last_name} 的课程 {sc.course_code} 期中成绩为 {data["midterm_grade"]}',
                target_table='student_courses',
                target_id=sc.id,
                created_at=datetime.now()
            )
            db.session.add(log)

        if 'final_grade' in data:
            sc.final_grade = data['final_grade']
            # 记录期末成绩录入日志
            log = OperationLog(
                user_id=current_user_id,
                operation_type='update_final_grade',
                operation_detail=f'更新学生 {sc.student.first_name} {sc.student.last_name} 的课程 {sc.course_code} 期末成绩为 {data["final_grade"]}',
                target_table='student_courses',
                target_id=sc.id,
                created_at=datetime.now()
            )
            db.session.add(log)

        db.session.commit()

        return jsonify({
            'code': 200,
            'data': sc.to_dict(),
            'message': 'Grades updated successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'Failed to update grades: {str(e)}'}), 500

@bp.route('/course/<course_code>', methods=['GET'])
@jwt_required()
def get_course_students(course_code):
    """获取指定课程正在修读的学生名单"""
    try:
        current_user_id = get_jwt_identity()
        
        # 记录查询课程学生日志
        log = OperationLog(
            user_id=current_user_id,
            operation_type='query_course_students',
            operation_detail=f'查询课程 {course_code} 的学生名单',
            target_table='student_courses',
            target_id=None,
            created_at=datetime.now()
        )
        db.session.add(log)
        db.session.commit()

        # 获取查询参数
        status = request.args.get('status', 'IN_PROGRESS')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)

        # 构建查询
        query = StudentCourse.query.join(Student).filter(
            StudentCourse.course_code == course_code
        )

        # 课程状态过滤
        try:
            status_enum = CourseStatus[status.upper()]
            query = query.filter(StudentCourse.status == status_enum)
        except KeyError:
            return jsonify({'code': 400, 'message': 'Invalid course status'}), 400

        # 分页
        pagination = query.order_by(StudentCourse.start_year.desc(), StudentCourse.start_month).paginate(
            page=page, 
            per_page=page_size, 
            error_out=False
        )

        # 构建返回数据
        students = []
        for sc in pagination.items:
            student_data = {
                'student_id': sc.student_id,
                'student_name': f"{sc.student.first_name} {sc.student.last_name}",
                'start_date': f"{sc.start_year}-{sc.start_month.value}-{sc.start_day}",
                'is_compulsory': sc.is_compulsory,
                'is_local': sc.is_local,
                'status': sc.status.value
            }
            students.append(student_data)

        return jsonify({
            'code': 200,
            'data': {
                'total': pagination.total,
                'list': students
            }
        })

    except Exception as e:
        return jsonify({'code': 500, 'message': f'Failed to get course students list: {str(e)}'}), 500

# --------------------------------------------------
# DELETE /student_courses/<int:id>  (管理员)
# --------------------------------------------------
@bp.route('/<int:sc_id>', methods=['DELETE'])
@admin_required
def delete_student_course(sc_id):
    """删除学生课程记录（仅管理员）"""
    try:
        sc = StudentCourse.query.get_or_404(sc_id)
        current_user_id = get_jwt_identity()
        
        # 记录删除课程日志
        log = OperationLog(
            user_id=current_user_id,
            operation_type='delete_student_course',
            operation_detail=f'删除学生 {sc.student.first_name} {sc.student.last_name} 的课程 {sc.course_code}',
            target_table='student_courses',
            target_id=sc.id,
            created_at=datetime.now()
        )
        db.session.add(log)
        
        db.session.delete(sc)
        db.session.commit()
        
        return jsonify({'code': 200, 'message': 'Course record deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'Failed to delete course record: {str(e)}'}), 500

@bp.route('/<int:sc_id>/withdraw', methods=['POST'])
@admin_required
def withdraw_course(sc_id):
    """退课（管理员权限）"""
    try:
        sc = StudentCourse.query.get_or_404(sc_id)
        current_user_id = get_jwt_identity()

        # 记录退课日志
        log = OperationLog(
            user_id=current_user_id,
            operation_type='withdraw_course',
            operation_detail=f'学生 {sc.student.first_name} {sc.student.last_name} 退课 {sc.course_code}',
            target_table='student_courses',
            target_id=sc.id,
            created_at=datetime.now()
        )
        db.session.add(log)

        # 更新课程状态为退课
        sc.status = CourseStatus.WITHDRAWN
        sc.withdrawal_date = datetime.now().date()

        db.session.commit()

        return jsonify({
            'code': 200,
            'data': sc.to_dict(),
            'message': 'Course withdrawn successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'Failed to withdraw course: {str(e)}'}), 500

@bp.route('/student/<int:student_id>/withdraw', methods=['POST'])
@admin_required
def withdraw_student(student_id):
    """学生退学，所有课程状态改为退课（管理员权限）"""
    try:
        student = Student.query.get_or_404(student_id)
        current_user_id = get_jwt_identity()

        # 获取学生的所有课程
        courses = StudentCourse.query.filter_by(student_id=student_id).all()
        
        # 记录退学日志
        log = OperationLog(
            user_id=current_user_id,
            operation_type='withdraw_student',
            operation_detail=f'学生 {student.first_name} {student.last_name} 退学，共 {len(courses)} 门课程',
            target_table='students',
            target_id=student_id,
            created_at=datetime.now()
        )
        db.session.add(log)

        # 更新所有课程状态为退课
        for course in courses:
            course.status = CourseStatus.WITHDRAWN
            course.withdrawal_date = datetime.now().date()
            
            # 记录每门课程的退课日志
            course_log = OperationLog(
                user_id=current_user_id,
                operation_type='withdraw_course',
                operation_detail=f'学生 {student.first_name} {student.last_name} 退学，课程 {course.course_code} 状态改为退课',
                target_table='student_courses',
                target_id=course.id,
                created_at=datetime.now()
            )
            db.session.add(course_log)

        db.session.commit()

        return jsonify({
            'code': 200,
            'data': {
                'student_id': student_id,
                'withdrawn_courses': len(courses)
            },
            'message': 'Student withdrawn successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'Failed to withdraw student: {str(e)}'}), 500
