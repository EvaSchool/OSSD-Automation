from app import create_app
from app.models.user import User, UserRole
from app import db

app = create_app()

with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"Username: {user.username}, Role: {user.role}") 