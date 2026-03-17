import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS surveys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS survey_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    survey_id INTEGER,
    option_text TEXT NOT NULL,
    FOREIGN KEY (survey_id) REFERENCES surveys(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    survey_id INTEGER,
    user_id INTEGER,
    option_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (survey_id) REFERENCES surveys(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (option_id) REFERENCES survey_options(id)
)
""")

conn.commit()
conn.close()

print("Base de datos creada correctamente")