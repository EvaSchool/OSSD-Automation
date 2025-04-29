from __future__ import annotations
import os
import uuid
import datetime as _dt
from pathlib import Path
from typing import Dict, Any
import subprocess

from docxtpl import DocxTemplate
from flask import current_app
from app import db
from app.models import Template as TemplateModel, TemplateType, OperationLog


class DocumentService:
    _OUTPUT_ROOT = Path("generated_docs")

    @classmethod
    def generate(
        cls,
        template_type: TemplateType,
        context: Dict[str, Any],
        user_id: int,
        *,
        export_pdf: bool = True,
    ) -> Path:
        """
        渲染模板 → 生成 docx → 自动转换 PDF（可选）

        Returns:
            Path 最终文件路径（PDF 或 DOCX）
        """
        # ① 获取模板路径
        tpl_rec: TemplateModel | None = TemplateModel.query.filter_by(
            template_type=template_type
        ).first()
        if not tpl_rec:
            raise FileNotFoundError(f"未找到模板类型: {template_type.value}")
        tpl_path = Path(tpl_rec.file_path)
        if not tpl_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {tpl_path}")

        # ② 渲染 DOCX 模板
        doc = DocxTemplate(str(tpl_path))
        doc.render(context)

        out_dir = cls._OUTPUT_ROOT / template_type.value
        out_dir.mkdir(parents=True, exist_ok=True)
        docx_path = out_dir / f"{uuid.uuid4().hex}.docx"
        doc.save(docx_path)

        final_path: Path = docx_path

        # ③ LibreOffice 转 PDF
        if export_pdf:
            try:
                pdf_path = cls._convert_to_pdf(docx_path)
                if pdf_path.exists():
                    final_path = pdf_path
            except Exception as e:
                current_app.logger.warning(f"LibreOffice PDF 转换失败: {e}")

        # ④ 写操作日志
        log = OperationLog(
            user_id=user_id,
            operation_type="generate_document",
            operation_detail=f"生成 {template_type.value} 文档 {final_path.name}",
            target_table="templates",
            target_id=tpl_rec.template_id,
            created_at=_dt.datetime.now(),
        )
        db.session.add(log)
        db.session.commit()

        return final_path

    @staticmethod
    def _convert_to_pdf(docx_path: Path) -> Path:
        """
        用 LibreOffice 将 DOCX 转 PDF（同目录）
        """
        output_dir = docx_path.parent
        subprocess.run(
            [
                "libreoffice",
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(output_dir),
                str(docx_path),
            ],
            check=True,
        )
        return output_dir / f"{docx_path.stem}.pdf"

    @staticmethod
    def build_student_context(student) -> Dict[str, Any]:
        return {
            "STUDENT_FIRSTNAME": student.first_name,
            "STUDENT_LASTNAME": student.last_name,
            "STUDENT_FULLNAME": f"{student.last_name}, {student.first_name}",
            "OEN": f"{student.OEN[:3]}-{student.OEN[3:6]}-{student.OEN[6:]}",
            "DOB": f"{student.birth_year}-{student.birth_month.value}-{student.birth_day:02d}",
            "ENROLL_DATE": f"{student.enrollment_year}-{student.enrollment_month.value}-{student.enrollment_day:02d}",
            "EXPECTED_GRAD": f"{student.expected_graduation_year}-{student.expected_graduation_month.value}-{student.expected_graduation_day:02d}",
            "ADDRESS": student.address or "Eva High School, Toronto, ON",
            "VOLUNTEER_HOURS": student.volunteer_hours,
            "GRADE": student.grade.value,
            "GRAD_STATUS": student.graduation_status.value,
            "TODAY": _dt.datetime.now().strftime("%Y-%b-%d"),
        }
    @staticmethod
    def build_course_context(course) -> Dict[str, Any]:
        return {
            "COURSE_CODE": course.course_code,
            "COURSE_NAME": course.course_name,
            "COURSE_DESCRIPTION": course.description,
            "COURSE_LEVEL": course.course_level.value,   # e.g. "11", "ESL4"
            "CREDIT": str(course.credit or ""),          # 转成字符串，防止为 None
            "IS_COMPULSORY": "Yes" if course.is_compulsory else "No",
            "IS_LOCAL": "Yes" if getattr(course, "is_local", False) else "No",
        }

