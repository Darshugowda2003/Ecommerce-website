import sqlite3

def create_database():
    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect('app_data.db')
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            aadhar_card_number TEXT,
            address TEXT,
            card_details TEXT,
            phone_number TEXT
        )
    ''')

    # Create contacts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Save changes and close the connection
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    create_database()
