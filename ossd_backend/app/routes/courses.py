from flask import Blueprint, request, jsonify
from app.models import Course, CourseLevel
from app import db
from app.utils import admin_required, parse_enum
print("✅ app.utils.parse_enum 已导入")
from sqlalchemy import or_
import csv
from io import StringIO
import pandas as pd


bp = Blueprint('courses', __name__)

@bp.route('', methods=['GET'])
def get_courses():
    try:
        keyword = request.args.get('keyword', '')
        course_code = request.args.get('course_code')
        course_levels = request.args.getlist('course_level')
        is_compulsory = request.args.get('is_compulsory', type=lambda x: x.lower() == 'true')
        sort_field = request.args.get('sort_field', 'course_code')
        sort_order = request.args.get('sort_order', 'asc')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)

        query = Course.query

        if course_code:
            query = query.filter(Course.course_code == course_code)
        elif keyword:
            query = query.filter(or_(
                Course.course_code.ilike(f'%{keyword}%'),
            ))

        if course_levels:
            parsed_levels = [parse_enum(CourseLevel, lvl) for lvl in course_levels]
            query = query.filter(Course.course_level.in_(parsed_levels))

        if is_compulsory is not None:
            query = query.filter(Course.is_compulsory == is_compulsory)

        if hasattr(Course, sort_field):
            sort_column = getattr(Course, sort_field)
            if sort_order.lower() == 'desc':
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)

        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        courses = pagination.items

        return jsonify({
            'code': 200,
            'data': {
                'total': pagination.total,
                'list': [course.to_dict() for course in courses]
            }
        })

    except ValueError as e:
        return jsonify({'code': 400, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'code': 500, 'message': f'Failed to get course list: {str(e)}'}), 500


@bp.route('', methods=['POST'])
@admin_required
def create_course():
    try:
        data = request.get_json()
        required_fields = ['course_code', 'course_name', 'description', 'course_level']
        for field in required_fields:
            if field not in data:
                return jsonify({'code': 400, 'message': f'Missing required field: {field}'}), 400

        print("[create_course] Received course_level from input:", data.get("course_level"))
        course_level = parse_enum(CourseLevel, data.get("course_level"))
        print("[create_course] Parsed course_level:", course_level)

        if not isinstance(course_level, CourseLevel):
            return jsonify({'code': 400, 'message': f'Invalid course_level: {data.get("course_level")}'}), 400

        credit = float(data['credit']) if data.get('credit') else None
        is_compulsory = str(data.get('is_compulsory', 'false')).lower() == 'true'

        course = Course(
            course_code=data['course_code'],
            course_name=data['course_name'],
            description=data['description'],
            credit=credit,
            course_level=course_level.value,
            is_compulsory=is_compulsory
        )
        
        

        db.session.add(course)
        db.session.commit()

        return jsonify({'code': 201, 'message': 'Course created successfully'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'Failed to create course: {str(e)}'}), 500

@bp.route('/<course_code>', methods=['PUT'])
@admin_required
def update_course(course_code):
    try:
        course = Course.query.get_or_404(course_code)
        data = request.get_json()

        if 'course_name' in data:
            course.course_name = data['course_name']
        if 'description' in data:
            course.description = data['description']
        if 'credit' in data:
            course.credit = float(data['credit']) if data['credit'] is not None else None
        if 'course_level' in data:
            course_level = parse_enum(CourseLevel, data.get('course_level'))
            if not isinstance(course_level, CourseLevel):
                return jsonify({'code': 400, 'message': f'Invalid course_level: {data.get("course_level")}'}), 400
            course.course_level = course_level.value
        if 'is_compulsory' in data:
            course.is_compulsory = bool(data['is_compulsory'])

        db.session.commit()
        return jsonify({'code': 200, 'message': 'Course updated successfully'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'Failed to update course: {str(e)}'}), 500


@bp.route('', methods=['DELETE'])
@admin_required
def delete_courses():
    try:
        if not request.is_json:
            return jsonify({'code': 400, 'message': 'Request must be JSON'}), 400

        data = request.get_json(silent=True) or {}
        course_codes = data.get('course_codes')

        if not course_codes or not isinstance(course_codes, list):
            return jsonify({'code': 400, 'message': 'Please provide course_codes as a list'}), 400

        deleted_count = Course.query.filter(Course.course_code.in_(course_codes)).delete(synchronize_session=False)
        db.session.commit()

        return jsonify({
            'code': 200,
            'data': {'deleted_count': deleted_count},
            'message': f'{deleted_count} course(s) deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'Failed to delete courses: {str(e)}'}), 500


@bp.route('/import', methods=['POST'])
@admin_required
def import_courses():
    try:
        print("🔍 开始导入课程...")
        if 'file' not in request.files:
            print("❌ 没有找到上传的文件")
            return jsonify({'code': 400, 'message': 'Please upload a file'}), 400

        file = request.files['file']
        filename = file.filename.lower()
        print(f"📁 文件名: {filename}")

        if filename.endswith('.csv'):
            print("📝 处理CSV文件...")
            content = file.read().decode('utf-8')
            csv_file = StringIO(content)
            df = pd.read_csv(csv_file)
        elif filename.endswith('.xlsx'):
            print("📝 处理Excel文件...")
            df = pd.read_excel(file)
        else:
            print(f"❌ 不支持的文件类型: {filename}")
            return jsonify({'code': 400, 'message': 'Please upload a CSV or Excel (.xlsx) file'}), 400

        print(f"📊 读取到的列: {df.columns.tolist()}")
        df.columns = [str(c).strip() for c in df.columns]
        print(f"📊 处理后的列: {df.columns.tolist()}")
        print(f"📊 数据行数: {len(df)}")

        created, updated, errors = [], [], []

        for idx, row in df.iterrows():
            try:
                print(f"\n🔍 处理第 {idx + 1} 行数据... 原始数据: {row}")
                course_code = str(row['course_code']).strip().upper()
                course_name = str(row['course_name']).strip()
                description = str(row['description']).strip() if pd.notna(row['description']) else ""
                credit = float(row['credit']) if pd.notna(row['credit']) else 0.0
                
                print(f"📝 课程代码: {course_code}")
                print(f"📝 课程名称: {course_name}")
                print(f"📝 学分: {credit}")
                
                # 处理course_level
                course_level = None
                course_level_raw = row['course_level']
                if pd.isna(course_level_raw):
                    course_level_str = ''
                else:
                    try:
                        course_level_str = str(int(float(course_level_raw)))
                    except Exception:
                        course_level_str = str(course_level_raw).strip()
                print(f"📝 原始课程级别: {course_level_raw}，标准化后: {course_level_str}")
                level_map = {
                    '1': 'ESL1', '2': 'ESL2', '3': 'ESL3', '4': 'ESL4', '5': 'ESL5',
                    '9': '09', '10': '10', '11': '11', '12': '12'
                }
                mapped_level = level_map.get(course_level_str)
                if mapped_level:
                    try:
                        course_level = parse_enum(CourseLevel, mapped_level)
                        print(f"✅ 解析课程级别: {course_level}")
                    except Exception as e:
                        print(f"❌ 解析课程级别失败: {e}")
                        errors.append({'row': idx + 2, 'course_code': course_code, 'error': f'course_level无效: {course_level_raw}'})
                        continue
                else:
                    print(f"❌ 未知course_level: {course_level_raw}")
                    errors.append({'row': idx + 2, 'course_code': course_code, 'error': f'course_level无效: {course_level_raw}'})
                    continue
                # 处理is_compulsory
                is_compulsory = False
                if pd.notna(row.get('is_compulsory')):
                    is_compulsory = str(row['is_compulsory']).lower() == 'true'
                print(f"📝 是否必修: {is_compulsory}")

                existing = Course.query.filter_by(course_code=course_code).first()
                if existing:
                    print(f"📝 更新已存在的课程: {course_code}")
                    # 更新
                    existing.course_name = course_name
                    existing.description = description
                    existing.credit = credit
                    existing.course_level = course_level.value
                    existing.is_compulsory = is_compulsory
                    updated.append(course_code)
                else:
                    print(f"📝 创建新课程: {course_code}")
                    # 新增
                    course = Course(
                        course_code=course_code,
                        course_name=course_name,
                        description=description,
                        credit=credit,
                        course_level=course_level.value,
                        is_compulsory=is_compulsory
                    )
                    db.session.add(course)
                    created.append(course_code)

            except Exception as e:
                print(f"❌ 处理第 {idx + 1} 行时出错: {str(e)}")
                db.session.rollback()
                errors.append({'row': idx + 2, 'course_code': row.get('course_code', ''), 'error': str(e)})

        # 在所有数据处理完成后提交事务
        db.session.commit()

        print(f"\n📊 导入结果统计:")
        print(f"✅ 创建: {len(created)} 个课程")
        print(f"📝 更新: {len(updated)} 个课程")
        print(f"❌ 错误: {len(errors)} 个")

        return jsonify({
            'code': 201,
            'data': {
                'created': created,
                'updated': updated,
                'errors': errors
            }
        }), 201

    except Exception as e:
        print(f"❌ 导入过程中发生错误: {str(e)}")
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'Failed to import courses: {str(e)}'}), 500
