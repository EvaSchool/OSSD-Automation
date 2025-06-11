from flask import Blueprint, jsonify, request
from app.models.student import Student, Month, GraduationStatus
from app import db
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from app.utils import parse_enum, month_str_to_num
import random
import pandas as pd
from io import StringIO

bp = Blueprint('students', __name__)

@bp.route('/students', methods=['GET'])
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

@bp.route('/students/<int:student_id>', methods=['GET'])
@jwt_required()
def get_student(student_id):
    student = Student.query.get_or_404(student_id)
    return jsonify(student.to_dict())

@bp.route('/students', methods=['POST'])
@jwt_required()
def create_student():
    data = request.get_json()
    last_name = data.get('last_name')
    first_name = data.get('first_name')
    birth_year = data.get('birth_year')
    birth_month = data.get('birth_month')
    birth_day = data.get('birth_day')
    enrollment_year = data.get('enrollment_year')
    enrollment_month = data.get('enrollment_month')
    # 自动生成 student_number: YYMM + 随机两位数字 + DOB
    random_suffix = f"{random.randint(0, 99):02d}"
    dob_str = f"{birth_year % 100:02d}{month_str_to_num(birth_month):02d}{int(birth_day):02d}"
    student_number = f"{enrollment_year % 100:02d}{month_str_to_num(enrollment_month):02d}{random_suffix}{dob_str}"
    try:
        student = Student(
            student_number=student_number,
            last_name=last_name,
            first_name=first_name,
            OEN=data['OEN'],
            birth_year=birth_year,
            birth_month=parse_enum(Month, birth_month),
            birth_day=birth_day,
            enrollment_year=enrollment_year,
            enrollment_month=parse_enum(Month, enrollment_month),
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

@bp.route('/students/<int:student_id>', methods=['PUT'])
@jwt_required()
def update_student(student_id):
    student = Student.query.get_or_404(student_id)
    data = request.get_json()
    student_number = data.get('student_number')
    last_name = data.get('last_name')
    first_name = data.get('first_name')

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

    student.student_number = student_number
    student.last_name = last_name
    student.first_name = first_name

    db.session.commit()
    return jsonify(student.to_dict())

@bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    return '', 204

@bp.route('/import', methods=['POST'])
@jwt_required()
def import_students():
    print("🔍 [import_students] 开始处理导入请求")
    if 'file' not in request.files:
        print("❌ [import_students] 未上传文件")
        return jsonify({'error': '请上传文件'}), 400
    file = request.files['file']
    filename = file.filename.lower()
    print(f"📁 [import_students] 文件名: {filename}")
    if filename.endswith('.csv'):
        content = file.read().decode('utf-8')
        csv_file = StringIO(content)
        df = pd.read_csv(csv_file)
    elif filename.endswith('.xlsx'):
        df = pd.read_excel(file)
    else:
        print("❌ [import_students] 文件类型不支持")
        return jsonify({'error': '请上传CSV或Excel文件'}), 400

    # 统一列名小写
    df.columns = [str(c).strip().lower() for c in df.columns]
    print(f"📊 [import_students] 列名: {df.columns.tolist()}")
    if 'oen' not in df.columns:
        print("❌ [import_students] 缺少OEN列")
        return jsonify({'error': 'CSV文件缺少OEN列'}), 400
    updated, created, conflict, errors = [], [], [], []
    for idx, row in df.iterrows():
        try:
            oen = str(row['oen']).strip()
            print(f"➡️ [import_students] 处理第{idx+2}行，OEN: {oen}")
            student = Student.query.filter_by(OEN=oen).first()
            # 取student_number并检查唯一性
            new_number = str(row['student_number']).strip() if 'student_number' in row and pd.notna(row['student_number']) else None
            if new_number:
                conflict_student = Student.query.filter(Student.student_number == new_number, Student.OEN != oen).first()
                if conflict_student:
                    print(f"❌ [import_students] student_number冲突: {new_number} 已被OEN={conflict_student.OEN}占用")
                    conflict.append({'row': idx+2, 'oen': oen, 'student_number': new_number, 'conflict_oen': conflict_student.OEN})
                    db.session.rollback()
                    continue
            # 字段准备
            fields = ['student_number','last_name','first_name','oen','birth_year','birth_month','birth_day','enrollment_year','enrollment_month','enrollment_day','expected_graduation_year','expected_graduation_month','expected_graduation_day','address','graduation_status','volunteer_hours','grade','remark']
            data = {}
            for field in fields:
                if field in row and pd.notna(row[field]):
                    data[field] = row[field]
            # 类型转换
            int_fields = ['birth_year','birth_day','enrollment_year','enrollment_day','expected_graduation_year','expected_graduation_day','volunteer_hours']
            for f in int_fields:
                if f in data:
                    try:
                        data[f] = int(data[f])
                    except Exception:
                        pass
            # 枚举转换
            if 'birth_month' in data:
                data['birth_month'] = parse_enum(Month, str(data['birth_month']))
            if 'enrollment_month' in data:
                data['enrollment_month'] = parse_enum(Month, str(data['enrollment_month']))
            if 'expected_graduation_month' in data:
                data['expected_graduation_month'] = parse_enum(Month, str(data['expected_graduation_month']))
            if 'graduation_status' in data:
                data['graduation_status'] = parse_enum(GraduationStatus, str(data['graduation_status']))
            if 'grade' in data:
                from app.models.student import GradeLevel
                data['grade'] = parse_enum(GradeLevel, str(data['grade']))
            if student:
                # 更新所有字段
                for k, v in data.items():
                    setattr(student, k, v)
                print(f"✅ [import_students] 已更新学生: {oen}")
                updated.append(oen)
            else:
                # 新增前再次检查student_number唯一性
                if new_number:
                    conflict_student = Student.query.filter(Student.student_number == new_number).first()
                    if conflict_student:
                        print(f"❌ [import_students] student_number冲突: {new_number} 已被OEN={conflict_student.OEN}占用")
                        conflict.append({'row': idx+2, 'oen': oen, 'student_number': new_number, 'conflict_oen': conflict_student.OEN})
                        db.session.rollback()
                        continue
                # 新增
                try:
                    student = Student(**data)
                    db.session.add(student)
                    print(f"🆕 [import_students] 已新增学生: {oen}")
                    created.append(oen)
                except Exception as e:
                    print(f"❌ [import_students] 新增学生失败: {e}")
                    errors.append({'row': idx+2, 'oen': oen, 'error': str(e)})
                    db.session.rollback()
                    continue
        except Exception as e:
            print(f"❌ [import_students] 行{idx+2}出错: {e}")
            errors.append({'row': idx+2, 'oen': row.get('oen', ''), 'error': str(e)})
            db.session.rollback()
            continue
    try:
        db.session.commit()
    except Exception as e:
        print(f"❌ [import_students] commit失败: {e}")
        errors.append({'commit_error': str(e)})
        db.session.rollback()
    print(f"📦 [import_students] 完成，更新: {len(updated)}，新增: {len(created)}，冲突: {len(conflict)}，错误: {len(errors)}")
    return jsonify({
        'code': 200,
        'updated': updated,
        'created': created,
        'conflict': conflict,
        'errors': errors
    })
