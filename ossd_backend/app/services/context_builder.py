"""
集中管理一切"占位符 → 值"的拼装逻辑
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, List
import random
from app.models import Student, Course
from app.models.student_course import StudentCourse
from app.services.learning_comments import LEARNING_COMMENTS


# ──────────────── 默认教师名单 ────────────────
DEFAULT_TEACHERS = {
    "ASM2O": "Emily Dawson",
    "AVI2O": "Jacob Whitman",
    "BAF3M": "Laura Bennett",
    "BAT4M": "Nathan Harris",
    "BBB4M": "Olivia Sanders",
    "BEP2O": "William Turner",
    "BOH4M": "Ashley Reed",
    "CHC2D": "Kevin Brooks",
    "CHV2O": "Megan Sullivan",
    "CIA4U": "Ryan Webster",
    "ENG3U": "Samantha Fraser",
    "ENG4U": "Thomas Blake",
    "ESLBO": "Julia Morton",
    "ESLCO": "Henry Patterson",
    "ESLDO": "Chloe Matthews",
    "ESLEO": "Liam Campbell",
    "GLC2O": "Nicole Jenkins",
    "HHS4U": "Andrew Clarke",
    "HSB4U": "Sophie Richardson",
    "LKBDU": "Mark Douglas",
    "MCR3U": "Natalie Graham",
    "MCV4U": "Stephen Moore",
    "MDM4U": "Isabelle Long",
    "MHF4U": "Benjamin Scott",
    "MPM2D": "Caroline Lewis",
    "OLC4O": "Zachary Palmer",
    "SBI3U": "Hailey Morgan",
    "SBI4U": "Peter Adams",
    "SCH3U": "Victoria Ellis",
    "SCH4U": "Daniel Carter",
    "SNC2D": "Brianna Taylor",
    "SPH3U": "Eric Thompson",
    "SPH4U": "Rachel Stevens",
}


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



def infer_learning_skills(score: int) -> dict[str, str]:
    """
    根据成绩推断 R/O/W/C/I/S 六项学习技能等级（E/G/S）
    返回字段：{"R": "E", "O": "E", ..., "S": "E"}
    """
    domains = ["R", "O", "W", "C", "I", "S"]  # Responsibility, Organization, ...

    if score >= 95:
        return {d: "E" for d in domains}

    elif 90 <= score < 95:
        downgrade = random.sample(domains, 1)
        return {d: ("G" if d in downgrade else "E") for d in domains}

    elif 85 <= score < 90:
        downgrade = random.sample(domains, 2)
        return {d: ("G" if d in downgrade else "E") for d in domains}

    elif 80 <= score < 85:
        downgrade = random.sample(domains, 4)
        return {d: ("G" if d in downgrade else "E") for d in domains}

    elif 75 <= score < 80:
        return {d: "G" for d in domains}

    elif 70 <= score < 75:
        downgrade = random.sample(domains, 1)
        return {d: ("S" if d in downgrade else "G") for d in domains}

    else:
        return {d: "S" for d in domains}


def generate_comment(levels: dict[str, str]) -> str:
    """
    根据每个领域的等级，从语料库中抽取评语并组合成自然段落。
    """
    segments = []
    for domain, grade in levels.items():
        options = LEARNING_COMMENTS.get(domain, {}).get(grade, [])
        if options:
            segments.append(random.choice(options))
    return " ".join(segments)

# ──────────────── Report Card ────────────────
def get_semester_from_date(date: datetime = None) -> str:
    """
    根据日期自动判断学期
    9-12月：第一学期 (1)
    1-3月：第二学期 (2)
    4-6月：第三学期 (3)
    """
    if date is None:
        date = datetime.now()
    
    month = date.month
    if 9 <= month <= 12:
        return "1"
    elif 1 <= month <= 3:
        return "2"
    elif 4 <= month <= 6:
        return "3"
    else:
        return "3"  # 7-8月默认返回第三学期

def build_report_card_context(
    student: Student,
    student_courses: List[StudentCourse],
    extra_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    构建用于 Report Card 的渲染上下文，结合数据库与手动填写数据。
    如果课程有期末成绩，则使用期末成绩单；否则使用期中成绩单。
    """
    base = build_student_context(student)

    # 自动判断学期（如果手动指定了则使用手动指定的值）
    semester = extra_data.get("semester")
    if semester is None:
        semester = get_semester_from_date()

    # 学校与顶部字段
    base.update({
        "semester": semester,
        "name": f"{student.last_name}, {student.first_name}",
        "OEN": student.oen,
        "Grade": student.grade.value if hasattr(student, "grade") else "",
        "homeroom": extra_data.get("homeroom", "N/A"),
        "principal": "Eric Tran",
        "schoolName": "Emerald Valley Academy",
        "schoolAddr": "170 Sheppard Ave E, North York, ON M2N 3A4",
        "schoolTel": "+1 437-268-6158",
        "schoolFax": "",
        "schoolBoard": "Private School",
        "schoolWeb": "https://evaschool.ca/",
        "schoolBSID": "BSID: 887678",
    })

    rows = []
    # 获取每个课程的 reporting 状态（如果手动指定了则使用手动指定的值）
    course_reporting = extra_data.get("course_reporting", {})

    for sc in student_courses:
        course = sc.course
        cid = str(sc.id)
        
        # 如果手动指定了该课程的 reporting 状态，则使用手动指定的值
        # 否则根据是否有期末成绩自动判断
        if cid in course_reporting:
            reporting_period = course_reporting[cid]
        else:
            reporting_period = "2" if sc.final_grade is not None else "1"

        mid_score = sc.midterm_grade or 0
        final_score = sc.final_grade or mid_score

        mid_skills = infer_learning_skills(mid_score)
        final_skills = infer_learning_skills(final_score)

        # 根据该课程的 reporting 生成不同的评语
        if reporting_period == "1":
            comment = generate_comment(mid_skills)
        else:
            comment = generate_comment(final_skills)

        rows.append({
            "courseTitle": course.course_name,
            "courseCode": course.course_code,
            "teacher": extra_data.get(f"{cid}_teacher", DEFAULT_TEACHERS.get(course.course_code, "TBD")),
            "midmark": sc.midterm_grade or "",
            "finalmark": sc.final_grade or "",
            "midmedian": "",
            "finalmedian": "",
            "midCR": "",
            "finalCR": f"{course.credit:.2f}",
            # 学习技能等级（优先使用手动填写）
            "midR": extra_data.get(f"{cid}_midR", mid_skills["R"]),
            "finalR": extra_data.get(f"{cid}_finalR", final_skills["R"]),
            "midO": extra_data.get(f"{cid}_midO", mid_skills["O"]),
            "finalO": extra_data.get(f"{cid}_finalO", final_skills["O"]),
            "midW": extra_data.get(f"{cid}_midW", mid_skills["W"]),
            "finalW": extra_data.get(f"{cid}_finalW", final_skills["W"]),
            "midC": extra_data.get(f"{cid}_midC", mid_skills["C"]),
            "finalC": extra_data.get(f"{cid}_finalC", final_skills["C"]),
            "midI": extra_data.get(f"{cid}_midI", mid_skills["I"]),
            "finalI": extra_data.get(f"{cid}_finalI", final_skills["I"]),
            "midS": extra_data.get(f"{cid}_midS", mid_skills["S"]),
            "finalS": extra_data.get(f"{cid}_finalS", final_skills["S"]),
            # 出勤
            "midClassMissed": extra_data.get(f"{cid}_midClassMissed", 0),
            "midTotalClass": extra_data.get(f"{cid}_midTotalClass", ""),
            "midTimesLate": extra_data.get(f"{cid}_midTimesLate", 0),
            "finalClassMissed": extra_data.get(f"{cid}_finalClassMissed", 0),
            "finalTotalClass": extra_data.get(f"{cid}_finalTotalClass", ""),
            "finalTimesLate": extra_data.get(f"{cid}_finalTimesLate", 0),
            # 评语（优先使用手动填写）
            "comment": extra_data.get(f"{cid}_comment", comment),
        })

    base["RC_COURSES"] = rows
    return base

# ──────────────── 示例数据 ────────────────
"""
extra_data = {
    "semester": "1",
    "reporting": "2",
    "homeroom": "N/A",
    "12_teacher": "Mr. Smith",
    "12_midR": "E", "12_finalR": "G",
    "12_midO": "G", "12_finalO": "G",
    "12_midW": "S", "12_finalW": "E",
    "12_midC": "N", "12_finalC": "S",
    "12_midI": "G", "12_finalI": "E",
    "12_midS": "S", "12_finalS": "G",
    "12_comment": "Excellent participation.",
    "12_midClassMissed": 0, "12_midTotalClass": 20, "12_midTimesLate": 1,
    "12_finalClassMissed": 1, "12_finalTotalClass": 40, "12_finalTimesLate": 0,

    "13_teacher": "Ms. Lee",
    "13_midR": "G", "13_finalR": "G",
    "13_midO": "S", "13_finalO": "S",
    "13_midW": "N", "13_finalW": "S",
    "13_midC": "S", "13_finalC": "S",
    "13_midI": "E", "13_finalI": "G",
    "13_midS": "G", "13_finalS": "G",
    "13_comment": "Needs improvement in homework.",
    "13_midClassMissed": 2, "13_midTotalClass": 18, "13_midTimesLate": 3,
    "13_finalClassMissed": 3, "13_finalTotalClass": 35, "13_finalTimesLate": 1,
}
"""
def build_transcript_context(student: Student, student_courses: List[StudentCourse], is_final: bool = False, extra_data: dict = {}) -> dict[str, str]:
    from datetime import datetime

    ctx: dict[str, str] = {}

    # 日期 & 页码支持手动覆写
    ctx["date"] = extra_data.get("date", datetime.now().strftime("%Y-%m-%d"))
    ctx["currPage"] = extra_data.get("currPage", "1")
    ctx["totalPage"] = extra_data.get("totalPage", "1")

    # 学生基础信息
    ctx["lastName"] = student.last_name
    ctx["firstName"] = student.first_name
    ctx["OEN"] = student.oen
    ctx["dobYear"] = str(student.birth_year)
    ctx["dobMonth"] = student.birth_month.value
    ctx["dobDay"] = str(student.birth_day)
    ctx["enrollYear"] = str(student.enrollment_year)
    ctx["enrollMonth"] = student.enrollment_month.value
    ctx["enrollDay"] = str(student.enrollment_day)

    # 自动 studentNo = YYMM + last2(student_id) + DOB
    suffix = f"{student.id:02d}"[-2:]
    dob_str = f"{student.birth_year % 100:02d}{student.birth_month.value:02d}{student.birth_day:02d}"
    ctx["studentNo"] = f"{student.enrollment_year % 100:02d}{student.enrollment_month.value:02d}{suffix}{dob_str}"

    # 学校字段
    ctx["schoolBoard"] = "Private"
    ctx["boardNumber"] = ""
    ctx["schoolName"] = "Emerald Valley Academy"
    ctx["schoolNo"] = "887678"

    # Final OST 额外字段
    if is_final:
        ctx["gradYear"] = str(student.expected_graduation_year)

    # 课程分发（最多23）
    ple_course = next((sc for sc in student_courses if sc.course_code == "PLE"), None)
    others = [sc for sc in student_courses if sc.course_code != "PLE"]
    rows = []

    # PLE 特殊行（放第1个）
    if ple_course:
        ple = ple_course
        rows.append({
            "code": "PLE",
            "course": "Equivalent Credits",
            "level": "",
            "grade": "EQV",
            "cr": str(int(ple.midterm_grade or 0)),
            "compul": str(int(ple.final_grade or 0)),
            "note": "",
            "month": str(ple.start_month.value),
            "year": f"*{ple.start_year}"
        })

    # 正常课程（本地/外校判断）
    for sc in others:
        c = sc.course
        rows.append({
            "code": c.course_code,
            "course": c.course_name,
            "level": (
                c.course_level.name[-1] if c.course_level.name.startswith("ESL")
                else c.course_level.name[-2:]
            ),
            "grade": str(sc.final_grade) if sc.final_grade is not None else "",
            "cr": f"{c.credit:.1f}",
            "compul": "X" if sc.is_compulsory else "",
            "note": "",
            "month": str(sc.start_month.value),
            "year": f"*{sc.start_year}" if not sc.is_local else str(sc.start_year)
        })

    rows = rows[:23]

    for i, row in enumerate(rows, start=1):
        for k, v in row.items():
            ctx[f"{k}{i}"] = v

    # 总学分统计
    total_cr = 0
    total_compul = 0
    for sc in student_courses:
        if sc.course_code == "PLE":
            total_cr += sc.midterm_grade or 0
            total_compul += sc.final_grade or 0
        else:
            total_cr += sc.course.credit or 0
            if sc.is_compulsory:
                total_compul += 1

    ctx["totalcr"] = str(int(total_cr))
    ctx["totalcompul"] = str(int(total_compul))

    return ctx
