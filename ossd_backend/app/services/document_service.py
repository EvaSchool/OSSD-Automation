"""
通用文档渲染 + LibreOffice PDF 转换服务
"""

from __future__ import annotations
import subprocess
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from docxtpl import DocxTemplate
from flask import current_app
from app import db
from app.models import Template as TemplateModel, TemplateType, OperationLog
from . import context_builder as ctxb


OUTPUT_ROOT = Path("generated_docs")


class DocumentService:
    """所有模板最终都走 generate()；部分模板提供专用快捷方法"""

    # ─────────────────────────────
    # 通用入口
    # ─────────────────────────────
    @classmethod
    def generate(cls, tpl_type: TemplateType, context: Dict[str, Any], user_id: int) -> Path:
        tpl_rec: TemplateModel | None = TemplateModel.query.filter_by(template_type=tpl_type).first()
        if not tpl_rec:
            raise FileNotFoundError(f"模板 {tpl_type.value} 未上传")

        tpl_path = Path(tpl_rec.file_path)
        if not tpl_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {tpl_path}")

        # ① 渲染 DOCX
        doc = DocxTemplate(str(tpl_path))
        doc.render(context)

        out_dir = OUTPUT_ROOT / tpl_type.value
        out_dir.mkdir(parents=True, exist_ok=True)
        docx_path = out_dir / f"{uuid.uuid4().hex}.docx"
        doc.save(docx_path)

        # ② 转 PDF（失败则返回 DOCX）
        final_path = cls._convert_to_pdf(docx_path) or docx_path

        # ③ 写操作日志
        log = OperationLog(
            user_id=user_id,
            operation_type="generate_document",
            operation_detail=f"生成 {tpl_type.value} → {final_path.name}",
            target_table="templates",
            target_id=tpl_rec.id,
            created_at=datetime.now(),
        )
        db.session.add(log)
        db.session.commit()

        return final_path

    # ─────────────────────────────
    # Welcome Letter
    # ─────────────────────────────
    @classmethod
    def generate_welcome_letter(cls, student, courses, user_id):
        ctx = ctxb.build_student_context(student)
        ctx.update(ctxb.build_login_context(student))
        ctx.update(ctxb.build_course_desc_context(courses))
        return cls.generate(TemplateType.WELCOME_LETTER, ctx, user_id)

    # ─────────────────────────────
    # Letter of Enrolment
    # ─────────────────────────────
    @classmethod
    def generate_letter_of_enrolment(cls, student, user_id):
        ctx = ctxb.build_student_context(student)
        return cls.generate(TemplateType.LETTER_OF_ENROLMENT, ctx, user_id)

    # ─────────────────────────────
    # Letter of Acceptance
    # ─────────────────────────────
    @classmethod
    def generate_letter_of_acceptance(cls, student, user_id):
        ctx = ctxb.build_student_context(student)
        return cls.generate(TemplateType.LETTER_OF_ACCEPTANCE, ctx, user_id)

    # ─────────────────────────────
    # Enrollment + Predicted Grades
    # ─────────────────────────────
    @classmethod
    def generate_enrollment_with_predicted(cls, student, courses, predicted_map, user_id):
        """
        对应模板：Enrollment Letter and Predicted Grades
        predicted_map: {course_id: (grade, completion_date)}
        """
        ctx = ctxb.build_student_context(student)
        rows = []
        for c in courses:
            grade, date = predicted_map.get(c.id, ("", ""))
            rows.append({
                "COURSE_NAME": c.course_name,
                "COURSE_CODE": c.course_code,
                "COURSE_LEVEL": c.course_level.value,
                "PREDICTED_GRADE": grade,
                "COMPLETION_DATE": date
            })
        ctx["PREDICTED_COURSES"] = rows
        return cls.generate(TemplateType.PREDICTED_GRADES, ctx, user_id)

    # ─────────────────────────────
    # 预留：Transcript / ReportCard (PDF模板)
    # ─────────────────────────────
    @classmethod
    def generate_transcript_pdf(cls, student, data: Dict[str, Any], user_id: int) -> Path:
        """
        预留接口：未来填充 PDF 表单（非 Word 模板）
        """
        raise NotImplementedError("Transcript PDF 生成功能待实现")

    @classmethod
    def generate_report_card_pdf(cls, student, course_data: Dict[str, Any], user_id: int) -> Path:
        """
        预留接口：Report Card 生成（PDF 填表）
        """
        raise NotImplementedError("Report Card PDF 生成功能待实现")

    # ─────────────────────────────
    # LibreOffice 转 PDF
    # ─────────────────────────────
    @staticmethod
    def _convert_to_pdf(docx_path: Path) -> Path | None:
        pdf_path = docx_path.with_suffix(".pdf")
        try:
            subprocess.run(
                [
                    "soffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", str(docx_path.parent),
                    str(docx_path),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return pdf_path if pdf_path.exists() else None
        except Exception as exc:
            current_app.logger.warning("PDF 转换失败: %s", exc)
            return None
