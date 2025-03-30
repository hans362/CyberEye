from db import Session, engine
from models.user import User
from argon2 import PasswordHasher
from db import create_db_and_tables
import sys

action = sys.argv[1] if len(sys.argv) > 1 else None

if action == "create_admin":
    create_db_and_tables()
    try:
        username = input("Enter admin username: ")
        password = input("Enter admin password: ")
        session = Session(engine)
        user = User(
            username=username,
            password=PasswordHasher().hash(password),
            role="admin",
        )
        session.add(user)
        session.commit()
        session.close()
        print("Admin user created successfully.")
    except Exception as e:
        session.rollback()
        session.close()
        print(f"Error creating admin user: {e}")
        sys.exit(1)
else:
    print("Error: Invalid action.")
    print("Usage: python manage.py <action>")
    sys.exit(1)
