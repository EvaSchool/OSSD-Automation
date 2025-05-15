# app/models/document_job.py

from app import db
from datetime import datetime
from enum import Enum


class DocumentJobStatus(Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class DocumentJob(db.Model):
    __tablename__ = "document_jobs"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, nullable=False)
    template_type = db.Column(db.String(64), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum(DocumentJobStatus), nullable=False, default=DocumentJobStatus.PENDING)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "template_type": self.template_type,
            "file_path": self.file_path,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }
