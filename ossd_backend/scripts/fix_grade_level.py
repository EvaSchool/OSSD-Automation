import os
import sys
from sqlalchemy import text

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app, db

def fix_grade_level():
    app = create_app()
    with app.app_context():
        # 更新数据库中的年级值
        db.session.execute(text("UPDATE students SET grade = 'GRADE_9' WHERE grade = '9'"))
        db.session.execute(text("UPDATE students SET grade = 'GRADE_10' WHERE grade = '10'"))
        db.session.execute(text("UPDATE students SET grade = 'GRADE_11' WHERE grade = '11'"))
        db.session.execute(text("UPDATE students SET grade = 'GRADE_12' WHERE grade = '12'"))
        db.session.commit()
        print("年级枚举值已更新")

if __name__ == '__main__':
    fix_grade_level() 