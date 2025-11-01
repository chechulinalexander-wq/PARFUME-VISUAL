"""Test server startup"""
import sys
import traceback

print("Testing server startup...")
print(f"Python version: {sys.version}")
print(f"Working directory: {sys.path[0]}")
print()

try:
    print("Importing app.py...")
    import app
    print("✓ Import successful!")
    print()
    
    print("Checking Flask app...")
    print(f"✓ Flask app created: {app.app}")
    print()
    
    print("Checking configuration...")
    print(f"OPENAI_API_KEY: {'SET' if app.OPENAI_API_KEY else 'NOT SET'}")
    print(f"REPLICATE_API_TOKEN: {'SET' if app.REPLICATE_API_TOKEN else 'NOT SET'}")
    print(f"DB_PATH: {app.DB_PATH}")
    print()
    
    print("Testing database connection...")
    conn = app.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"✓ Database tables: {[t[0] for t in tables]}")
    conn.close()
    print()
    
    print("All checks passed!")
    print("Server should be able to start.")
    
except Exception as e:
    print(f"✗ ERROR: {e}")
    print()
    print("Full traceback:")
    traceback.print_exc()
    sys.exit(1)

