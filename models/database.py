import sqlite3
import os
import shutil
import logging
from flask import g, current_app
from config import Config, BASE_DIR

logger = logging.getLogger(__name__)

def ensure_writable_db_path(target_path):
    """
    Ensure the target database path is writable.
    If the target directory is read-only (such as /var/task on Vercel), fallback to /tmp/celebration.db.
    Also, if the DB file doesn't exist at the writable target but a seed DB exists in the project,
    copy it over so initial state/demo users are immediately available.
    """
    resolved_path = target_path or Config.DATABASE_PATH
    
    # Check if target directory is writable
    try:
        abs_path = os.path.abspath(resolved_path)
        target_dir = os.path.dirname(abs_path)
        os.makedirs(target_dir, exist_ok=True)
        # Test write permission in directory
        test_file = os.path.join(target_dir, ".test_write_perm")
        with open(test_file, "w") as f:
            f.write("1")
        if os.path.exists(test_file):
            os.remove(test_file)
    except (OSError, IOError, PermissionError):
        # Target directory is read-only (e.g. AWS Lambda / Vercel Serverless /var/task)
        resolved_path = "/tmp/celebration.db"
        abs_path = os.path.abspath(resolved_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    # If database file does not exist at target, copy seed db if present
    if not os.path.exists(abs_path):
        seed_db = BASE_DIR / "celebration.db"
        if seed_db.exists() and str(seed_db.resolve()) != abs_path:
            try:
                shutil.copyfile(str(seed_db), abs_path)
                logger.info(f"Initialized database from seed at: {abs_path}")
            except Exception as e:
                logger.warning(f"Could not copy seed DB to {abs_path}: {e}")

    return resolved_path

def get_db():
    """Retrieve or create the database connection for the current Flask request context."""
    if "db" not in g:
        raw_path = current_app.config.get("DATABASE_PATH", Config.DATABASE_PATH) if current_app else Config.DATABASE_PATH
        db_path = ensure_writable_db_path(raw_path)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        # Enforce foreign key constraints
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()

def get_standalone_db(db_path=None):
    """Return an independent database connection for scripts or background tests."""
    path = ensure_writable_db_path(db_path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(app=None):
    """Initialize all database tables and indexes."""
    raw_path = app.config.get("DATABASE_PATH", Config.DATABASE_PATH) if app else Config.DATABASE_PATH
    db_path = ensure_writable_db_path(raw_path)
    conn = get_standalone_db(db_path)
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        event_type TEXT NOT NULL,
        event_date TEXT NOT NULL,
        start_time TEXT,
        end_time TEXT,
        location TEXT NOT NULL,
        indoor_outdoor TEXT DEFAULT 'Indoor',
        guest_count INTEGER DEFAULT 50,
        total_budget REAL NOT NULL,
        currency TEXT DEFAULT 'INR',
        budget_tier TEXT DEFAULT 'balanced',
        theme TEXT,
        color_palette TEXT,
        food_preference TEXT DEFAULT 'Mixed',
        entertainment_preference TEXT,
        cultural_traditions TEXT,
        accessibility_needs TEXT,
        additional_notes TEXT,
        services_needed TEXT,
        ai_concept TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Expenses Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        planned_amount REAL DEFAULT 0.0,
        actual_amount REAL DEFAULT 0.0,
        status TEXT DEFAULT 'Planned',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    );
    """)

    # Timeline Tasks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timeline_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        due_date TEXT,
        priority TEXT DEFAULT 'Medium',
        category TEXT DEFAULT 'Preparation',
        is_completed INTEGER DEFAULT 0,
        explanation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    );
    """)

    # Vendors Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        name TEXT,
        contact_info TEXT,
        estimated_cost REAL DEFAULT 0.0,
        actual_cost REAL DEFAULT 0.0,
        booking_status TEXT DEFAULT 'Needed',
        payment_status TEXT DEFAULT 'Unpaid',
        deadline TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    );
    """)

    # Guests Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        email_or_phone TEXT,
        rsvp_status TEXT DEFAULT 'Invited',
        attendees_count INTEGER DEFAULT 1,
        dietary_preference TEXT DEFAULT 'No preference',
        table_or_group TEXT,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    );
    """)

    # Checklist Items Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS checklist_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        item_name TEXT NOT NULL,
        is_completed INTEGER DEFAULT 0,
        estimated_cost REAL DEFAULT 0.0,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    );
    """)

    # Event Ideas Table (AI Generated & Bookmarkable)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_ideas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        is_favorited INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    );
    """)

    # Chat Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        sender TEXT NOT NULL,
        content TEXT NOT NULL,
        action_proposal TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
    );
    """)

    # Performance Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_event ON expenses(event_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_timeline_event ON timeline_tasks(event_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendors_event ON vendors(event_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_guests_event ON guests(event_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_checklist_event ON checklist_items(event_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ideas_event ON event_ideas(event_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_event ON chat_messages(event_id);")

    conn.commit()
    conn.close()
