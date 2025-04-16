from app import db
from datetime import datetime
from enum import Enum

class OperationType(Enum):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'

class TargetTable(Enum):
    STUDENTS = 'students'
    COURSES = 'courses'
    STUDENT_COURSES = 'student_courses'
    TEMPLATES = 'templates'

class OperationLog(db.Model):
    __tablename__ = 'operation_logs'
    
    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='日志ID')
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False, comment='操作用户ID')
    operation_type = db.Column(db.Enum(OperationType), nullable=False, comment='操作类型')
    target_table = db.Column(db.Enum(TargetTable), nullable=False, comment='目标表')
    target_id = db.Column(db.String(255), nullable=False, comment='目标记录ID')
    operation_details = db.Column(db.JSON, comment='操作详情（JSON格式）')
    operation_time = db.Column(db.DateTime, default=datetime.utcnow, comment='操作时间')
    
    # 关联关系
    user = db.relationship('User', back_populates='operation_logs')
    
    def to_dict(self):
        return {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'operation_type': self.operation_type.value,
            'target_table': self.target_table.value,
            'target_id': self.target_id,
            'operation_details': self.operation_details,
            'operation_time': self.operation_time.isoformat()
        } 