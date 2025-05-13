from app import db
from enum import Enum

class TemplateType(Enum):
    REPORT_CARD = 'ReportCard'
    TRANSCRIPT = 'Transcript'
    PREDICTED_GRADES = 'PredictedGrades'
    LETTER_OF_ENROLMENT = 'LetterOfEnrolment'
    LETTER_OF_ACCEPTANCE = 'LetterOfAcceptance'
    WELCOME_LETTER = 'WelcomeLetter'
    FINAL_TRANSCRIPT = 'FinalTranscript'

class Template(db.Model):
    __tablename__ = 'templates'
    
    template_id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='模板ID')
    template_type = db.Column(db.Enum(TemplateType), nullable=False, comment='模板类型')
    file_path = db.Column(db.String(255), nullable=False, comment='模板文件路径')
    description = db.Column(db.Text, comment='模板说明')
    
    def to_dict(self):
        return {
            'template_id': self.template_id,
            'template_type': self.template_type.value,
            'file_path': self.file_path,
            'description': self.description
        } 