#!/usr/bin/env python3
"""
LocalStack AWS CI/CD Services Workshop Setup Script

This script automates the complete workshop setup for multiple users.
"""

import os
import sys
import json
import subprocess
import time
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import argparse

# Configuration
DEFAULT_CONFIG = {
    "role_name": "demo-role",
    "domain_name": "demo-domain",
    "repo_name": "demo-repo", 
    "connection_name": "demo-connection",
    "pipeline_name": "demo-pipeline",
    "github_repo": "lodash/lodash",
    "github_branch": "4.17.21"
}

# ANSI Color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

class WorkshopSetup:
    def __init__(self, config_file: Optional[str] = None):
        self.config = DEFAULT_CONFIG.copy()
        self.config_file = config_file or "workshop_config.json"
        self.setup_logging()
        self.load_config()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('workshop_setup.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def print_colored(self, message: str, color: str = Colors.NC, emoji: str = ""):
        """Print colored message with optional emoji"""
        print(f"{color}{emoji} {message}{Colors.NC}")
        
    def print_header(self, title: str):
        """Print section header"""
        print(f"\n{Colors.BLUE}{'='*50}{Colors.NC}")
        print(f"{Colors.BLUE}{title.center(50)}{Colors.NC}")
        print(f"{Colors.BLUE}{'='*50}{Colors.NC}")
        
    def print_success(self, message: str):
        self.print_colored(message, Colors.GREEN, "✅")
        
    def print_warning(self, message: str):
        self.print_colored(message, Colors.YELLOW, "⚠️")
        
    def print_error(self, message: str):
        self.print_colored(message, Colors.RED, "❌")
        
    def print_info(self, message: str):
        self.print_colored(message, Colors.BLUE, "ℹ️")

    def load_config(self):
        """Load configuration from file if it exists"""
        config_path = Path(self.config_file)
        if config_path.exists():
            self.print_info(f"Loading configuration from {self.config_file}")
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                self.print_success("Configuration loaded successfully")
            except Exception as e:
                self.print_warning(f"Failed to load config: {e}. Using defaults.")
        else:
            self.print_info("No config file found. Using defaults.")
            self.save_config()

    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.print_success(f"Configuration saved to {self.config_file}")
        except Exception as e:
            self.print_error(f"Failed to save config: {e}")

    def run_command(self, command: str, check: bool = True, capture_output: bool = True) -> Tuple[bool, str, str]:
        """Run a shell command and return success status and output"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=capture_output, 
                text=True, 
                check=check
            )
            return True, result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stdout.strip() if e.stdout else "", e.stderr.strip() if e.stderr else ""

    def check_prerequisites(self) -> bool:
        """Check all prerequisites for the workshop"""
        self.print_header("Checking Prerequisites")
        
        # Check Docker
        success, _, _ = self.run_command("docker info", check=False)
        if not success:
            self.print_error("Docker is not running. Please start Docker and try again.")
            return False
        self.print_success("Docker is running")
        
        # Check awslocal
        success, _, _ = self.run_command("which awslocal", check=False)
        if not success:
            self.print_error("awslocal not found. Install with: pip install awscli-local")
            return False
        self.print_success("awslocal is available")
        
        # Check jq
        success, _, _ = self.run_command("which jq", check=False)
        if not success:
            self.print_warning("jq not found. Attempting to install...")
            if not self.install_jq():
                self.print_error("Failed to install jq. Please install manually.")
                return False
        self.print_success("jq is available")
        
        # Check sample app exists
        if not os.path.exists("sample-app/package.json"):
            self.print_error("Sample app not found. Make sure you have the sample-app directory.")
            return False
        self.print_success("Sample application is available")
        
        return True

    def install_jq(self) -> bool:
        """Try to install jq using available package managers"""
        # Try brew (macOS)
        success, _, _ = self.run_command("which brew", check=False)
        if success:
            success, _, _ = self.run_command("brew install jq", check=False)
            return success
            
        # Try apt (Ubuntu/Debian)
        success, _, _ = self.run_command("which apt-get", check=False)
        if success:
            success, _, _ = self.run_command("sudo apt-get update && sudo apt-get install -y jq", check=False)
            return success
            
        # Try yum (RHEL/CentOS)
        success, _, _ = self.run_command("which yum", check=False)
        if success:
            success, _, _ = self.run_command("sudo yum install -y jq", check=False)
            return success
            
        return False

    def start_localstack(self) -> bool:
        """Start LocalStack container"""
        self.print_header("Starting LocalStack")
        
        # Check if LocalStack is already running
        success, output, _ = self.run_command("docker ps | grep localstack/localstack", check=False)
        if success and output:
            self.print_warning("LocalStack container is already running")
            container_id = output.split()[0]
            self.print_info(f"Using existing container: {container_id}")
            return True
            
        # Start new container
        self.print_info("Starting new LocalStack container...")
        
        cmd = (
            f"docker run --rm -d -p 4566:4566 "
            f"-e DEBUG=1 "
            f"--name localstack-workshop "
            f"localstack/localstack"
        )
        
        success, output, error = self.run_command(cmd, check=False)
        if not success:
            self.print_error(f"Failed to start LocalStack: {error}")
            return False
            
        # Wait for LocalStack to be ready
        self.print_info("Waiting for LocalStack to be ready...")
        for i in range(30):
            success, _, _ = self.run_command("awslocal sts get-caller-identity", check=False)
            if success:
                self.print_success("LocalStack is ready")
                return True
            time.sleep(1)
            
        self.print_error("LocalStack failed to start within 30 seconds")
        return False

    def setup_iam(self) -> bool:
        """Setup IAM resources"""
        self.print_header("Setting up IAM Resources")
        
        role_name = self.config['role_name']
        
        # Check if role exists
        success, _, _ = self.run_command(f"awslocal iam get-role --role-name {role_name}", check=False)
        if success:
            self.print_warning(f"Role {role_name} already exists")
        else:
            self.print_info(f"Creating IAM role: {role_name}")
            
            # Create role
            success, _, error = self.run_command(
                f"awslocal iam create-role --role-name {role_name} "
                f"--assume-role-policy-document file://templates/role.json",
                check=False
            )
            if not success:
                self.print_error(f"Failed to create role: {error}")
                return False
                
            # Attach policy
            success, _, error = self.run_command(
                f"awslocal iam put-role-policy --role-name {role_name} "
                f"--policy-name {role_name}-policy "
                f"--policy-document file://templates/policy.json",
                check=False
            )
            if not success:
                self.print_error(f"Failed to attach policy: {error}")
                return False
                
            self.print_success("IAM role and policy created")
        
        self.role_arn = f"arn:aws:iam::000000000000:role/{role_name}"
        self.print_info(f"Role ARN: {self.role_arn}")
        return True

    def setup_codeartifact(self) -> bool:
        """Setup CodeArtifact domain and repository"""
        self.print_header("Setting up CodeArtifact")
        
        domain_name = self.config['domain_name']
        repo_name = self.config['repo_name']
        
        # Create domain
        success, _, _ = self.run_command(
            f"awslocal codeartifact describe-domain --domain {domain_name}", 
            check=False
        )
        if success:
            self.print_warning(f"CodeArtifact domain {domain_name} already exists")
        else:
            self.print_info(f"Creating CodeArtifact domain: {domain_name}")
            success, _, error = self.run_command(
                f"awslocal codeartifact create-domain --domain {domain_name}",
                check=False
            )
            if not success:
                self.print_error(f"Failed to create domain: {error}")
                return False
            self.print_success("CodeArtifact domain created")
        
        # Create repository
        success, _, _ = self.run_command(
            f"awslocal codeartifact describe-repository --domain {domain_name} --repository {repo_name}",
            check=False
        )
        if success:
            self.print_warning(f"CodeArtifact repository {repo_name} already exists")
        else:
            self.print_info(f"Creating CodeArtifact repository: {repo_name}")
            success, _, error = self.run_command(
                f"awslocal codeartifact create-repository --domain {domain_name} --repository {repo_name}",
                check=False
            )
            if not success:
                self.print_error(f"Failed to create repository: {error}")
                return False
            self.print_success("CodeArtifact repository created")
            
        return True

    def setup_source_code(self) -> bool:
        """Create and upload source code zip to S3"""
        self.print_header("Setting up Source Code")
        
        # Create source bucket
        success, _, _ = self.run_command(
            "awslocal s3api head-bucket --bucket demo-source-bucket",
            check=False
        )
        if not success:
            self.print_info("Creating S3 bucket for source code")
            success, _, error = self.run_command(
                "awslocal s3 mb s3://demo-source-bucket",
                check=False
            )
            if not success:
                self.print_error(f"Failed to create source bucket: {error}")
                return False
            self.print_success("Source bucket created")
        else:
            self.print_warning("Source bucket already exists")
        
        # Create zip of sample app
        self.print_info("Creating source code archive...")
        import zipfile
        import os
        
        zip_path = "source-code.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk("sample-app"):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_path = os.path.relpath(file_path, "sample-app")
                    zip_file.write(file_path, arc_path)
        
        self.print_success("Source code archive created")
        
        # Upload to S3
        self.print_info("Uploading source code to S3...")
        success, _, error = self.run_command(
            "awslocal s3 cp source-code.zip s3://demo-source-bucket/source-code.zip",
            check=False
        )
        if not success:
            self.print_error(f"Failed to upload source code: {error}")
            return False
            
        self.print_success("Source code uploaded to S3")
        
        # Clean up local zip file
        try:
            os.remove(zip_path)
        except OSError:
            pass
            
        return True

    def setup_s3_and_buildspecs(self) -> bool:
        """Setup S3 buckets and upload BuildSpecs"""
        self.print_header("Setting up S3 and BuildSpecs")
        
        # Create BuildSpec bucket
        success, _, _ = self.run_command(
            "awslocal s3api head-bucket --bucket demo-buildspecs",
            check=False
        )
        if success:
            self.print_warning("S3 bucket demo-buildspecs already exists")
        else:
            self.print_info("Creating S3 bucket for BuildSpecs")
            success, _, error = self.run_command(
                "awslocal s3 mb s3://demo-buildspecs",
                check=False
            )
            if not success:
                self.print_error(f"Failed to create bucket: {error}")
                return False
            self.print_success("S3 bucket created")
        
        # Upload BuildSpecs
        self.print_info("Uploading BuildSpec files")
        buildspecs = ["demo-test.yaml", "demo-publish.yaml"]
        for buildspec in buildspecs:
            success, _, error = self.run_command(
                f"awslocal s3 cp templates/{buildspec} s3://demo-buildspecs/",
                check=False
            )
            if not success:
                self.print_error(f"Failed to upload {buildspec}: {error}")
                return False
        self.print_success("BuildSpecs uploaded")
        
        # Create artifact bucket
        success, _, _ = self.run_command(
            "awslocal s3api head-bucket --bucket demo-artif-bucket",
            check=False
        )
        if success:
            self.print_warning("S3 bucket demo-artif-bucket already exists")
        else:
            self.print_info("Creating S3 bucket for artifacts")
            success, _, error = self.run_command(
                "awslocal s3 mb s3://demo-artif-bucket",
                check=False
            )
            if not success:
                self.print_error(f"Failed to create artifact bucket: {error}")
                return False
            self.print_success("Artifact bucket created")
            
        return True

    def setup_codebuild(self) -> bool:
        """Setup CodeBuild projects"""
        self.print_header("Setting up CodeBuild Projects")
        
        projects = [
            ("demo-test", "demo-test.yaml"),
            ("demo-publish", "demo-publish.yaml")
        ]
        
        for project_name, buildspec_file in projects:
            # Check if project exists
            success, _, _ = self.run_command(
                f"awslocal codebuild describe-projects --names {project_name}",
                check=False
            )
            if success:
                self.print_warning(f"CodeBuild project {project_name} already exists")
                continue
                
            self.print_info(f"Creating CodeBuild project: {project_name}")
            cmd = (
                f"awslocal codebuild create-project "
                f"--name {project_name} "
                f"--source type=CODEPIPELINE,buildspec=arn:aws:s3:::demo-buildspecs/{buildspec_file} "
                f"--artifacts type=CODEPIPELINE "
                f"--environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL "
                f"--service-role {self.role_arn}"
            )
            
            success, _, error = self.run_command(cmd, check=False)
            if not success:
                self.print_error(f"Failed to create project {project_name}: {error}")
                return False
            self.print_success(f"{project_name} project created")
            
        return True

    def setup_codepipeline(self) -> bool:
        """Setup CodePipeline"""
        self.print_header("Setting up CodePipeline")
        
        pipeline_name = self.config['pipeline_name']
        
        # Generate pipeline definition
        self.print_info("Generating pipeline definition")
        pipeline_def = self.generate_pipeline_definition()
        
        # Save pipeline definition
        with open('generated_pipeline.json', 'w') as f:
            json.dump(pipeline_def, f, indent=2)
        
        # Create or update pipeline
        success, _, _ = self.run_command(
            f"awslocal codepipeline get-pipeline --name {pipeline_name}",
            check=False
        )
        if success:
            self.print_warning(f"Pipeline {pipeline_name} already exists")
            self.print_info("Updating pipeline...")
            success, _, error = self.run_command(
                "awslocal codepipeline update-pipeline --pipeline file://generated_pipeline.json",
                check=False
            )
            if not success:
                self.print_error(f"Failed to update pipeline: {error}")
                return False
            self.print_success("Pipeline updated")
        else:
            self.print_info(f"Creating pipeline: {pipeline_name}")
            success, _, error = self.run_command(
                "awslocal codepipeline create-pipeline --pipeline file://generated_pipeline.json",
                check=False
            )
            if not success:
                self.print_error(f"Failed to create pipeline: {error}")
                return False
            self.print_success("Pipeline created")
            
        return True

    def generate_pipeline_definition(self) -> Dict:
        """Generate pipeline definition from configuration"""
        return {
            "pipelineType": "V1",
            "name": self.config['pipeline_name'],
            "roleArn": self.role_arn,
            "artifactStore": {
                "type": "S3",
                "location": "demo-artif-bucket"
            },
            "stages": [
                {
                    "name": "source",
                    "actions": [
                        {
                            "name": "get-source-code",
                            "actionTypeId": {
                                "category": "Source",
                                "owner": "AWS",
                                "provider": "S3",
                                "version": "1"
                            },
                            "outputArtifacts": [
                                {
                                    "name": "source-code"
                                }
                            ],
                            "configuration": {
                                "S3Bucket": "demo-source-bucket",
                                "S3ObjectKey": "source-code.zip",
                                "PollForSourceChanges": "false"
                            }
                        }
                    ]
                },
                {
                    "name": "test",
                    "actions": [
                        {
                            "name": "run-tests",
                            "actionTypeId": {
                                "category": "Test",
                                "owner": "AWS",
                                "provider": "CodeBuild",
                                "version": "1"
                            },
                            "inputArtifacts": [
                                {
                                    "name": "source-code"
                                }
                            ],
                            "configuration": {
                                "ProjectName": "demo-test"
                            }
                        }
                    ]
                },
                {
                    "name": "publish",
                    "actions": [
                        {
                            "name": "publish-package",
                            "actionTypeId": {
                                "category": "Build",
                                "owner": "AWS",
                                "provider": "CodeBuild",
                                "version": "1"
                            },
                            "inputArtifacts": [
                                {
                                    "name": "source-code"
                                }
                            ],
                            "configuration": {
                                "ProjectName": "demo-publish"
                            }
                        }
                    ]
                }
            ]
        }

    def show_status(self):
        """Display setup completion status and next steps"""
        self.print_header("Workshop Setup Complete!")
        
        print(f"{Colors.GREEN}🎉 Your LocalStack CI/CD workshop is ready!{Colors.NC}")
        print()
        print(f"{Colors.BLUE}Resources Created:{Colors.NC}")
        print(f"  • IAM Role: {self.role_arn}")
        print(f"  • CodeArtifact Domain: {self.config['domain_name']}")
        print(f"  • CodeArtifact Repository: {self.config['repo_name']}")
        print(f"  • GitHub Connection: {self.config['connection_name']}")
        print(f"  • CodeBuild Projects: demo-test, demo-publish")
        print(f"  • CodePipeline: {self.config['pipeline_name']}")
        print()
        print(f"{Colors.BLUE}Next Steps:{Colors.NC}")
        print(f"  1. Monitor pipeline: {Colors.YELLOW}python monitor_pipeline.py{Colors.NC}")
        print(f"  2. Check packages: {Colors.YELLOW}python check_packages.py{Colors.NC}")
        print(f"  3. View logs: {Colors.YELLOW}python view_logs.py{Colors.NC}")
        print(f"  4. Cleanup: {Colors.YELLOW}python cleanup_workshop.py{Colors.NC}")
        print()
        print(f"{Colors.BLUE}Useful Commands:{Colors.NC}")
        print(f"  • awslocal codepipeline list-pipeline-executions --pipeline-name {self.config['pipeline_name']}")
        print(f"  • awslocal codeartifact list-packages --domain {self.config['domain_name']} --repository {self.config['repo_name']}")
        print(f"  • docker logs -f localstack-workshop")

    def run_setup(self) -> bool:
        """Run the complete workshop setup"""
        self.print_header("LocalStack CI/CD Workshop Setup")
        
        try:
            if not self.check_prerequisites():
                return False
                
            if not self.start_localstack():
                return False
                
            if not self.setup_iam():
                return False
                
            if not self.setup_codeartifact():
                return False
                
            if not self.setup_source_code():
                return False
                
            if not self.setup_s3_and_buildspecs():
                return False
                
            if not self.setup_codebuild():
                return False
                
            if not self.setup_codepipeline():
                return False
                
            self.show_status()
            return True
            
        except KeyboardInterrupt:
            self.print_warning("Setup interrupted by user")
            return False
        except Exception as e:
            self.print_error(f"Unexpected error: {e}")
            self.logger.exception("Setup failed with exception")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='LocalStack CI/CD Workshop Setup')
    parser.add_argument('--config', '-c', help='Configuration file path', default='workshop_config.json')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    setup = WorkshopSetup(args.config)
    
    success = setup.run_setup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()