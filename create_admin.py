from app import create_app
from app.extensions import db
from app.models import User
import sys

def make_admin(username, password=None):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            user.role = 'admin'
            db.session.commit()
            print(f"User '{username}' is now an admin.")
        else:
            if not password:
                print(f"User '{username}' not found and no password provided for creation.")
                return
            new_user = User(username=username, role='admin')
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            print(f"Admin user '{username}' created successfully.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python create_admin.py <username> [password]")
    else:
        uname = sys.argv[1]
        pwd = sys.argv[2] if len(sys.argv) > 2 else None
        make_admin(uname, pwd)
