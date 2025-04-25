from app import db
from enum import Enum

class CourseLevel(Enum):
    GRADE_09 = '09'
    GRADE_10 = '10'
    GRADE_11 = '11'
    GRADE_12 = '12'
    ESL_1 = 'ESL1'
    ESL_2 = 'ESL2'
    ESL_3 = 'ESL3'
    ESL_4 = 'ESL4'
    ESL_5 = 'ESL5'
    EQV = 'EQV'  # 转学分课程

class Course(db.Model):
    __tablename__ = 'courses'
    
    course_code = db.Column(db.String(20), primary_key=True, comment='Course code')
    course_name = db.Column(db.String(100), nullable=False, comment='Course name')
    description = db.Column(db.Text, nullable=False, comment='Course description')
    credit = db.Column(db.Numeric(4,1), nullable=True, comment='Course credit (EQV courses can be null)')
    course_level = db.Column(db.String(10), nullable=False, comment='Course level')
    is_compulsory = db.Column(db.Boolean, nullable=False, default=False, comment='Whether the course is compulsory')
    
    # Relationships
    students = db.relationship('StudentCourse', back_populates='course', cascade='all, delete-orphan')
    
    def to_dict(self):
        print(f"[to_dict] course_level type: {type(self.course_level)}")
        print(f"[to_dict] course_level value: {self.course_level}")
        try:
            course_level_enum = CourseLevel(self.course_level)
            return {
                'course_code': self.course_code,
                'course_name': self.course_name,
                'description': self.description,
                'credit': float(self.credit) if self.credit is not None else None,
                'course_level': course_level_enum.value,
                'is_compulsory': self.is_compulsory
            }
        except ValueError:
            return {
                'course_code': self.course_code,
                'course_name': self.course_name,
                'description': self.description,
                'credit': float(self.credit) if self.credit is not None else None,
                'course_level': None,
                'is_compulsory': self.is_compulsory
            }
