from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from app.models.course import Course
from app.models.operation_log import OperationLog
from app.utils.file_helper import save_uploaded_file
from app.utils.response_helper import success_response, error_response
from typing import List, Dict, Any
import csv
import os
from datetime import datetime

class CourseService:
    @staticmethod
    def get_courses(
        db: Session,
        page: int = 1,
        per_page: int = 10,
        search: str = None,
        sort_by: str = None,
        sort_order: str = None
    ) -> Dict[str, Any]:
        """
        获取课程列表
        """
        query = db.query(Course)
        
        # 搜索条件
        if search:
            query = query.filter(
                or_(
                    Course.course_code.ilike(f"%{search}%"),
                    Course.course_name.ilike(f"%{search}%"),
                    Course.teacher.ilike(f"%{search}%")
                )
            )
        
        # 排序
        if sort_by and hasattr(Course, sort_by):
            sort_column = getattr(Course, sort_by)
            if sort_order == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)
        
        # 分页
        total = query.count()
        courses = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return {
            "total": total,
            "courses": [course.to_dict() for course in courses]
        }
    
    @staticmethod
    def create_course(db: Session, course_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """
        创建新课程
        """
        # 检查课程代码是否已存在
        if db.query(Course).filter(Course.course_code == course_data["course_code"]).first():
            return error_response("课程代码已存在")
        
        course = Course(**course_data)
        db.add(course)
        
        # 记录操作日志
        log = OperationLog(
            user_id=user_id,
            operation_type="create_course",
            operation_detail=f"创建课程: {course.course_code}",
            created_at=datetime.now()
        )
        db.add(log)
        
        db.commit()
        return success_response("课程创建成功")
    
    @staticmethod
    def update_course(
        db: Session,
        course_code: str,
        course_data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        更新课程信息
        """
        course = db.query(Course).filter(Course.course_code == course_code).first()
        if not course:
            return error_response("课程不存在")
        
        # 更新课程信息
        for key, value in course_data.items():
            setattr(course, key, value)
        
        # 记录操作日志
        log = OperationLog(
            user_id=user_id,
            operation_type="update_course",
            operation_detail=f"更新课程: {course_code}",
            created_at=datetime.now()
        )
        db.add(log)
        
        db.commit()
        return success_response("课程更新成功")
    
    @staticmethod
    def delete_courses(db: Session, course_codes: List[str], user_id: int) -> Dict[str, Any]:
        """
        批量删除课程
        """
        courses = db.query(Course).filter(Course.course_code.in_(course_codes)).all()
        if not courses:
            return error_response("未找到要删除的课程")
        
        # 删除课程
        for course in courses:
            db.delete(course)
        
        # 记录操作日志
        log = OperationLog(
            user_id=user_id,
            operation_type="delete_courses",
            operation_detail=f"删除课程: {', '.join(course_codes)}",
            created_at=datetime.now()
        )
        db.add(log)
        
        db.commit()
        return success_response("课程删除成功")
    
    @staticmethod
    def import_courses(db: Session, file_path: str, user_id: int) -> Dict[str, Any]:
        """
        从CSV文件导入课程
        """
        success_count = 0
        error_count = 0
        error_messages = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # 检查必填字段
                        required_fields = ["course_code", "course_name", "credit", "teacher"]
                        if not all(row.get(field) for field in required_fields):
                            error_count += 1
                            error_messages.append(f"第{reader.line_num}行: 缺少必填字段")
                            continue
                        
                        # 检查课程代码是否已存在
                        if db.query(Course).filter(Course.course_code == row["course_code"]).first():
                            error_count += 1
                            error_messages.append(f"第{reader.line_num}行: 课程代码 {row['course_code']} 已存在")
                            continue
                        
                        # 创建课程
                        course = Course(
                            course_code=row["course_code"],
                            course_name=row["course_name"],
                            credit=float(row["credit"]),
                            teacher=row["teacher"],
                            description=row.get("description", ""),
                            created_at=datetime.now()
                        )
                        db.add(course)
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"第{reader.line_num}行: {str(e)}")
                
                # 记录操作日志
                log = OperationLog(
                    user_id=user_id,
                    operation_type="import_courses",
                    operation_detail=f"导入课程: 成功 {success_count} 条, 失败 {error_count} 条",
                    created_at=datetime.now()
                )
                db.add(log)
                
                db.commit()
                
                return {
                    "success": True,
                    "message": f"导入完成: 成功 {success_count} 条, 失败 {error_count} 条",
                    "errors": error_messages
                }
                
        except Exception as e:
            return error_response(f"导入失败: {str(e)}")
        
        finally:
            # 删除临时文件
            if os.path.exists(file_path):
                os.remove(file_path) 