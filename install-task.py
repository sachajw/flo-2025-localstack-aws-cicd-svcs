#!/usr/bin/env python3
"""
Install Task runner for easy workshop commands
"""

import platform
import subprocess
import sys
import os

def run_command(command):
    """Run command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()

def install_task():
    """Install Task runner based on platform"""
    system = platform.system().lower()
    
    print("🔧 Installing Task runner...")
    
    if system == "darwin":  # macOS
        print("Detected macOS - trying Homebrew...")
        success, output = run_command("brew --version")
        if success:
            print("Installing Task via Homebrew...")
            success, _ = run_command("brew install go-task/tap/go-task")
            if success:
                print("✅ Task installed successfully!")
                return True
        
        # Fallback to direct download
        print("Downloading Task binary...")
        success, _ = run_command("sh -c \"$(curl -ssL https://taskfile.dev/install.sh)\" -- -d -b ~/.local/bin")
        if success:
            print("✅ Task installed to ~/.local/bin/task")
            print("Add ~/.local/bin to your PATH")
            return True
            
    elif system == "linux":
        # Try package managers
        print("Detected Linux - trying package managers...")
        
        # Try snap first
        success, _ = run_command("snap install task --classic")
        if success:
            print("✅ Task installed via snap!")
            return True
            
        # Try direct download
        print("Downloading Task binary...")
        success, _ = run_command("sh -c \"$(curl -ssL https://taskfile.dev/install.sh)\" -- -d -b ~/.local/bin")
        if success:
            print("✅ Task installed to ~/.local/bin/task")
            print("Add ~/.local/bin to your PATH or run: sudo mv ~/.local/bin/task /usr/local/bin/")
            return True
            
    elif system == "windows":
        print("Detected Windows - trying package managers...")
        
        # Try chocolatey
        success, _ = run_command("choco install go-task")
        if success:
            print("✅ Task installed via Chocolatey!")
            return True
            
        # Try scoop
        success, _ = run_command("scoop install task")
        if success:
            print("✅ Task installed via Scoop!")
            return True
            
        print("❌ Please install Task manually:")
        print("   • Download from: https://github.com/go-task/task/releases")
        print("   • Or install Chocolatey/Scoop first")
        return False
    
    print(f"❌ Unsupported platform: {system}")
    print("Visit https://taskfile.dev/installation/ for manual installation")
    return False

def main():
    """Main entry point"""
    print("Task Runner Installer")
    print("=" * 30)
    
    # Check if Task is already installed
    success, version = run_command("task --version")
    if success:
        print(f"✅ Task is already installed: {version}")
        print("\nYou can now use:")
        print("  task start    # Setup and run workshop")
        print("  task help     # Show all commands")
        return
    
    print("Task not found - installing...")
    
    if install_task():
        print("\n🎉 Installation complete!")
        print("\nNow you can use:")
        print("  task start    # Setup and run workshop")  
        print("  task help     # Show all commands")
        
        # Test installation
        success, _ = run_command("task --version")
        if not success:
            print("\n⚠️  You may need to restart your terminal or update your PATH")
    else:
        print("\n❌ Installation failed")
        print("Don't worry - you can still use Python scripts directly:")
        print("  python3 setup_workshop.py")
        print("  python3 monitor_pipeline.py")
        sys.exit(1)

if __name__ == "__main__":
    main()