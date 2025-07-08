import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# === CONFIG ===
DB_NAME = "health_db"
DB_USER = "postgres"     # Use the main PostgreSQL user
DB_PASSWORD = "1" # Update to your actual password
DB_HOST = "localhost"
DB_PORT = "5432"

def create_database():
    try:
        # Step 1: Connect to default 'postgres' DB to create new one
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)  # Allow CREATE DATABASE
        cur = conn.cursor()

        # Step 2: Create the DB if not exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cur.fetchone()
        if not exists:
            cur.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"✅ Database '{DB_NAME}' created.")
        else:
            print(f"✅ Database '{DB_NAME}' already exists.")
        cur.close()
        conn.close()

    except Exception as e:
        print("❌ Failed to create database:", e)

def create_table():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                symptoms TEXT,
                location TEXT,
                diagnosis TEXT,
                user_id VARCHAR(20) UNIQUE
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Table 'users' ensured.")
    except Exception as e:
        print("❌ Failed to create table:", e)

def save_user(name, symptoms, location, diagnosis, user_id):
    #print(f"--> Inserting: {name}, {symptoms}, {location}, {diagnosis}, {user_id}")
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (name, symptoms, location, diagnosis, user_id)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (user_id) DO NOTHING;
    """, (name, symptoms, location, diagnosis, user_id))
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ User {name} saved.")

def get_user(user_id):
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def update_user(user_id, symptoms, location, diagnosis):
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cur = conn.cursor()
    cur.execute("""
        UPDATE users
        SET symptoms = %s, location = %s, diagnosis = %s
        WHERE user_id = %s
    """, (symptoms, location, diagnosis, user_id))
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ User {user_id} updated.")

# === Run everything ===
create_database()
create_table()
print("✅ Setup complete.")
