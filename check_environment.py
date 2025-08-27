#!/usr/bin/env python3
"""
Environment Prerequisites Checker for LocalStack CI/CD Workshop

This script checks all prerequisites and provides clear instructions.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m' 
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    BOLD = '\033[1m'
    NC = '\033[0m'

class PrereqChecker:
    def __init__(self):
        self.all_good = True
        self.system = platform.system().lower()
        
    def print_colored(self, message: str, color: str = Colors.NC, emoji: str = ""):
        print(f"{color}{emoji} {message}{Colors.NC}")
        
    def print_header(self, title: str):
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.NC}")
        print(f"{Colors.BLUE}{Colors.BOLD}{title.center(60)}{Colors.NC}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*60}{Colors.NC}")
        
    def print_success(self, message: str):
        self.print_colored(message, Colors.GREEN, "✅")
        
    def print_error(self, message: str):
        self.print_colored(message, Colors.RED, "❌")
        self.all_good = False
        
    def print_warning(self, message: str):
        self.print_colored(message, Colors.YELLOW, "⚠️")
        
    def print_info(self, message: str):
        self.print_colored(message, Colors.CYAN, "ℹ️")

    def print_instruction(self, message: str):
        self.print_colored(message, Colors.PURPLE, "👉")

    def check_command(self, command: str) -> bool:
        """Check if a command exists"""
        return shutil.which(command) is not None
    
    def run_command(self, command: str) -> tuple[bool, str]:
        """Run command and return success status and output"""
        try:
            result = subprocess.run(
                command.split(), 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0, result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False, ""

    def check_python(self):
        """Check Python version"""
        self.print_info("Checking Python...")
        
        version = sys.version_info
        if version.major >= 3 and version.minor >= 8:
            self.print_success(f"Python {version.major}.{version.minor}.{version.micro} ✓")
        else:
            self.print_error(f"Python {version.major}.{version.minor}.{version.micro} is too old")
            self.print_instruction("Install Python 3.8+ from https://python.org")

    def check_docker(self):
        """Check Docker installation and status"""
        self.print_info("Checking Docker...")
        
        # Check if docker command exists
        if not self.check_command("docker"):
            self.print_error("Docker not found")
            self.provide_docker_installation_instructions()
            return
            
        # Check Docker version
        success, version_output = self.run_command("docker --version")
        if not success:
            self.print_error("Docker command failed")
            return
            
        self.print_success(f"Docker installed: {version_output}")
        
        # Check if Docker daemon is running
        success, _ = self.run_command("docker info")
        if not success:
            self.print_error("Docker daemon is not running")
            self.print_instruction("Start Docker Desktop or run: sudo systemctl start docker")
            return
            
        self.print_success("Docker daemon is running ✓")

    def provide_docker_installation_instructions(self):
        """Provide OS-specific Docker installation instructions"""
        self.print_instruction("Install Docker:")
        
        if self.system == "darwin":  # macOS
            print("   • Download Docker Desktop: https://docs.docker.com/desktop/mac/install/")
            print("   • Or install via Homebrew: brew install --cask docker")
        elif self.system == "linux":
            print("   • Ubuntu/Debian: sudo apt update && sudo apt install docker.io")
            print("   • RHEL/CentOS: sudo yum install docker")
            print("   • Or follow: https://docs.docker.com/engine/install/")
        elif self.system == "windows":
            print("   • Download Docker Desktop: https://docs.docker.com/desktop/windows/install/")
        else:
            print("   • Visit: https://docs.docker.com/get-docker/")

    def check_localstack_container(self):
        """Check if LocalStack container image is available"""
        self.print_info("Checking LocalStack container...")
        
        # Try to pull LocalStack image
        self.print_info("Pulling LocalStack image (this may take a moment)...")
        success, output = self.run_command("docker pull localstack/localstack")
        
        if success:
            self.print_success("LocalStack container image ready ✓")
        else:
            self.print_error("Failed to pull LocalStack container")
            self.print_instruction("Check your internet connection and Docker setup")

    def check_awscli_local(self):
        """Check AWS CLI and awslocal wrapper"""
        self.print_info("Checking AWS CLI tools...")
        
        # Check awslocal
        if not self.check_command("awslocal"):
            self.print_error("awslocal not found")
            self.print_instruction("Install with: pip install awscli-local")
        else:
            self.print_success("awslocal found ✓")
            
        # Test awslocal works (when LocalStack is not running)
        success, _ = self.run_command("awslocal --version")
        if success:
            self.print_success("awslocal is functional ✓")
        else:
            self.print_warning("awslocal may not be working correctly")

    def check_github_token(self):
        """Check GitHub Personal Access Token"""
        self.print_info("Checking GitHub token...")
        
        token = os.environ.get('CODEPIPELINE_GH_TOKEN')
        if not token:
            self.print_error("CODEPIPELINE_GH_TOKEN environment variable not set")
            self.print_instruction("Get a GitHub Personal Access Token:")
            print("   1. Go to https://github.com/settings/tokens")
            print("   2. Click 'Generate new token (classic)'")
            print("   3. Select 'repo' permissions")
            print("   4. Copy the token and set it:")
            print(f"      {Colors.YELLOW}export CODEPIPELINE_GH_TOKEN='your_token_here'{Colors.NC}")
            return
            
        # Basic token validation (should start with ghp_)
        if not token.startswith(('ghp_', 'github_pat_')):
            self.print_warning("Token doesn't look like a GitHub Personal Access Token")
            self.print_info("GitHub tokens usually start with 'ghp_' or 'github_pat_'")
        else:
            self.print_success("GitHub token is set ✓")
            
        # Show partial token for verification
        masked_token = token[:8] + '*' * (len(token) - 12) + token[-4:] if len(token) > 12 else token[:4] + '*' * 4
        self.print_info(f"Token: {masked_token}")

    def check_optional_tools(self):
        """Check optional but helpful tools"""
        self.print_info("Checking optional tools...")
        
        tools = {
            'jq': 'JSON processor for parsing AWS CLI output',
            'curl': 'HTTP client for API testing',
            'git': 'Version control (usually pre-installed)'
        }
        
        for tool, description in tools.items():
            if self.check_command(tool):
                self.print_success(f"{tool}: {description} ✓")
            else:
                self.print_warning(f"{tool}: {description} (missing)")

    def check_required_files(self):
        """Check if workshop files are present"""
        self.print_info("Checking workshop files...")
        
        required_files = [
            'setup_workshop.py',
            'Taskfile.yml',
            'templates/role.json',
            'templates/policy.json',
            'templates/demo-test.yaml',
            'templates/demo-publish.yaml'
        ]
        
        for file_path in required_files:
            if Path(file_path).exists():
                self.print_success(f"{file_path} ✓")
            else:
                self.print_error(f"{file_path} missing")
                
        # Check if templates directory exists
        if not Path('templates').exists():
            self.print_error("templates/ directory missing")
            self.print_instruction("Run: mkdir templates")

    def check_task_runner(self):
        """Check if Task runner is available"""
        self.print_info("Checking Task runner...")
        
        if self.check_command("task"):
            success, version = self.run_command("task --version")
            if success:
                self.print_success(f"Task runner available: {version} ✓")
            else:
                self.print_success("Task runner available ✓")
        else:
            self.print_warning("Task runner not found (optional)")
            self.print_instruction("Install Task runner:")
            if self.system == "darwin":
                print("   • brew install go-task/tap/go-task")
            else:
                print("   • Visit https://taskfile.dev/installation/")
            print("   • Or run Python scripts directly")

    def show_summary(self):
        """Show final summary and next steps"""
        self.print_header("SUMMARY")
        
        if self.all_good:
            self.print_success("🎉 All prerequisites met! You're ready to start.")
            print()
            self.print_info("Quick Start:")
            print("   1. Run the setup: python3 setup_workshop.py")
            print("   2. Or use Task: task start")
            print()
        else:
            self.print_error("❌ Some prerequisites are missing.")
            print()
            self.print_instruction("Fix the issues above, then run this check again:")
            print("   python3 check_environment.py")
            print()
            
        self.print_info("Workshop Resources:")
        print("   • README.md - Complete workshop guide")
        print("   • CLAUDE.md - Reference for Claude Code")
        print("   • Taskfile.yml - Easy commands with Task")
        
    def run_all_checks(self):
        """Run all prerequisite checks"""
        self.print_header("LocalStack CI/CD Workshop - Prerequisites Check")
        
        print(f"{Colors.CYAN}This will check if you have everything needed for the workshop.{Colors.NC}")
        print()
        
        # Core requirements
        self.check_python()
        self.check_docker()
        self.check_localstack_container()
        self.check_awscli_local()
        self.check_github_token()
        
        # Workshop files
        self.check_required_files()
        
        # Optional tools
        self.check_task_runner()
        self.check_optional_tools()
        
        # Summary
        self.show_summary()
        
        return self.all_good

def main():
    """Main entry point"""
    checker = PrereqChecker()
    
    try:
        success = checker.run_all_checks()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Check interrupted by user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()