from app import db
from datetime import datetime
from enum import Enum

class Month(Enum):
    JAN = 'JAN'
    FEB = 'FEB'
    MAR = 'MAR'
    APR = 'APR'
    MAY = 'MAY'
    JUN = 'JUN'
    JUL = 'JUL'
    AUG = 'AUG'
    SEP = 'SEP'
    OCT = 'OCT'
    NOV = 'NOV'
    DEC = 'DEC'

class GraduationStatus(Enum):
    IN_PROGRESS = 'IN_PROGRESS'
    GRADUATED = 'GRADUATED'
    WITHDRAWN = 'WITHDRAWN'


class Student(db.Model):
    __tablename__ = 'students'
    
    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='学生唯一ID')
    last_name = db.Column(db.String(50), nullable=False, comment='学生姓氏')
    first_name = db.Column(db.String(50), nullable=False, comment='学生名字')
    OEN = db.Column(db.String(9), unique=True, nullable=False, comment='OEN（9位数字，显示时格式化为XXX-XXX-XXX）')
    birth_year = db.Column(db.Integer, nullable=False, comment='出生年份')
    birth_month = db.Column(db.Enum(Month), nullable=False, comment='出生月份')
    birth_day = db.Column(db.Integer, nullable=False, comment='出生日期')
    enrollment_year = db.Column(db.Integer, nullable=False, comment='入学年份')
    enrollment_month = db.Column(db.Enum(Month), nullable=False, comment='入学月份')
    enrollment_day = db.Column(db.Integer, nullable=False, comment='入学日期')
    expected_graduation_year = db.Column(db.Integer, nullable=False, comment='预计毕业年份')
    expected_graduation_month = db.Column(db.Enum(Month), nullable=False, default=Month.JUN, comment='预计毕业月份')
    expected_graduation_day = db.Column(db.Integer, nullable=False, default=30, comment='预计毕业日期')
    address = db.Column(db.Text, comment='学生地址（格式：街道, 城市, 省, 国家）')
    graduation_status = db.Column(db.Enum(GraduationStatus), nullable=False, default=GraduationStatus.IN_PROGRESS, comment='毕业状态')
    volunteer_hours = db.Column(db.Integer, nullable=False, default=0, comment='义工时数（≥0）')
    
    # 关联关系
    courses = db.relationship('StudentCourse', back_populates='student', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'student_id': self.student_id,
            'last_name': self.last_name,
            'first_name': self.first_name,
            'OEN': self.OEN,
            'birth_year': self.birth_year,
            'birth_month': self.birth_month.value,
            'birth_day': self.birth_day,
            'enrollment_year': self.enrollment_year,
            'enrollment_month': self.enrollment_month.value,
            'enrollment_day': self.enrollment_day,
            'expected_graduation_year': self.expected_graduation_year,
            'expected_graduation_month': self.expected_graduation_month.value,
            'expected_graduation_day': self.expected_graduation_day,
            'address': self.address,
            'graduation_status': self.graduation_status.value,
            'volunteer_hours': self.volunteer_hours
        } 