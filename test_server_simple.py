"""Simple server test"""
import sys
import os

# Set UTF-8 encoding for console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

print("Testing server startup...")
print(f"Python: {sys.version}")
print()

try:
    print("Importing Flask app...")
    import app as server_app
    print("OK - Import successful")
    print()
    
    print("Testing database...")
    conn = server_app.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM global_settings")
    count = cursor.fetchone()[0]
    print(f"OK - Database connected, global_settings has {count} rows")
    conn.close()
    print()
    
    print("Checking APIs...")
    print(f"OpenAI: {'CONFIGURED' if server_app.OPENAI_API_KEY else 'NOT SET'}")
    print(f"Replicate: {'CONFIGURED' if server_app.REPLICATE_API_TOKEN else 'NOT SET'}")
    print()
    
    print("=== ALL CHECKS PASSED ===")
    print("Server should start normally.")
    print()
    print("Try running: python app.py")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

