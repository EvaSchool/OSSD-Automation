"""
通用文档渲染 + LibreOffice PDF 转换服务
"""
from __future__ import annotations
import subprocess
import uuid
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Literal
from docxtpl import DocxTemplate
from flask import current_app
from app import db
from app.models import Template as TemplateModel, TemplateType, OperationLog
from . import context_builder as ctxb
from .context_builder import build_transcript_context, build_report_card_context
from app.utils.file_path import get_generated_file_path

print(f"[调试] {__name__} 模块被导入")

class DocumentService:
    """所有模板最终都走 generate()；部分模板提供专用快捷方法"""

    # ─────────────────────────────
    # 通用入口
    # ─────────────────────────────
    @classmethod
    def generate_word_template(cls, tpl_type: TemplateType, context: Dict[str, Any], user_id: int,
                                output_format: Literal["docx", "flatten_pdf"] = "flatten_pdf") -> Path:
        print(f"[调试] {__name__}::{cls.__name__}::{sys._getframe().f_code.co_name} 被调用")
        print(f"[调试] 参数: tpl_type={tpl_type}, user_id={user_id}, output_format={output_format}")
        tpl_rec = TemplateModel.query.filter_by(template_type=tpl_type).first()
        if not tpl_rec or not Path(tpl_rec.file_path).exists():
            print(f"[调试] 模板文件未找到: {tpl_type.value}, 路径: {tpl_rec.file_path if tpl_rec else 'None'}")
            raise FileNotFoundError(f"模板 {tpl_type.value} 未找到")

        tpl_path = Path(tpl_rec.file_path)
        print(f"[调试] 使用模板文件: {tpl_path}")
        doc = DocxTemplate(str(tpl_path))
        doc.render(context)

        docx_path = get_generated_file_path(
            context.get("STUDENT_LASTNAME", "unknown"),
            context.get("STUDENT_FIRSTNAME", "unknown"),
            tpl_type.value,
            ".docx"
        )
        print(f"[调试] 生成Word文件路径: {docx_path}")
        doc.save(docx_path)

        final_path = docx_path
        if output_format == "flatten_pdf":
            final_path = cls._convert_to_pdf(docx_path) or docx_path
            print(f"[调试] 转换为PDF后路径: {final_path}")

        log = OperationLog(
            user_id=user_id,
            operation_type="generate_word_template",
            operation_details={"message": f"生成 {tpl_type.value} → {final_path.name}"},
            target_table="templates",
            target_id=tpl_rec.template_id,
            operation_time=datetime.now(),
        )
        db.session.add(log)
        db.session.commit()

        return final_path

    # ─────────────────────────────────────────
    # 通用：PDF 表单模板 → 填充 / flatten_pdf
    # ─────────────────────────────────────────
    @classmethod
    def generate_pdf_form_template(cls, tpl_type: TemplateType, context: Dict[str, Any], user_id: int,
                                   flatten: bool = False) -> Path:
        print(f"[调试] {__name__}::{cls.__name__}::{sys._getframe().f_code.co_name} 被调用")
        print(f"[调试] 参数: tpl_type={tpl_type}, user_id={user_id}, flatten={flatten}")
        tpl_rec = TemplateModel.query.filter_by(template_type=tpl_type).first()
        if not tpl_rec or not Path(tpl_rec.file_path).exists():
            print(f"[调试] 模板文件未找到: {tpl_type.value}, 路径: {tpl_rec.file_path if tpl_rec else 'None'}")
            raise FileNotFoundError(f"模板 {tpl_type.value} 未找到")

        print(f"[调试] 使用模板文件: {tpl_rec.file_path}")
        filled_path = cls._fill_pdf_template(Path(tpl_rec.file_path), context)
        print(f"[调试] 填充PDF表单后路径: {filled_path}")
        final_path = cls._flatten_pdf(filled_path) if flatten else filled_path
        print(f"[调试] Flatten后路径: {final_path}")

        log = OperationLog(
            user_id=user_id,
            operation_type="generate_pdf_form_template",
            operation_details={"message": f"生成 {tpl_type.value} → {final_path.name}"},
            target_table="templates",
            target_id=tpl_rec.template_id,
            operation_time=datetime.now(),
        )
        db.session.add(log)
        db.session.commit()

        return final_path

    # ─────────────────────────────────────────
    # 填充 PDF 表单
    # ─────────────────────────────────────────
    @staticmethod
    def _fill_pdf_template(pdf_path: Path, context: dict[str, str]) -> Path:
        from PyPDF2 import PdfReader, PdfWriter

        output_path = get_generated_file_path(
            context.get("STUDENT_LASTNAME", "unknown"),
            context.get("STUDENT_FIRSTNAME", "unknown"),
            "pdf_form_filled",
            ".pdf"
        )
        reader = PdfReader(str(pdf_path))
        writer = PdfWriter()

        page = reader.pages[0]
        writer.add_page(page)
        writer.update_page_form_field_values(writer.pages[0], context)

        with open(output_path, "wb") as f:
            writer.write(f)

        return output_path
    
    # ─────────────────────────────────────────
    # PDF 表单 → Flatten
    # ─────────────────────────────────────────
    @staticmethod
    def _flatten_pdf(input_path: Path) -> Path:
        output_path = input_path.with_stem(input_path.stem + "_flat")
        try:
            subprocess.run(
                ["pdftoppm", "-png", str(input_path), str(output_path.with_suffix(""))], check=True
            )
            subprocess.run(
                ["convert", str(output_path.with_name(output_path.stem + "-1.png")), str(output_path)], check=True
            )
            return output_path
        except Exception as e:
            current_app.logger.warning("PDF flatten 失败: %s", e)
            return input_path
        

    # ─────────────────────────────
    # Welcome Letter
    # ─────────────────────────────
    @classmethod
    def generate_welcome_letter(cls, student, courses, user_id):
        ctx = ctxb.build_student_context(student)
        ctx.update(ctxb.build_login_context(student))
        ctx.update(ctxb.build_course_desc_context(courses))
        return cls.generate_word_template(TemplateType.WELCOME_LETTER, ctx, user_id)

    # ─────────────────────────────
    # Letter of Enrolment
    # ─────────────────────────────
    @classmethod
    def generate_letter_of_enrolment(cls, student, user_id):
        ctx = ctxb.build_student_context(student)
        return cls.generate_word_template(TemplateType.LETTER_OF_ENROLMENT, ctx, user_id)

    # ─────────────────────────────
    # Letter of Acceptance
    # ─────────────────────────────
    @classmethod
    def generate_letter_of_acceptance(cls, student, user_id):
        ctx = ctxb.build_student_context(student)
        return cls.generate_word_template(TemplateType.LETTER_OF_ACCEPTANCE, ctx, user_id)

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
        return cls.generate_word_template(TemplateType.PREDICTED_GRADES, ctx, user_id)

    # ─────────────────────────────
    # Transcript / ReportCard (PDF模板)
    # ─────────────────────────────
    @classmethod
    def generate_transcript_pdf(cls, student, student_courses, is_final: bool, user_id: int, extra_data: dict = {}):
        tpl_type = TemplateType.FINAL_TRANSCRIPT if is_final else TemplateType.TRANSCRIPT
        ctx = build_transcript_context(student, student_courses, is_final, extra_data)
        return cls.generate_pdf_form_template(tpl_type, ctx, user_id, flatten=True)

    @classmethod
    def generate_report_card_pdf(cls, student, student_courses, reporting: str | Dict[str, str], user_id: int, extra_data: dict = {}):
        """
        生成成绩单 PDF
        :param student: 学生对象
        :param student_courses: 学生课程列表
        :param reporting: 可以是字符串（全局 reporting）或字典（每个课程的 reporting）
        :param user_id: 用户 ID
        :param extra_data: 额外数据
        """
        # 如果 reporting 是字符串，转换为字典格式
        if isinstance(reporting, str):
            course_reporting = {str(sc.id): reporting for sc in student_courses}
        else:
            course_reporting = reporting

        ctx = build_report_card_context(
            student, 
            student_courses, 
            extra_data | {"course_reporting": course_reporting}
        )
        return cls.generate_pdf_form_template(TemplateType.REPORT_CARD, ctx, user_id, flatten=True)

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
