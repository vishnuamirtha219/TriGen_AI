"""
Migration Script: Add Confidence Score Columns
TriGen-AI Healthcare Platform

This migration adds confidence_score columns to all result tables
to store the AI prediction confidence metrics.

Run this script to update the database schema.
"""

from app import create_app
from app.extensions import db
from sqlalchemy import text

def run_migration():
    """Add confidence_score columns to result tables"""
    app = create_app()
    
    with app.app_context():
        print("Starting migration: Adding confidence_score columns...")
        
        # List of tables and their confidence columns
        migrations = [
            ("immunity_results", "confidence_score FLOAT"),
            ("sickle_results", "confidence_score FLOAT"),
            ("lsd_results", "confidence_score FLOAT"),
        ]
        
        for table_name, column_def in migrations:
            try:
                # Check if column already exists
                check_sql = text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}' 
                    AND column_name = 'confidence_score'
                """)
                result = db.session.execute(check_sql).fetchone()
                
                if result:
                    print(f"  ✓ {table_name}.confidence_score already exists")
                else:
                    # Add column
                    alter_sql = text(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
                    db.session.execute(alter_sql)
                    db.session.commit()
                    print(f"  ✓ Added confidence_score to {table_name}")
                    
            except Exception as e:
                print(f"  ⚠ Error with {table_name}: {str(e)}")
                db.session.rollback()
                
                # Try SQLite syntax as fallback
                try:
                    alter_sql = text(f"ALTER TABLE {table_name} ADD COLUMN confidence_score REAL")
                    db.session.execute(alter_sql)
                    db.session.commit()
                    print(f"  ✓ Added confidence_score to {table_name} (SQLite)")
                except Exception as e2:
                    if "duplicate column" in str(e2).lower() or "already exists" in str(e2).lower():
                        print(f"  ✓ {table_name}.confidence_score already exists")
                    else:
                        print(f"  ✗ Failed: {str(e2)}")
        
        print("\nMigration completed!")

if __name__ == "__main__":
    run_migration()
