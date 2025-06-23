#!/usr/bin/env python3
"""
Production deployment script for Auto-DJ Server on Render.

This script helps with deploying the application to Render using the render.yaml blueprint.
It provides guidance and checks for proper configuration.
"""

import os
import sys
import subprocess
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

def check_render_cli():
    """Check if Render CLI is installed."""
    success, version, _ = run_command("render --version", capture_output=True)
    if success:
        print(f"✅ Render CLI is installed: {version}")
        return True
    else:
        print("❌ Render CLI is not installed")
        print("💡 Install it with: npm install -g @render-api/cli")
        return False

def check_git_status():
    """Check if changes are committed and pushed."""
    # Check if we're in a git repository
    success, _, _ = run_command("git status", capture_output=True)
    if not success:
        print("❌ Not in a git repository")
        return False
    
    # Check for uncommitted changes
    success, output, _ = run_command("git status --porcelain", capture_output=True)
    if success and output.strip():
        print("⚠️  You have uncommitted changes:")
        print(output)
        response = input("Continue deployment anyway? (y/N): ").lower()
        if response != 'y':
            return False
    
    # Check if local branch is ahead of remote
    success, output, _ = run_command("git status -b --porcelain", capture_output=True)
    if success and "ahead" in output:
        print("⚠️  Your local branch is ahead of remote")
        print("💡 Make sure to push your changes before deploying")
        response = input("Continue deployment anyway? (y/N): ").lower()
        if response != 'y':
            return False
    
    print("✅ Git status looks good")
    return True

def check_blueprint():
    """Check if render.yaml exists and is valid."""
    blueprint_path = Path("../../render.yaml")
    if not blueprint_path.exists():
        print("❌ render.yaml not found in project root")
        return False
    
    print("✅ render.yaml found")
    
    # Try to validate the YAML
    try:
        import yaml
        with open(blueprint_path, 'r') as f:
            yaml.safe_load(f)
        print("✅ render.yaml is valid YAML")
    except ImportError:
        print("⚠️  PyYAML not installed, skipping YAML validation")
    except Exception as e:
        print(f"❌ render.yaml has syntax errors: {e}")
        return False
    
    return True

def show_deployment_steps():
    """Show the deployment steps."""
    print("\n🚀 Deployment Steps:")
    print("=" * 50)
    print("1. Go to the Render Dashboard: https://dashboard.render.com")
    print("2. Click 'New' → 'Blueprint'")
    print("3. Connect your repository (if not already connected)")
    print("4. Select the repository containing your render.yaml")
    print("5. Review the services that will be created:")
    print("   - autodj-redis (Redis service)")
    print("   - autodj-api (Web service)")
    print("   - autodj-celery-worker (Background worker)")
    print("6. Set the required environment variables:")
    
    print("\n🔐 Required Environment Variables:")
    print("-" * 30)
    env_vars = [
        "SECRET_KEY", "DATABASE_URL", "SPOTIFY_CLIENT_ID", 
        "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REDIRECT_URI",
        "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", 
        "S3_BUCKET_NAME", "CLOUDFRONT_DOMAIN", "CORS_ORIGINS"
    ]
    
    for var in env_vars:
        print(f"   • {var}")
    
    print("\n💡 Tips:")
    print("   • Use your Supabase connection string for DATABASE_URL")
    print("   • Update SPOTIFY_REDIRECT_URI with your Render app URL")
    print("   • Set CORS_ORIGINS to include your frontend domain")
    print("   • Generate a strong SECRET_KEY (64+ characters)")
    
    print("\n7. Click 'Apply' to deploy")
    print("8. Monitor the deployment progress")
    print("9. Test your API at: https://your-app-name.onrender.com/health")

def main():
    """Main function."""
    print("🎵 Auto-DJ Server Production Deployment")
    print("=" * 45)
    
    # Change to the server directory
    script_dir = Path(__file__).parent
    server_dir = script_dir.parent
    os.chdir(server_dir)
    
    # Run checks
    checks_passed = True
    
    if not check_blueprint():
        checks_passed = False
    
    if not check_git_status():
        checks_passed = False
    
    # Optional: Check Render CLI
    check_render_cli()
    
    if not checks_passed:
        print("\n❌ Some checks failed. Please fix the issues before deploying.")
        sys.exit(1)
    
    print("\n✅ All checks passed!")
    
    # Show deployment steps
    show_deployment_steps()
    
    print("\n📚 Additional Resources:")
    print("   • Render Blueprints: https://render.com/docs/infrastructure-as-code")
    print("   • Environment Variables: https://render.com/docs/configure-environment-variables")
    print("   • Deployment Guide: https://render.com/docs/deploy-fastapi")

if __name__ == "__main__":
    main() 