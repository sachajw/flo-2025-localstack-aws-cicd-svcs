#!/usr/bin/env python3
"""
Check published packages in CodeArtifact
"""

import json
import subprocess
import sys

class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    BOLD = '\033[1m'
    NC = '\033[0m'

def run_command(command):
    """Run command and return output"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        return result.returncode == 0, result.stdout.strip()
    except:
        return False, ""

def print_status(message, color=Colors.NC, emoji=""):
    print(f"{color}{emoji} {message}{Colors.NC}")

def check_packages():
    """Check packages in CodeArtifact repository"""
    print(f"{Colors.BLUE}{Colors.BOLD}📦 CodeArtifact Packages{Colors.NC}")
    print("=" * 40)
    
    # List packages
    success, output = run_command("awslocal codeartifact list-packages --domain demo-domain --repository demo-repo")
    if not success:
        print_status("Failed to list packages", Colors.RED, "❌")
        print_status("Is LocalStack running? Try: python3 setup_workshop.py", Colors.YELLOW, "💡")
        return False
        
    try:
        packages = json.loads(output)
        package_list = packages.get('packages', [])
        
        if not package_list:
            print_status("No packages found yet", Colors.YELLOW, "📭")
            print_status("Pipeline may still be running. Check: python3 monitor_pipeline.py", Colors.BLUE, "🔄")
            return False
            
        print_status(f"Found {len(package_list)} package(s):", Colors.GREEN, "📦")
        
        for package in package_list:
            package_name = package['package']
            format_type = package['format']
            print(f"   • {Colors.BOLD}{package_name}{Colors.NC} ({format_type})")
            
            # Get package versions
            success, version_output = run_command(
                f"awslocal codeartifact list-package-versions --domain demo-domain --repository demo-repo --format {format_type} --package {package_name}"
            )
            if success:
                try:
                    versions = json.loads(version_output)
                    version_list = versions.get('versions', [])
                    if version_list:
                        latest_version = version_list[0]['version']
                        print(f"     Version: {Colors.GREEN}{latest_version}{Colors.NC}")
                        print(f"     Published: {Colors.BLUE}{version_list[0].get('publishedTime', 'Unknown')}{Colors.NC}")
                except json.JSONDecodeError:
                    pass
        
        # Show npm install instructions
        if any(p['format'] == 'npm' for p in package_list):
            print(f"\n{Colors.BLUE}📥 To use the package:{Colors.NC}")
            print("1. Configure npm:")
            print(f"   {Colors.YELLOW}awslocal codeartifact login --tool npm --domain demo-domain --repository demo-repo{Colors.NC}")
            print("2. Install package:")
            print(f"   {Colors.YELLOW}npm install localstack-workshop-demo{Colors.NC}")
            print("3. Or download:")
            print(f"   {Colors.YELLOW}npm pack localstack-workshop-demo{Colors.NC}")
            
        return True
        
    except json.JSONDecodeError:
        print_status("Failed to parse package list", Colors.RED, "❌")
        return False

def show_repository_info():
    """Show repository information"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}🏪 Repository Information{Colors.NC}")
    print("=" * 40)
    
    success, output = run_command("awslocal codeartifact describe-repository --domain demo-domain --repository demo-repo")
    if success:
        try:
            repo_info = json.loads(output)
            repo = repo_info.get('repository', {})
            
            print(f"Name: {Colors.BOLD}{repo.get('name', 'Unknown')}{Colors.NC}")
            print(f"Domain: {Colors.BOLD}{repo.get('domainName', 'Unknown')}{Colors.NC}")
            print(f"Description: {repo.get('description', 'LocalStack CI/CD Workshop Repository')}")
            
            # Show endpoint
            success, endpoint_output = run_command("awslocal codeartifact get-repository-endpoint --domain demo-domain --repository demo-repo --format npm")
            if success:
                try:
                    endpoint_info = json.loads(endpoint_output)
                    endpoint = endpoint_info.get('repositoryEndpoint', '')
                    print(f"NPM Endpoint: {Colors.BLUE}{endpoint}{Colors.NC}")
                except json.JSONDecodeError:
                    pass
                    
        except json.JSONDecodeError:
            pass

def main():
    """Main entry point"""
    # Check LocalStack connection
    success, _ = run_command("awslocal sts get-caller-identity")
    if not success:
        print_status("LocalStack not accessible", Colors.RED, "❌")
        print_status("Start with: python3 setup_workshop.py", Colors.YELLOW, "💡")
        sys.exit(1)
    
    packages_found = check_packages()
    show_repository_info()
    
    if packages_found:
        print(f"\n{Colors.GREEN}🎉 Workshop completed successfully!{Colors.NC}")
        print(f"{Colors.BLUE}This demonstrates LocalStack's CI/CD capabilities:{Colors.NC}")
        print("   ✓ CodePipeline orchestration")
        print("   ✓ CodeBuild execution") 
        print("   ✓ CodeArtifact package publishing")
        print("   ✓ GitHub integration via CodeConnections")
        print("   ✓ All running locally!")
    else:
        print(f"\n{Colors.YELLOW}⏳ Packages not ready yet{Colors.NC}")
        print("Monitor pipeline: python3 monitor_pipeline.py")

if __name__ == "__main__":
    main()