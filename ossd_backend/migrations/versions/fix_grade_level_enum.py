"""fix grade level enum

Revision ID: fix_grade_level_enum
Revises: add_student_number
Create Date: 2024-03-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_grade_level_enum'
down_revision = 'add_student_number'  # 指向 add_student_number 迁移
branch_labels = None
depends_on = None

def upgrade():
    # 在这里添加你的升级逻辑
    pass

def downgrade():
    # 在这里添加你的回滚逻辑
    pass 