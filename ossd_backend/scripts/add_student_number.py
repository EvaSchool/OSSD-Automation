import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import random
from app import create_app, db
from app.models.student import Student
from app.utils import month_str_to_num

app = create_app()
with app.app_context():
    students = Student.query.all()
    for student in students:
        # 跳过已填充的
        if student.student_number:
            continue
        random_suffix = f"{random.randint(0, 99):02d}"
        dob_str = f"{student.birth_year % 100:02d}{month_str_to_num(student.birth_month)}{int(student.birth_day):02d}"
        student_number = f"{student.enrollment_year % 100:02d}{month_str_to_num(student.enrollment_month)}{random_suffix}{dob_str}"
        student.student_number = student_number
    db.session.commit()
    print("所有学生的 student_number 已生成并填充。")