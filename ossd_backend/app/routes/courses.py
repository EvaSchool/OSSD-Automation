from flask import Blueprint, request, jsonify
from app.models import Course
from app import db
from app.utils import admin_required
from sqlalchemy import or_
import csv
from io import StringIO

bp = Blueprint('courses', __name__)

@bp.route('', methods=['GET'])
def get_courses():
    """Get course list (with pagination, filtering, and sorting)"""
    try:
        # Get query parameters
        keyword = request.args.get('keyword', '')
        course_levels = request.args.getlist('course_level')
        is_compulsory = request.args.get('is_compulsory', type=lambda x: x.lower() == 'true')
        sort_field = request.args.get('sort_field', 'course_code')
        sort_order = request.args.get('sort_order', 'asc')
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)

        # Build query
        query = Course.query

        # Keyword search
        if keyword:
            query = query.filter(
                or_(
                    Course.course_code.ilike(f'%{keyword}%'),
                    Course.course_name.ilike(f'%{keyword}%')
                )
            )

        # Course level filter
        if course_levels:
            query = query.filter(Course.course_level.in_(course_levels))

        # Compulsory filter
        if is_compulsory is not None:
            query = query.filter(Course.is_compulsory == is_compulsory)

        # Sorting
        if hasattr(Course, sort_field):
            sort_column = getattr(Course, sort_field)
            if sort_order.lower() == 'desc':
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)

        # Pagination
        pagination = query.paginate(page=page, per_page=page_size, error_out=False)
        courses = pagination.items

        return jsonify({
            'code': 200,
            'data': {
                'total': pagination.total,
                'list': [course.to_dict() for course in courses]
            }
        })

    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'Failed to get course list: {str(e)}'
        }), 500

@bp.route('', methods=['POST'])
@admin_required
def create_course():
    """Create a new course"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['course_code', 'course_name', 'description', 'credit', 'course_level']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'code': 400,
                    'message': f'Missing required field: {field}'
                }), 400

        # Create course
        course = Course(
            course_code=data['course_code'],
            course_name=data['course_name'],
            description=data['description'],
            credit=data['credit'],
            course_level=data['course_level'],
            is_compulsory=data.get('is_compulsory', False)
        )

        db.session.add(course)
        db.session.commit()

        return jsonify({
            'code': 201,
            'message': 'Course created successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'Failed to create course: {str(e)}'
        }), 500

@bp.route('/<course_code>', methods=['PUT'])
@admin_required
def update_course(course_code):
    """Update course information"""
    try:
        course = Course.query.get_or_404(course_code)
        data = request.get_json()

        # Update course information
        if 'course_name' in data:
            course.course_name = data['course_name']
        if 'description' in data:
            course.description = data['description']
        if 'credit' in data:
            course.credit = data['credit']
        if 'course_level' in data:
            course.course_level = data['course_level']
        if 'is_compulsory' in data:
            course.is_compulsory = data['is_compulsory']

        db.session.commit()

        return jsonify({
            'code': 200,
            'message': 'Course updated successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'Failed to update course: {str(e)}'
        }), 500

@bp.route('', methods=['DELETE'])
@admin_required
def delete_courses():
    """Delete courses in batch"""
    try:
        data = request.get_json()
        course_codes = data.get('course_codes', [])

        if not course_codes:
            return jsonify({
                'code': 400,
                'message': 'Please provide course codes to delete'
            }), 400

        # Delete courses
        deleted_count = Course.query.filter(Course.course_code.in_(course_codes)).delete()
        db.session.commit()

        return jsonify({
            'code': 200,
            'data': {'deleted_count': deleted_count},
            'message': 'Courses deleted successfully'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'Failed to delete courses: {str(e)}'
        }), 500

@bp.route('/import', methods=['POST'])
@admin_required
def import_courses():
    """Import courses from CSV file"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'message': 'Please upload a file'
            }), 400

        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({
                'code': 400,
                'message': 'Please upload a CSV file'
            }), 400

        # Read CSV file
        content = file.read().decode('utf-8')
        csv_file = StringIO(content)
        reader = csv.DictReader(csv_file)

        success_count = 0
        failed_rows = []

        for row_num, row in enumerate(reader, start=2):  # Start from row 2 (skip header)
            try:
                course = Course(
                    course_code=row['course_code'],
                    course_name=row['course_name'],
                    description=row['description'],
                    credit=float(row['credit']),
                    course_level=row['course_level'],
                    is_compulsory=row.get('is_compulsory', 'false').lower() == 'true'
                )
                db.session.add(course)
                success_count += 1
            except Exception as e:
                failed_rows.append({
                    'row': row_num,
                    'errors': [str(e)]
                })

        db.session.commit()

        return jsonify({
            'code': 201,
            'data': {
                'success_count': success_count,
                'failed_rows': failed_rows
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'Failed to import courses: {str(e)}'
        }), 500 