from app import db, User, app
from werkzeug.security import generate_password_hash

def create_admin_user():
    username = input("Enter username: ")
    email = input("Enter email: ")
    password = input("Enter password: ")
    role = "admin"

    password_hash = generate_password_hash(password)

    admin_user = User(username=username, email=email, password=password_hash, role=role)

    existing_user = User.query.filter_by(username=username).first()

    if existing_user:
        print("Admin user already exists.")
    else:
        db.session.add(admin_user)
        db.session.commit()
        print("Admin user created.")

if __name__ == "__main__":
    # Use the app context manager
    with app.app_context():
        db.create_all()
        create_admin_user()


# python create_admin.py on comand prompt