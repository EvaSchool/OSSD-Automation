from pathlib import Path
from datetime import datetime, timezone
import sys
import os

# 获取项目根目录
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
GENERATED_ROOT = PROJECT_ROOT / "generated_docs"
print(f"[调试] GENERATED_ROOT 设置为: {GENERATED_ROOT.absolute()}")

def get_generated_file_path(
    lastname: str,
    firstname: str,
    template_type: str,
    ext: str = ".pdf"
) -> Path:
    """
    格式：generated_docs/{template_type}/{yyyy}/{lastname firstname}_{template_type}_{timestamp}.{ext}
    """
    print(f"[调试] get_generated_file_path 被调用")
    print(f"[调试] 参数: lastname={lastname}, firstname={firstname}, template_type={template_type}, ext={ext}")
    
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    subdir = GENERATED_ROOT / template_type.lower() / str(now.year)
    subdir.mkdir(parents=True, exist_ok=True)

    safe_lastname = lastname.strip().replace(" ", "_")
    safe_firstname = firstname.strip().replace(" ", "_")
    name = f"{safe_lastname}_{safe_firstname}_{template_type.lower()}_{ts}{ext}"

    output_path = subdir / name
    print(f"[调试] 最终文件路径: {output_path.absolute()}")
    
    return output_path
