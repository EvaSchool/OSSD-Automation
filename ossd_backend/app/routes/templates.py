from __future__ import annotations

import os
import uuid
import zipfile
from pathlib import Path
from typing import List
from app.utils.file_path import get_generated_file_path
from app.utils.file_path import GENERATED_ROOT
from datetime import datetime
import uuid
from app.models.document_job import DocumentJob, DocumentJobStatus
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    send_file,
)
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import (
    Template,
    TemplateType,
    Student,
    Course,
    StudentCourse,
)
from app.utils import admin_required
from app.services.document_service import DocumentService
from app.services.context_builder import (
    build_student_context,
    build_login_context,
    build_course_list_context,
)

bp = Blueprint("templates", __name__, url_prefix="/api/v1/templates")

UPLOAD_ROOT = Path("templates")

# ------------------------ 模板 CRUD ------------------------
@bp.route("", methods=["POST"])
@admin_required
def upload_template():
    tpl_type_raw = request.form.get("template_type", "")
    file = request.files.get("file")
    if not file or not tpl_type_raw:
        return jsonify(code=400, message="template_type 与 file 均必填"), 400

    tpl_type = _parse_template_type(tpl_type_raw)
    if not tpl_type:
        return jsonify(code=400, message="无效的 template_type"), 400

    suffix = Path(file.filename).suffix
    uuid_name = f"{uuid.uuid4().hex}{suffix}"
    save_dir = UPLOAD_ROOT / tpl_type.value
    save_dir.mkdir(parents=True, exist_ok=True)
    file_path = save_dir / uuid_name
    file.save(file_path)

    tpl = Template(
        template_type=tpl_type,
        file_path=str(file_path),
        description=request.form.get("description", ""),
    )
    db.session.add(tpl)
    db.session.commit()
    return jsonify(code=201, data={"template_id": tpl.id}), 201


@bp.route("", methods=["GET"])
@jwt_required()
def list_templates():
    q_type = request.args.get("template_type")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("page_size", 10, type=int)

    query = Template.query
    if q_type:
        try:
            query = query.filter(Template.template_type == TemplateType[q_type.upper()])
        except KeyError:
            return jsonify(code=400, message="无效的 template_type"), 400

    pagination = query.order_by(Template.template_id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    data = [t.to_dict() for t in pagination.items]
    return jsonify(code=200, data={"total": pagination.total, "list": data})


@bp.route("/<int:tpl_id>", methods=["PUT"])
@admin_required
def update_template(tpl_id):
    tpl = Template.query.get_or_404(tpl_id)

    if "description" in request.form:
        tpl.description = request.form["description"]

    if "file" in request.files:
        file = request.files["file"]
        suffix = Path(file.filename).suffix
        new_name = f"{uuid.uuid4().hex}{suffix}"
        save_dir = UPLOAD_ROOT / tpl.template_type.value
        save_dir.mkdir(parents=True, exist_ok=True)
        new_path = save_dir / new_name
        file.save(new_path)
        tpl.file_path = str(new_path)

    db.session.commit()
    return jsonify(code=200, message="模板已更新")


@bp.route("/<int:tpl_id>", methods=["DELETE"])
@admin_required
def delete_template(tpl_id):
    tpl = Template.query.get_or_404(tpl_id)
    try:
        os.remove(tpl.file_path)
    except FileNotFoundError:
        pass
    db.session.delete(tpl)
    db.session.commit()
    return jsonify(code=200, message="模板已删除")


# ------------------------ 文档生成 ------------------------

def _parse_template_type(raw: str) -> TemplateType | None:
    raw_lc = raw.replace("-", "_").lower()
    for tt in TemplateType:
        if raw_lc in (tt.name.lower(), tt.value.lower()):
            return tt
    return None


@bp.route("/<template_type>/generate/student/<int:student_id>", methods=["POST"])
@jwt_required()
def generate_single(template_type: str, student_id: int):
    tpl_type = _parse_template_type(template_type)
    if not tpl_type:
        return jsonify(code=400, message="无效的 template_type"), 400

    student = Student.query.get_or_404(student_id)
    body = request.get_json() or {}
    course_ids = body.get("course_ids", [])
    courses = Course.query.filter(Course.id.in_(course_ids)).all() if course_ids else []
    predicted_map = body.get("predicted_map", {})
    reporting = body.get("reporting")
    extra_data = body.get("extra_ctx", {})
    is_final = body.get("is_final", False)
    output_format = body.get("output_format", "flatten_pdf")
    flatten = body.get("flatten", True)
    user_id = get_jwt_identity()

    # 创建文档任务
    job = DocumentJob(
        student_id=student.student_id,
        template_type=tpl_type.name,
        file_path="",  # 先占位
        status=DocumentJobStatus.PENDING,
    )
    db.session.add(job)
    db.session.commit()

    try:
        if tpl_type == TemplateType.REPORT_CARD:
            scs = StudentCourse.query.filter_by(student_id=student.student_id).all()
            path = DocumentService.generate_report_card_pdf(student, scs, reporting, user_id, extra_data)
        elif tpl_type in (TemplateType.TRANSCRIPT, TemplateType.FINAL_TRANSCRIPT):
            scs = StudentCourse.query.filter_by(student_id=student.student_id).all()
            path = DocumentService.generate_transcript_pdf(student, scs, is_final, user_id, extra_data)
        elif tpl_type == TemplateType.WELCOME_LETTER:
            path = DocumentService.generate_welcome_letter(student, courses, user_id)
        elif tpl_type == TemplateType.LETTER_OF_ENROLMENT:
            path = DocumentService.generate_letter_of_enrolment(student, user_id)
        elif tpl_type == TemplateType.LETTER_OF_ACCEPTANCE:
            path = DocumentService.generate_letter_of_acceptance(student, user_id)
        elif tpl_type == TemplateType.PREDICTED_GRADES:
            path = DocumentService.generate_enrollment_with_predicted(student, courses, predicted_map, user_id)
        else:
            return jsonify(code=400, message="暂不支持该类型生成")

        # 成功更新 job 状态
        job.status = DocumentJobStatus.SUCCESS
        job.file_path = str(path)
        job.completed_at = datetime.utcnow()
        db.session.commit()

        return send_file(path, as_attachment=True)

    except Exception as e:
        job.status = DocumentJobStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.session.commit()
        return jsonify(code=500, message=f"生成失败: {str(e)}")


@bp.route("/<template_type>/generate/batch", methods=["POST"])
@jwt_required()
def generate_batch(template_type: str):
    tpl_type = _parse_template_type(template_type)
    if not tpl_type:
        return jsonify(code=400, message="无效的 template_type"), 400

    body = request.get_json() or {}
    student_ids = body.get("student_ids", [])
    if not student_ids:
        return jsonify(code=400, message="student_ids 不能为空"), 400

    students = Student.query.filter(Student.id.in_(student_ids)).all()
    course_ids = body.get("course_ids", [])
    courses = Course.query.filter(Course.id.in_(course_ids)).all() if course_ids else []
    predicted_map = body.get("predicted_map", {})
    extra_data = body.get("extra_ctx", {})
    is_final = body.get("is_final", False)
    reporting = body.get("reporting")
    output_format = body.get("output_format", "flatten_pdf")
    flatten = body.get("flatten", True)
    user_id = get_jwt_identity()

    now = datetime.now(datetime.UTC)
    zip_dir = GENERATED_ROOT / "batch_zip" / str(now.year)
    zip_dir.mkdir(parents=True, exist_ok=True)
    zip_path = zip_dir / f"batch_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.zip"

    generated_paths = []
    for stu in students:
        if tpl_type == TemplateType.REPORT_CARD:
            scs = StudentCourse.query.filter_by(student_id=stu.id).all()
            path = DocumentService.generate_report_card_pdf(stu, scs, reporting, user_id, extra_data)
        elif tpl_type in (TemplateType.TRANSCRIPT, TemplateType.FINAL_TRANSCRIPT):
            scs = StudentCourse.query.filter_by(student_id=stu.id).all()
            path = DocumentService.generate_transcript_pdf(stu, scs, is_final, user_id, extra_data)
        elif tpl_type == TemplateType.WELCOME_LETTER:
            path = DocumentService.generate_welcome_letter(stu, courses, user_id)
        elif tpl_type == TemplateType.LETTER_OF_ENROLMENT:
            path = DocumentService.generate_letter_of_enrolment(stu, user_id)
        elif tpl_type == TemplateType.LETTER_OF_ACCEPTANCE:
            path = DocumentService.generate_letter_of_acceptance(stu, user_id)
        elif tpl_type == TemplateType.PREDICTED_GRADES:
            path = DocumentService.generate_enrollment_with_predicted(stu, courses, predicted_map, user_id)
        else:
            continue
        generated_paths.append(path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in generated_paths:
            zf.write(p, arcname=p.name)

    return send_file(zip_path, as_attachment=True)


@bp.route("/generate/student/<int:student_id>/packages", methods=["POST"])
@jwt_required()
def generate_student_packages(student_id: int):
    student = Student.query.get_or_404(student_id)
    body = request.get_json() or {}
    template_types = body.get("template_types", [])
    if not template_types:
        return jsonify(code=400, message="template_types 不能为空"), 400

    course_ids = body.get("course_ids", [])
    courses = Course.query.filter(Course.id.in_(course_ids)).all() if course_ids else []
    predicted_map = body.get("predicted_map", {})
    reporting = body.get("reporting")
    extra_data = body.get("extra_ctx", {})
    is_final = body.get("is_final", False)
    user_id = get_jwt_identity()

    # 创建 job 任务
    from app.models.document_job import DocumentJob, DocumentJobStatus
    job = DocumentJob(
        student_id=student.student_id,
        template_type="PACKAGE",
        file_path="",
        status=DocumentJobStatus.PENDING,
    )
    db.session.add(job)
    db.session.commit()

    try:
        zip_path = get_generated_file_path(
            student.last_name,
            student.first_name,
            "package",
            ".zip"
        )

        generated_paths = []
        for tpl_type in template_types:
            try:
                tpl_enum = _parse_template_type(tpl_type)
                if not tpl_enum:
                    continue

                if tpl_enum == TemplateType.REPORT_CARD:
                    scs = StudentCourse.query.filter_by(student_id=student.student_id).all()
                    path = DocumentService.generate_report_card_pdf(student, scs, reporting, user_id, extra_data)
                elif tpl_enum in (TemplateType.TRANSCRIPT, TemplateType.FINAL_TRANSCRIPT):
                    scs = StudentCourse.query.filter_by(student_id=student.student_id).all()
                    path = DocumentService.generate_transcript_pdf(student, scs, is_final, user_id, extra_data)
                elif tpl_enum == TemplateType.WELCOME_LETTER:
                    path = DocumentService.generate_welcome_letter(student, courses, user_id)
                elif tpl_enum == TemplateType.LETTER_OF_ENROLMENT:
                    path = DocumentService.generate_letter_of_enrolment(student, user_id)
                elif tpl_enum == TemplateType.LETTER_OF_ACCEPTANCE:
                    path = DocumentService.generate_letter_of_acceptance(student, user_id)
                elif tpl_enum == TemplateType.PREDICTED_GRADES:
                    path = DocumentService.generate_enrollment_with_predicted(student, courses, predicted_map, user_id)
                else:
                    continue

                generated_paths.append(path)
            except Exception as e:
                current_app.logger.error(f"生成文件失败 {tpl_type}: {str(e)}")
                continue

        if not generated_paths:
            raise RuntimeError("所有文件生成失败")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in generated_paths:
                zf.write(p, arcname=p.name)

        job.status = DocumentJobStatus.SUCCESS
        job.file_path = str(zip_path)
        job.completed_at = datetime.utcnow()
        db.session.commit()

        return send_file(zip_path, as_attachment=True)

    except Exception as e:
        job.status = DocumentJobStatus.FAILED
        job.error_message = str(e)
        job.completed_at = datetime.utcnow()
        db.session.commit()
        return jsonify(code=500, message=f"生成失败: {str(e)}")

