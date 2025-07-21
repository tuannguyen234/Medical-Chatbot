import sqlite3
# SQLite Setup
DB_PATH = "image_database.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_path TEXT,
        description TEXT
    )
""")
conn.commit()