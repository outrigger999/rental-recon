#!/usr/bin/env python3
"""
Migration script to add contacts column to existing properties table.
Run this once to update existing databases.
"""

import sqlite3
import os

def add_contacts_column():
    db_path = "data/rentals.db"
    
    if not os.path.exists(db_path):
        print("Database file not found. No migration needed.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if contacts column already exists
        cursor.execute("PRAGMA table_info(properties)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'contacts' not in columns:
            print("Adding contacts column to properties table...")
            cursor.execute("ALTER TABLE properties ADD COLUMN contacts TEXT")
            conn.commit()
            print("✅ Contacts column added successfully!")
        else:
            print("✅ Contacts column already exists.")
            
    except sqlite3.Error as e:
        print(f"❌ Error during migration: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_contacts_column()
