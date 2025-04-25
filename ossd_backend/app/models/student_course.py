from app import db
from datetime import datetime, UTC
from enum import Enum
from app.models.student import Month

class CourseStatus(Enum):
    IN_PROGRESS = 'IN_PROGRESS'
    GRADUATED = 'GRADUATED'
    WITHDRAWN = 'WITHDRAWN'

class StudentCourse(db.Model):
    __tablename__ = 'student_courses'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='关联记录ID')
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, comment='学生ID')
    course_code = db.Column(db.String(20), db.ForeignKey('courses.course_code', ondelete='CASCADE'), nullable=False, comment='课程代码')
    status = db.Column(db.Enum(CourseStatus), nullable=False, default=CourseStatus.IN_PROGRESS, comment='课程状态')

    start_year = db.Column(db.Integer, nullable=False, comment='课程开始年份')
    start_month = db.Column(db.Enum(Month), nullable=False, comment='课程开始月份')
    start_day = db.Column(db.Integer, nullable=False, comment='课程开始日期')

    midterm_grade = db.Column(db.Integer, comment='期中成绩')
    final_grade = db.Column(db.Integer, comment='期末成绩')
    report_card_date = db.Column(db.Date, default=lambda: datetime.now(UTC).date(), comment='Report Card发布日期')

    is_compulsory = db.Column(db.Boolean, nullable=False, default=False, comment='该课程是否为该学生的必修')
    is_local = db.Column(db.Boolean, nullable=False, default=True, comment='是否为本校修读')
    completion_date = db.Column(db.Date, comment='课程完成时间')
    override_credit = db.Column(db.Numeric(4, 1), nullable=True, comment='覆盖课程学分（EQV或特殊情况）')

    # 关联关系
    student = db.relationship('Student', back_populates='courses')
    course = db.relationship('Course', back_populates='students')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'course_code': self.course_code,
            'status': self.status.value,
            'start_year': self.start_year,
            'start_month': self.start_month.value,
            'start_day': self.start_day,
            'midterm_grade': self.midterm_grade,
            'final_grade': self.final_grade,
            'report_card_date': self.report_card_date.isoformat() if self.report_card_date else None,
            'is_compulsory': self.is_compulsory,
            'is_local': self.is_local,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'override_credit': float(self.override_credit) if self.override_credit is not None else None
        }
