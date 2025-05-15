from pathlib import Path
from datetime import datetime

GENERATED_ROOT = Path("generated_docs")

def get_generated_file_path(
    lastname: str,
    firstname: str,
    template_type: str,
    ext: str = ".pdf"
) -> Path:
    """
    格式：generated_docs/{template_type}/{yyyy}/{lastname firstname}_{template_type}_{timestamp}.{ext}
    """
    now = datetime.now(datetime.UTC)
    ts = now.strftime("%Y%m%d_%H%M%S")
    subdir = GENERATED_ROOT / template_type.lower() / str(now.year)
    subdir.mkdir(parents=True, exist_ok=True)

    safe_lastname = lastname.strip().replace(" ", "_")
    safe_firstname = firstname.strip().replace(" ", "_")
    name = f"{safe_lastname}_{safe_firstname}_{template_type.lower()}_{ts}{ext}"

    return subdir / name
