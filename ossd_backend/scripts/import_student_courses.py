import os
import sys

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

import pandas as pd
from decimal import Decimal
from datetime import datetime
from app import create_app, db
from app.models import Student, Course, StudentCourse, CourseStatus, Month

app = create_app()

# 文件路径
EXCEL_FILE = "/home/devbox/project/data.xlsx"  # 请替换为您的Excel文件的实际路径

# 状态映射：直接使用原样（已统一为 IN_PROGRESS / COMPLETED / WITHDRAWN）
VALID_STATUSES = {"IN_PROGRESS", "COMPLETED", "WITHDRAWN"}

# 月份映射（大写）
MONTHS = {m.name: m for m in Month}

def load_students_by_oen():
    """构建 OEN → student_id 映射"""
    return {s.OEN.replace("-", ""): s for s in Student.query.all()}

def run_import():
    df = pd.read_excel(EXCEL_FILE)
    df.columns = [str(c).strip() for c in df.columns]

    success, skipped, errors = [], [], []

    with app.app_context():
        oen_map = load_students_by_oen()

        for idx, row in df.iterrows():
            try:
                raw_oen = str(row["OEN"]).replace("-", "").strip()
                if raw_oen not in oen_map:
                    errors.append((idx+2, "找不到学生", row["学生姓名"], raw_oen))
                    continue
                student = oen_map[raw_oen]

                course_code = str(row["课程代码"]).strip().upper()
                status = str(row["状态"]).strip().upper()
                if status not in VALID_STATUSES:
                    raise ValueError(f"无效的课程状态: {status}")

                exists = StudentCourse.query.filter_by(student_id=student.student_id, course_code=course_code).first()
                if exists:
                    skipped.append((student.first_name, student.last_name, course_code))
                    continue

                start_year = int(row["起始年"])
                start_month = MONTHS[str(row["起始月"]).strip().upper()]
                start_day = int(row["起始日"])

                midterm = row.get("Midterm")
                final = row.get("Final")
                completion_date = pd.to_datetime(row.get("Completion Date"), errors="coerce")
                report_card_date = pd.to_datetime(row.get("Report Card Date"), errors="coerce")

                is_compulsory = bool(int(row.get("Is Compulsory ", 0)))
                is_local = bool(int(row.get("Is Local", 0)))
                earned_credit = row.get("Earned Credit")
                override_credit = row.get("Override Credit")

                sc = StudentCourse(
                    student_id=student.student_id,
                    course_code=course_code,
                    start_year=start_year,
                    start_month=start_month,
                    start_day=start_day,
                    status=CourseStatus[status],
                    is_compulsory=is_compulsory,
                    is_local=is_local,
                )

                if pd.notna(midterm):
                    sc.midterm_grade = Decimal(midterm)
                if pd.notna(final):
                    sc.final_grade = Decimal(final)
                if pd.notna(completion_date):
                    sc.completion_date = completion_date.date()
                if pd.notna(report_card_date):
                    sc.report_card_date = report_card_date.date()
                if pd.notna(override_credit):
                    sc.override_credit = Decimal(override_credit)

                db.session.add(sc)
                success.append((student.first_name, student.last_name, course_code))

            except Exception as e:
                errors.append((idx+2, str(e), row.get("学生姓名", ""), row.get("课程代码", "")))

        db.session.commit()

    print("\n✅ 成功添加:")
    for fn, ln, code in success:
        print(f"  - {ln} {fn} - {code}")

    print("\n⏭️ 跳过已有:")
    for fn, ln, code in skipped:
        print(f"  - {ln} {fn} - {code}")

    print("\n❌ 错误记录:")
    for rownum, msg, name, code in errors:
        print(f"  - 第 {rownum} 行: {name} - {code}：{msg}")


if __name__ == "__main__":
    run_import()
