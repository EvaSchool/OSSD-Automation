# app/routes/document_jobs.py

from flask import Blueprint, request, jsonify
from app import db
from app.models.document_job import DocumentJob, DocumentJobStatus
from flask_jwt_extended import jwt_required
from datetime import datetime, timezone

bp = Blueprint("document_jobs", __name__, url_prefix="/api/v1/document_jobs")

@bp.route("", methods=["GET"])
@jwt_required()
def list_jobs():
    """任务列表，可选筛选 student_id"""
    student_id = request.args.get("student_id", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("page_size", 10, type=int)

    query = DocumentJob.query
    if student_id:
        query = query.filter_by(student_id=student_id)

    pagination = query.order_by(DocumentJob.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    jobs = [j.to_dict() for j in pagination.items]

    return jsonify(code=200, data={
        "total": pagination.total,
        "list": jobs
    })

@bp.route("/<int:job_id>/retry", methods=["POST"])
@jwt_required()
def retry_job(job_id):
    job = DocumentJob.query.get_or_404(job_id)

    if job.status != DocumentJobStatus.FAILED:
        return jsonify(code=400, message="只有失败的任务可以重试"), 400

    from app.models import Student, TemplateType
    from app.services.document_service import DocumentService

    try:
        student = Student.query.get_or_404(job.student_id)
        tpl_type = TemplateType[job.template_type]

        # 根据模板类型重新生成
        if tpl_type == TemplateType.REPORT_CARD:
            from app.models import StudentCourse
            scs = StudentCourse.query.filter_by(student_id=student.student_id).all()
            path = DocumentService.generate_report_card_pdf(student, scs, {}, 0, {})
        elif tpl_type in (TemplateType.TRANSCRIPT, TemplateType.FINAL_TRANSCRIPT):
            from app.models import StudentCourse
            scs = StudentCourse.query.filter_by(student_id=student.student_id).all()
            is_final = tpl_type == TemplateType.FINAL_TRANSCRIPT
            path = DocumentService.generate_transcript_pdf(student, scs, is_final, 0, {})
        elif tpl_type == TemplateType.WELCOME_LETTER:
            path = DocumentService.generate_welcome_letter(student, [], 0)
        elif tpl_type == TemplateType.LETTER_OF_ENROLMENT:
            path = DocumentService.generate_letter_of_enrolment(student, 0)
        elif tpl_type == TemplateType.LETTER_OF_ACCEPTANCE:
            path = DocumentService.generate_letter_of_acceptance(student, 0)
        elif tpl_type == TemplateType.PREDICTED_GRADES:
            path = DocumentService.generate_enrollment_with_predicted(student, [], {}, 0)
        else:
            return jsonify(code=400, message="该类型暂不支持重试")

        # 更新成功状态
        job.status = DocumentJobStatus.SUCCESS
        job.file_path = str(path)
        job.completed_at = datetime.now(timezone.utc)
        job.error_message = None
        db.session.commit()

        return jsonify(code=200, message="重试成功", data=job.to_dict())

    except Exception as e:
        job.status = DocumentJobStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        return jsonify(code=500, message=f"重试失败: {str(e)}")
