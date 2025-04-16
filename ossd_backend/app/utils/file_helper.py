import os
import uuid
from werkzeug.utils import secure_filename
from typing import Optional
from flask import current_app

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_unique_filename(original_filename):
    """生成唯一的文件名"""
    ext = original_filename.rsplit('.', 1)[1].lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}.{ext}"

def save_uploaded_file(file, allowed_extensions: list = None) -> Optional[str]:
    """
    保存上传的文件
    """
    if not file:
        return None
    
    # 获取文件名
    filename = secure_filename(file.filename)
    
    # 检查文件扩展名
    if allowed_extensions:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            return None
    
    # 创建上传目录
    upload_dir = os.path.join(current_app.static_folder, "uploads")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    # 保存文件
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    return file_path

def delete_file(file_path):
    """删除文件"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file {file_path}: {str(e)}")
        return False 