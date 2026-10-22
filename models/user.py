from werkzeug.security import generate_password_hash, check_password_hash
from models.database import get_db

class UserModel:
    """User data access layer and authentication methods."""

    @staticmethod
    def create(name, email, password, role="user"):
        """Create a new user with securely hashed password."""
        db = get_db()
        email_clean = email.strip().lower()
        password_hash = generate_password_hash(password)
        try:
            cursor = db.execute(
                "INSERT INTO users (name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (name.strip(), email_clean, password_hash, role)
            )
            db.commit()
            return UserModel.get_by_id(cursor.lastrowid)
        except Exception:
            return None

    @staticmethod
    def get_by_id(user_id):
        """Retrieve user by ID."""
        db = get_db()
        row = db.execute("SELECT id, name, email, role, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_email(email):
        """Retrieve user row (with hash) by email for authentication."""
        db = get_db()
        row = db.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def authenticate(email, password):
        """Verify user credentials and return user dict without password hash if valid."""
        user = UserModel.get_by_email(email)
        if not user:
            return None
        if check_password_hash(user["password_hash"], password):
            # Do not leak hash
            return {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "role": user["role"],
                "created_at": user["created_at"]
            }
        return None

    @staticmethod
    def get_or_create_demo_user():
        """Retrieve or initialize the default demo user for frictionless local testing."""
        demo_email = "planner@celebration.ai"
        user = UserModel.get_by_email(demo_email)
        if not user:
            user = UserModel.create("Alex Morgan", demo_email, "Celebration2026!", role="demo")
        return UserModel.get_by_id(user["id"])
