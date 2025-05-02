# register_templates.py
import sys
import os

# 把 ossd_backend 加入 Python 模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), "ossd_backend"))


from app import create_app, db
from app.models import Template, TemplateType

app = create_app()

# 模板配置列表（路径必须与你实际存放路径一致）
TEMPLATE_CONFIG = [
    {
        "template_type": TemplateType.WELCOME_LETTER,
        "file_path": "templates/WELCOME_LETTER/EVA-Welcome Letter 2025.docx",
        "description": "Welcome Letter"
    },
    {
        "template_type": TemplateType.LETTER_OF_ENROLMENT,
        "file_path": "templates/LETTER_OF_ENROLMENT/EVA-Enrollment Letter 2025.docx",
        "description": "Enrollment Letter"
    },
    {
        "template_type": TemplateType.LETTER_OF_ACCEPTANCE,
        "file_path": "templates/LETTER_OF_ACCEPTANCE/EVA-LOA 2025.docx",
        "description": "Letter of Acceptance"
    },
    {
        "template_type": TemplateType.PREDICTED_GRADES,
        "file_path": "templates/PREDICTED_GRADES/EVA-Enrollment Letter and Predicted Grades 2025.docx",
        "description": "Enrollment + Predicted Grades"
    }
]

if __name__ == "__main__":
    with app.app_context():
        for cfg in TEMPLATE_CONFIG:
            exists = Template.query.filter_by(template_type=cfg["template_type"]).first()
            if exists:
                print(f"⚠️ 已存在: {cfg['template_type'].value}，跳过")
                continue

            tpl = Template(
                template_type=cfg["template_type"],
                file_path=cfg["file_path"],
                description=cfg["description"]
            )
            db.session.add(tpl)
            print(f"✅ 添加: {cfg['template_type'].value}")
        db.session.commit()
        print("🎉 所有模板注册完成！")
