"""Database initialization script for Railway deployment."""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, get_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_admin_user():
    """Create default admin user if not exists."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if admin exists
    admin = cursor.execute(
        "SELECT id FROM users WHERE username = ?", 
        ('King',)
    ).fetchone()
    
    if not admin:
        print("Creating default admin user 'King'...", flush=True)
        # Note: Password hash should be set properly via auth endpoint
        # This just ensures the user exists
        try:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
            """, ('King', 'asanalivoin@gmail.com', 'needs_password_update', 1))
            conn.commit()
            print("✅ Admin user 'King' created", flush=True)
        except Exception as e:
            print(f"⚠️  Admin user might already exist: {e}", flush=True)
    else:
        print(f"✅ Admin user 'King' exists (ID={admin[0]})", flush=True)
    
    # Show all users
    users = cursor.execute(
        "SELECT id, username, is_admin FROM users"
    ).fetchall()
    
    print(f"\nTotal users: {len(users)}", flush=True)
    for u in users:
        print(f"  ID={u[0]}, Username={u[1]}, Admin={'Yes' if u[2] else 'No'}", flush=True)
    
    conn.close()

def main():
    print("=" * 60, flush=True)
    print("Initializing database for Railway deployment", flush=True)
    print("=" * 60, flush=True)
    
    # Initialize database schema
    print("\n[1/2] Creating database schema...", flush=True)
    init_db()
    print("✅ Database initialized", flush=True)
    
    # Create admin user
    print("\n[2/2] Setting up admin user...", flush=True)
    init_admin_user()
    
    print("\n" + "=" * 60, flush=True)
    print("✅ Database setup complete!", flush=True)
    print("=" * 60, flush=True)

if __name__ == '__main__':
    main()
