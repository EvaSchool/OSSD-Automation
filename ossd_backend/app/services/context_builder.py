"""
集中管理一切“占位符 → 值”的拼装逻辑
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, List

from app.models import Student, Course


# ──────────────── 基础学生字段 ────────────────
def build_student_context(stu: Student) -> Dict[str, Any]:
    return {
        # 基本信息
        "STUDENT_FIRSTNAME": stu.first_name,
        "STUDENT_LASTNAME": stu.last_name,
        "STUDENT_FULLNAME": f"{stu.last_name}, {stu.first_name}",
        "OEN": f"{stu.oen[:3]}-{stu.oen[3:6]}-{stu.oen[6:]}",
        "DOB": f"{stu.birth_year}-{stu.birth_month.value}-{stu.birth_day:02d}",
        "ENROLL_DATE": f"{stu.enrollment_year}-{stu.enrollment_month.value}-{stu.enrollment_day:02d}",
        "EXPECTED_GRAD": f"{stu.expected_graduation_year}-{stu.expected_graduation_month.value}-{stu.expected_graduation_day:02d}",
        "GRADE": stu.grade.value if hasattr(stu, "grade") else "",
        # 生成日期
        "TODAY": datetime.now().strftime("%Y-%b-%d"),
    }


# ──────────────── Welcome Letter 登录信息 ────────────────
def build_login_context(stu: Student) -> Dict[str, str]:
    username = (stu.first_name + stu.last_name).lower()
    password = f"Welcome2{stu.first_name[0].upper()}{stu.last_name[0].upper()}!"
    return {"USERNAME": username, "PASSWORD": password}


# ──────────────── 课程清单（字符串列表） ────────────────
def build_course_list_context(courses: List[Course]) -> Dict[str, Any]:
    """供 {{ course }} 循环或单元格换行列表"""
    lines = [f"{c.course_name} ({c.course_code})" for c in courses]
    return {"COURSE_LIST": lines}


# ──────────────── 课程表格 / 预测成绩 for-循环 ────────────────
def build_course_table_context(courses: List[Course]) -> Dict[str, Any]:
    """供 PredictedGrades 表格使用"""
    return {
        "SELECTED_COURSES": [
            {
                "COURSE_NAME": c.course_name,
                "COURSE_CODE": c.course_code,
                "COURSE_LEVEL": c.course_level.value,
                # 预测成绩、完成日期由调用方覆盖
                "PREDICTED_GRADE": "",
                "COMPLETION_DATE": "",
            }
            for c in courses
        ]
    }


# ──────────────── 课程描述列表 ────────────────
def build_course_desc_context(courses: List[Course]) -> Dict[str, Any]:
    """供 WelcomeLetter 课程描述 for-循环使用"""
    return {
        "SELECTED_COURSES": [
            {
                "COURSE_CODE": c.course_code,
                "COURSE_DESCRIPTION": c.description,
            }
            for c in courses
        ]
    }
