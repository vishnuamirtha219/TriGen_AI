from dotenv import load_dotenv
load_dotenv()

from app import create_app
from app.extensions import db
import os


def init_database():
    app = create_app()
    with app.app_context():
        print(f"Using database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        try:
            db.create_all()
            print("Database tables created successfully.")
        except Exception as e:
            print(f"Error creating tables: {e}")
            return False
    return True

if __name__ == '__main__':
    # First try to create postgres db if that's what's intended
    # (Optional: we keep the postgres creation logic if needed, 
    # but create_all handles the actual table creation)
    
    # Simple check for Postgres presence in config
    from config import Config
    if 'postgresql' in Config.SQLALCHEMY_DATABASE_URI:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
        try:
            # Connect to default 'postgres' to create the target db
            # Extract db name from URI or use default trigen_ai
            conn = psycopg2.connect(dbname='postgres', user='postgres', host='localhost', password='1915')
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'trigen_ai'")
            if not cur.fetchone():
                cur.execute('CREATE DATABASE trigen_ai')
                print("Postgres database 'trigen_ai' created.")
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Postgres DB creation skipped or failed: {e}")
            print("Falling back to defined SQLALCHEMY_DATABASE_URI (likely SQLite).")

    success = init_database()
    if not success:
        import sys
        sys.exit(1)
