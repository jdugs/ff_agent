#!/usr/bin/env python3
"""
Local development runner
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import psycopg2
        import redis
        print("✅ Dependencies check passed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_services():
    """Check if PostgreSQL and Redis are running"""
    try:
        # Check PostgreSQL
        result = subprocess.run(['pg_isready'], capture_output=True)
        if result.returncode != 0:
            print("❌ PostgreSQL is not running")
            print("Start with: brew services start postgresql (macOS) or sudo service postgresql start (Linux)")
            return False
        
        # Check Redis
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
        if result.stdout.strip() != 'PONG':
            print("❌ Redis is not running")
            print("Start with: brew services start redis (macOS) or sudo service redis-server start (Linux)")
            return False
        
        print("✅ Services check passed")
        return True
        
    except FileNotFoundError:
        print("⚠️  Could not check services automatically")
        print("Please ensure PostgreSQL and Redis are running")
        return True

def run_setup():
    """Run database setup"""
    print("🔧 Running database setup...")
    result = subprocess.run([sys.executable, 'scripts/setup_database.py'])
    return result.returncode == 0

def run_server():
    """Run the FastAPI server"""
    print("🚀 Starting FastAPI server...")
    os.chdir('backend')
    subprocess.run(['uvicorn', 'app.main:app', '--reload', '--host', '0.0.0.0', '--port', '8000'])

def main():
    print("🏈 Fantasy Football Dashboard - Local Development Setup")
    print("=" * 50)
    
    if not check_dependencies():
        sys.exit(1)
    
    if not check_services():
        print("\n💡 Tip: You can also use Docker: docker-compose up")
        sys.exit(1)
    
    if not run_setup():
        print("❌ Database setup failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    run_server()

if __name__ == "__main__":
    main()