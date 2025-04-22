from app import db
from enum import Enum
from datetime import date
from app.models.student import Month           # 已有枚举
# --------------------------------------------------

class CourseStatus(Enum):
    REGISTERED = 'REGISTERED'      # 已选未开课
    IN_PROGRESS = 'IN_PROGRESS'    # 上课中
    COMPLETED   = 'COMPLETED'      # 已结课

class StudentCourse(db.Model):
    __tablename__ = 'student_courses'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='关联记录ID')
    student_id  = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    course_code = db.Column(db.String(20), db.ForeignKey('courses.course_code', ondelete='CASCADE'), nullable=False)
    # —— 业务字段 ——
    status   = db.Column(db.Enum(CourseStatus), nullable=False, default=CourseStatus.REGISTERED)
    start_year  = db.Column(db.Integer, nullable=False)
    start_month = db.Column(db.Enum(Month), nullable=False)
    start_day   = db.Column(db.Integer, nullable=False)
    midterm_grade = db.Column(db.Integer)   # 0‑100，可为 NULL
    final_grade   = db.Column(db.Integer)   # 0‑100，可为 NULL
    report_card_date = db.Column(db.Date)   # 发布 RC 的日期，可为 NULL

    # —— 关系映射 ——
    student = db.relationship('Student', back_populates='courses')
    course  = db.relationship('Course',  back_populates='students')

    # —— 联合唯一约束：同一学生同一课程只能选一次 ——
    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_code', name='uq_student_course'),
    )

    # --------------------------------------------------
    # 自动维护 status
    # --------------------------------------------------
    def _update_status(self):
        """根据分数自动流转状态"""
        if self.final_grade is not None:
            self.status = CourseStatus.COMPLETED
        elif self.midterm_grade is not None:
            self.status = CourseStatus.IN_PROGRESS
        else:
            self.status = CourseStatus.REGISTERED

    # 在写回数据库前统一调用
    def set_midterm(self, grade: int):
        self.midterm_grade = grade
        self.report_card_date = date.today()
        self._update_status()

    def set_final(self, grade: int):
        if self.midterm_grade is None:
            raise ValueError('Mid‑term grade must be set before final grade')
        self.final_grade = grade
        self.report_card_date = date.today()
        self._update_status()

    # --------------------------------------------------
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
            'report_card_date': (
                self.report_card_date.isoformat() if self.report_card_date else None
            )
        }
