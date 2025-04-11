import sqlite3
from sqlite3 import Row


# Database initialization
def init_db():
    conn = sqlite3.connect('rides.db')
    c = conn.cursor()

    # Create users table with email and profile info
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        profile_picture TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create rides table
    c.execute('''
    CREATE TABLE IF NOT EXISTS rides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        mobile TEXT NOT NULL,
        date TEXT NOT NULL,
        train_flight_time TEXT NOT NULL,
        departure_time TEXT NOT NULL,
        start_location TEXT NOT NULL,
        destination TEXT NOT NULL,
        people_required INTEGER NOT NULL,
        cost_per_person INTEGER NOT NULL,
        vehicle_type TEXT NOT NULL,
        whatsapp_group_link TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Create applications table
    c.execute('''
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        ride_id INTEGER NOT NULL,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (ride_id) REFERENCES rides (id),
        UNIQUE(user_id, ride_id)
    )
    ''')

    # Create suggestions table
    c.execute('''
    CREATE TABLE IF NOT EXISTS suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        suggestion TEXT NOT NULL,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    conn.commit()
    conn.close()


# Function to get database connection
def get_db_connection():
    conn = sqlite3.connect('rides.db')
    conn.row_factory = Row
    return conn
