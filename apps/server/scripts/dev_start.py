#!/usr/bin/env python3
"""
Development startup script for the Auto-DJ Server.

This script:
1. Checks if Docker is available and running
2. Starts Docker Compose services (postgres, redis) if needed
3. Waits for services to be healthy
4. Starts the FastAPI server in development mode
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path

def run_command(cmd, shell=True, capture_output=False):
    """Run a command and return the result."""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(cmd, shell=shell)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def check_docker():
    """Check if Docker is available and running."""
    print("🔍 Checking Docker availability...")
    
    # Check if docker command is available
    success, _, _ = run_command("docker --version", capture_output=True)
    if not success:
        print("❌ Docker is not installed or not in PATH")
        return False
    
    # Check if Docker daemon is running
    success, _, _ = run_command("docker info", capture_output=True)
    if not success:
        print("❌ Docker daemon is not running")
        return False
    
    print("✅ Docker is available and running")
    return True

def check_services():
    """Check if required services are already running."""
    print("🔍 Checking if services are already running...")
    
    success, output, _ = run_command("docker compose ps --services --filter status=running", capture_output=True)
    if success and output:
        running_services = output.split('\n')
        postgres_running = 'postgres' in running_services
        redis_running = 'redis' in running_services
        
        if postgres_running and redis_running:
            print("✅ PostgreSQL and Redis are already running")
            return True
    
    return False

def cleanup_stopped_containers():
    """Remove stopped containers that might conflict with our service names."""
    print("🧹 Cleaning up any stopped containers...")
    
    # List of container names that might conflict
    container_names = ["autodj-postgres", "autodj-redis"]
    
    for container_name in container_names:
        # Check if container exists
        success, output, _ = run_command(f"docker ps -a --filter name={container_name} --format '{{{{.Names}}}}'", capture_output=True)
        if success and container_name in output:
            # Check if it's running
            success, running_output, _ = run_command(f"docker ps --filter name={container_name} --format '{{{{.Names}}}}'", capture_output=True)
            if success and container_name not in running_output:
                # Container exists but is not running, remove it
                print(f"🗑️  Removing stopped container: {container_name}")
                remove_success, _, error = run_command(f"docker rm {container_name}", capture_output=True)
                if not remove_success:
                    print(f"⚠️  Could not remove container {container_name}: {error}")
    
    return True

def start_services():
    """Start Docker Compose services."""
    print("🚀 Starting Docker services (PostgreSQL, Redis)...")
    
    # Clean up any stopped containers first
    cleanup_stopped_containers()
    
    success, _, error = run_command("docker compose up -d postgres redis")
    if not success:
        # If it failed due to container conflicts, try to handle it
        if "already in use" in error.lower() or "conflict" in error.lower():
            print("🔄 Container name conflict detected, attempting to resolve...")
            
            # Try to remove any conflicting containers more aggressively
            container_names = ["autodj-postgres", "autodj-redis"]
            for container_name in container_names:
                print(f"🗑️  Force removing container: {container_name}")
                run_command(f"docker rm -f {container_name}", capture_output=True)
            
            # Try starting services again
            print("🔄 Retrying service startup...")
            success, _, retry_error = run_command("docker compose up -d postgres redis")
            if not success:
                print(f"❌ Failed to start services after cleanup: {retry_error}")
                print("💡 Try running: npm run docker:down && npm run docker:up")
                return False
        else:
            print(f"❌ Failed to start services: {error}")
            return False
    
    print("⏳ Waiting for services to be healthy...")
    
    # Wait for services to be healthy (max 60 seconds)
    for i in range(60):
        success, output, _ = run_command("docker compose ps --format json", capture_output=True)
        if success:
            try:
                import json
                services = [json.loads(line) for line in output.split('\n') if line.strip()]
                postgres_healthy = any(s.get('Name', '').endswith('postgres') and s.get('Health', '') == 'healthy' for s in services)
                redis_healthy = any(s.get('Name', '').endswith('redis') and s.get('Health', '') == 'healthy' for s in services)
                
                if postgres_healthy and redis_healthy:
                    print("✅ All services are healthy")
                    return True
            except:
                pass
        
        time.sleep(1)
    
    print("⚠️  Services may not be fully healthy yet, but continuing...")
    return True

def start_api_server():
    """Start the FastAPI development server."""
    print("🚀 Starting FastAPI development server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/api/v1/docs")
    print("🔗 Health check: http://localhost:8000/health")
    print("\n💡 To start the Celery worker separately, run: npm run dev:worker")
    print("💡 To start Celery beat separately, run: npm run dev:beat")
    print("\n🛑 Press Ctrl+C to stop the server\n")
    
    # Start the server
    os.execvp("uvicorn", ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])

def cleanup_handler(signum, frame):
    """Handle cleanup on exit."""
    print("\n\n🛑 Shutting down...")
    print("💡 To stop Docker services, run: npm run docker:down")
    sys.exit(0)

def main():
    """Main function."""
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    print("🎵 Auto-DJ Server Development Startup")
    print("=" * 40)
    
    # Change to the server directory
    script_dir = Path(__file__).parent
    server_dir = script_dir.parent
    os.chdir(server_dir)
    
    # Check if .env file exists
    if not Path(".env").exists():
        print("⚠️  .env file not found. Please create one based on env.production")
        print("💡 You can copy env.production to .env and modify it for local development")
        sys.exit(1)
    
    # Check Docker and start services if needed
    if check_docker():
        if not check_services():
            if not start_services():
                print("\n❌ Failed to start required services")
                print("\n🛠️  Troubleshooting steps:")
                print("   1. Try: npm run docker:clean (cleans everything)")
                print("   2. Try: npm run docker:down && npm run docker:up")  
                print("   3. Check if ports 5432/6379 are in use: lsof -i :5432 -i :6379")
                print("   4. Restart Docker Desktop if on macOS/Windows")
                sys.exit(1)
        else:
            print("✅ Services are already running")
    else:
        print("⚠️  Docker not available. Make sure PostgreSQL and Redis are running manually.")
        print("   PostgreSQL: localhost:5432 (database: autodj, user: autodj, password: password)")
        print("   Redis: localhost:6379")
        
        response = input("\nContinue anyway? (y/N): ").lower()
        if response != 'y':
            sys.exit(1)
    
    # Start the API server
    start_api_server()

if __name__ == "__main__":
    main() 