"""
Database migration to add image metadata fields to the property_images table.

This migration adds the following fields to store image metadata:
- width: Image width in pixels
- height: Image height in pixels
- format: Image format (e.g., 'JPEG', 'PNG')
- size_kb: File size in kilobytes
- is_optimized: Whether the image has been optimized
- original_format: Original format before optimization (if converted)
"""
from sqlalchemy import text
from app.database import engine

def upgrade():
    """Run the migration to add image metadata fields."""
    with engine.connect() as connection:
        # SQLite doesn't support adding multiple columns in a single ALTER TABLE
        # So we'll execute separate ALTER TABLE statements for each column
        columns_to_add = [
            ('width', 'INTEGER'),
            ('height', 'INTEGER'),
            ('format', 'VARCHAR(10)'),
            ('size_kb', 'FLOAT'),
            ('is_optimized', 'BOOLEAN DEFAULT 0'),  # SQLite uses 0/1 for BOOLEAN
            ('original_format', 'VARCHAR(10)')
        ]
        
        # Check if columns exist before adding them
        cursor = connection.execute(text("PRAGMA table_info(property_images)"))
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                connection.execute(text(f"ALTER TABLE property_images ADD COLUMN {column_name} {column_type}"))
        connection.commit()
        print("Migration completed: Added image metadata fields to property_images table")

if __name__ == "__main__":
    upgrade()
