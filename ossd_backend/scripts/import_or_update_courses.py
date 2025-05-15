import pandas as pd
from decimal import Decimal
from datetime import datetime
from app import create_app
from app.models import db, Student, StudentCourse, CourseStatus, Month

app = create_app()

def run_import(file_path: str):
    df = pd.read_excel(file_path)
    df.columns = [str(col).strip() for col in df.columns]

    status_map = {
        "REGISTERED": CourseStatus.IN_PROGRESS,
        "IN_PROGRESS": CourseStatus.IN_PROGRESS,
        "COMPLETED": CourseStatus.COMPLETED,
        "GRADUATED": CourseStatus.COMPLETED,
    }
    month_map = {m.name: m for m in Month}

    created, updated, skipped, errors = [], [], [], []

    with app.app_context():
        name_map = {
            f"{s.last_name.strip()} {s.first_name.strip()}": s.id
            for s in Student.query.all()
        }

        for i, row in df.iterrows():
            try:
                full_name = str(row["学生姓名"]).strip()
                course_code = str(row["课程代码"]).strip()

                if full_name not in name_map:
                    raise ValueError(f"Student not found: {full_name}")
                student_id = name_map[full_name]

                existing = StudentCourse.query.filter_by(
                    student_id=student_id, course_code=course_code
                ).first()

                status = status_map[str(row["状态"]).strip().upper()]
                start_year = int(row["起始年"])
                start_month = month_map[str(row["起始月"]).strip().upper()]
                start_day = int(row["起始日"])
                is_compulsory = bool(int(row["Is Compulsory （1 必修; 0 非必修)"]))
                is_local = bool(int(row["Is Local(1代表是本校修的学分，0代表不是)"]))

                override_credit = None
                if "Override Credit（重修的时候填写）" in row and pd.notna(row["Override Credit（重修的时候填写）"]):
                    override_credit = Decimal(str(row["Override Credit（重修的时候填写）"]))
                    if override_credit < 0 or override_credit > 4:
                        raise ValueError("Invalid override_credit")

                if existing:
                    if existing.status == CourseStatus.IN_PROGRESS:
                        changed = False
                        if pd.notna(row["Midterm"]):
                            existing.midterm_grade = Decimal(row["Midterm"])
                            changed = True
                        if pd.notna(row["Final"]):
                            existing.final_grade = Decimal(row["Final"])
                            changed = True
                        if changed:
                            updated.append((full_name, course_code))
                        else:
                            skipped.append((full_name, course_code))
                    else:
                        skipped.append((full_name, course_code))
                    continue

                # 新增课程
                sc = StudentCourse(
                    student_id=student_id,
                    course_code=course_code,
                    start_year=start_year,
                    start_month=start_month,
                    start_day=start_day,
                    status=status,
                    is_compulsory=is_compulsory,
                    is_local=is_local,
                    override_credit=override_credit,
                )

                if status == CourseStatus.COMPLETED:
                    sc.midterm_grade = Decimal(row["Midterm"])
                    sc.final_grade = Decimal(row["Final"])
                    sc.completion_date = pd.to_datetime(
                        row["Completion Date（这个日期是和OST上出现的日期一致）"]
                    ).date()
                    sc.report_card_date = pd.to_datetime(
                        row["Report Card Date（可以直接参照completion date）"]
                    ).date()

                db.session.add(sc)
                created.append((full_name, course_code))

            except Exception as e:
                errors.append((i + 2, full_name if 'full_name' in locals() else '', course_code if 'course_code' in locals() else '', str(e)))

        db.session.commit()

    # 打印汇总
    print(f"\n✅ 添加新课程：{len(created)} 条")
    for name, code in created:
        print(f"  - 新增：{name} - {code}")

    print(f"\n🟡 成绩更新：{len(updated)} 条")
    for name, code in updated:
        print(f"  - 更新：{name} - {code}")

    print(f"\n⏭️ 跳过已有：{len(skipped)} 条")
    for name, code in skipped:
        print(f"  - 已有：{name} - {code}")

    if errors:
        print(f"\n❌ 错误记录：{len(errors)} 条")
        for rownum, name, code, err in errors:
            print(f"  - 第 {rownum} 行（{name}-{code}）：{err}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python import_or_update_courses.py <Excel file path>")
    else:
        run_import(sys.argv[1])
