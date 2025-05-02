"""
app/routes/templates.py
~~~~~~~~~~~~~~~~~~~~~~~
– 模板管理 + 文档生成 统一路由
"""

from __future__ import annotations

import os
import uuid
import zipfile
from pathlib import Path
from typing import List

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
)
from app.utils import admin_required
from app.services.document_service import DocumentService
from app.services.context_builder import (
    build_student_context,
    build_login_context,
    build_course_list_context,
)

bp = Blueprint("templates", __name__, url_prefix="/api/v1/templates")

# ---------------------------------------------------------------------
# 1️⃣  模板 CRUD
# ---------------------------------------------------------------------

UPLOAD_ROOT = Path("templates")  # 相对项目根目录


@bp.route("", methods=["POST"])
@admin_required
def upload_template():
    """上传 Word/PDF 模板"""
    tpl_type_raw = request.form.get("template_type", "")
    file = request.files.get("file")
    if not file or not tpl_type_raw:
        return jsonify(code=400, message="template_type 与 file 均必填"), 400

    try:
        tpl_type = _parse_template_type(tpl_type_raw)
        if not tpl_type:
            return jsonify(code=400, message="无效的 template_type"), 400
    except KeyError:
        return jsonify(code=400, message="无效的 template_type"), 400

    # 保存文件
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
    """分页 + 按类型过滤"""
    q_type = request.args.get("template_type")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("page_size", 10, type=int)

    query = Template.query
    if q_type:
        try:
            query = query.filter(Template.template_type == TemplateType[q_type.upper()])
        except KeyError:
            return jsonify(code=400, message="无效的 template_type"), 400

    pagination = query.order_by(Template.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    data = [
        {
            "id": t.id,
            "template_type": t.template_type.value,
            "description": t.description,
            "file_path": t.file_path,
        }
        for t in pagination.items
    ]
    return jsonify(code=200, data={"total": pagination.total, "list": data})


@bp.route("/<int:tpl_id>", methods=["PUT"])
@admin_required
def update_template(tpl_id):
    """重新上传文件或修改描述"""
    tpl: Template = Template.query.get_or_404(tpl_id)

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
    """删除模板（硬删）"""
    tpl: Template = Template.query.get_or_404(tpl_id)
    # 删除磁盘文件
    try:
        os.remove(tpl.file_path)
    except FileNotFoundError:
        pass
    db.session.delete(tpl)
    db.session.commit()
    return jsonify(code=200, message="模板已删除")


# ---------------------------------------------------------------------
# 2️⃣  文档生成接口（所有生成动作都走 /templates/.../generate/...）
# ---------------------------------------------------------------------


def _parse_template_type(raw: str) -> TemplateType | None:
    """
    将路径里的 template_type 字符串映射到枚举：
    • name  :  WELCOME_LETTER / REPORT_CARD ...
    • value :  WelcomeLetter  / ReportCard  ...
    • slug  :  welcome_letter / report_card ...
    不区分大小写，匹配到就返回枚举，否则 None
    """
    raw_lc = raw.replace("-", "_").lower()
    for tt in TemplateType:
        if raw_lc in (tt.name.lower(), tt.value.lower()):
            return tt
    return None



# ---------------- 单学生 ----------------
@bp.route("/<template_type>/generate/student/<int:student_id>", methods=["POST"])
@jwt_required()
def generate_single(template_type: str, student_id: int):
    """根据模板为单个学生生成文档"""
    tpl_type = _parse_template_type(template_type)
    if not tpl_type:
        return jsonify(code=400, message="无效的 template_type"), 400

    student: Student = Student.query.get_or_404(student_id)
    body = request.get_json() or {}

    # 解析课程（可选，最多 3 门）
    course_ids: List[int] = body.get("course_ids", [])[:3]
    courses: List[Course] = []
    if course_ids:
        courses = Course.query.filter(Course.id.in_(course_ids)).all()

    # ---------- 构造 context ----------
    ctx = build_student_context(student)

    # Welcome Letter 需自动生成账号密码
    if tpl_type == TemplateType.WELCOME_LETTER:
        ctx.update(build_login_context(student))

    if courses:
        ctx.update(build_course_list_context(courses))

    # 用户自定义额外字段
    ctx.update(body.get("extra_ctx", {}))

    # ---------- 调用 Service ----------
    file_path = DocumentService.generate(tpl_type, ctx, user_id=get_jwt_identity())
    return send_file(file_path, as_attachment=True)


# ---------------- 批量生成 ----------------
@bp.route("/<template_type>/generate/batch", methods=["POST"])
@jwt_required()
def generate_batch(template_type: str):
    """
    批量为多个学生生成同一模板。
    JSON 体：
    {
        "student_ids": [1,2,3],
        "extra_ctx": {...},
        "course_ids": [...],          # 可选，Welcome Letter 时最多传 3
        "zip_name": "welcome_batch"   # 可选
    }
    """
    tpl_type = _parse_template_type(template_type)
    if not tpl_type:
        return jsonify(code=400, message="无效的 template_type"), 400

    body = request.get_json() or {}
    student_ids: List[int] = body.get("student_ids", [])
    if not student_ids:
        return jsonify(code=400, message="student_ids 不能为空"), 400

    students = Student.query.filter(Student.id.in_(student_ids)).all()
    if len(students) != len(student_ids):
        return jsonify(code=404, message="部分 student_id 不存在"), 404

    course_ids: List[int] = body.get("course_ids", [])[:3]
    courses: List[Course] = []
    if course_ids:
        courses = Course.query.filter(Course.id.in_(course_ids)).all()

    extra_ctx = body.get("extra_ctx", {})
    current_user = get_jwt_identity()

    generated_paths: List[Path] = []
    for stu in students:
        ctx = build_student_context(stu)
        if tpl_type == TemplateType.WELCOME_LETTER:
            ctx.update(build_login_context(stu))
        if courses:
            ctx.update(build_course_list_context(courses))
        ctx.update(extra_ctx)

        generated_paths.append(DocumentService.generate(tpl_type, ctx, user_id=current_user))

    # ------ 打包 ZIP 返回 ------
    zip_dir = Path("generated_docs") / "zip"
    zip_dir.mkdir(parents=True, exist_ok=True)
    zip_name = body.get("zip_name") or f"{uuid.uuid4().hex}.zip"
    zip_path = zip_dir / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in generated_paths:
            zf.write(p, arcname=p.name)

    return send_file(zip_path, as_attachment=True)
