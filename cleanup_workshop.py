#!/usr/bin/env python3
"""
Workshop Cleanup Script

This script safely removes all workshop resources from LocalStack.
"""

import os
import sys
import json
import subprocess
import time
from typing import Tuple, List
import argparse

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

class WorkshopCleanup:
    def __init__(self, force: bool = False, keep_container: bool = False):
        self.force = force
        self.keep_container = keep_container
        self.resources_found = []
        self.cleanup_errors = []
        
    def print_colored(self, message: str, color: str = Colors.NC, emoji: str = ""):
        print(f"{color}{emoji} {message}{Colors.NC}")
        
    def print_header(self, title: str):
        print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*50}{Colors.NC}")
        print(f"{Colors.BLUE}{Colors.BOLD}{title.center(50)}{Colors.NC}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*50}{Colors.NC}")
        
    def print_success(self, message: str):
        self.print_colored(message, Colors.GREEN, "✅")
        
    def print_error(self, message: str):
        self.print_colored(message, Colors.RED, "❌")
        
    def print_warning(self, message: str):
        self.print_colored(message, Colors.YELLOW, "⚠️")
        
    def print_info(self, message: str):
        self.print_colored(message, Colors.CYAN, "ℹ️")

    def run_command(self, command: str, check: bool = True) -> Tuple[bool, str, str]:
        """Run a shell command and return success status and output"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=check,
                timeout=30
            )
            return True, result.stdout.strip(), result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stdout.strip() if e.stdout else "", e.stderr.strip() if e.stderr else ""
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
    
    def aws_command(self, service_command: str, check: bool = True) -> Tuple[bool, str, str]:
        """Run AWS CLI command with LocalStack endpoint configuration"""
        full_command = f"AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 {service_command}"
        return self.run_command(full_command, check=check)

    def check_localstack_connection(self) -> bool:
        """Check if LocalStack is accessible"""
        success, _, _ = self.aws_command("sts get-caller-identity", check=False)
        return success

    def cleanup_codepipeline(self):
        """Delete CodePipeline resources"""
        self.print_info("Cleaning up CodePipeline resources...")
        
        # List pipelines
        success, output, _ = self.aws_command("codepipeline list-pipelines", check=False)
        if not success:
            return
            
        try:
            pipelines = json.loads(output)
            for pipeline in pipelines.get('pipelines', []):
                pipeline_name = pipeline['name']
                if 'demo' in pipeline_name.lower():
                    self.print_info(f"Deleting pipeline: {pipeline_name}")
                    success, _, error = self.aws_command(f"codepipeline delete-pipeline --name {pipeline_name}",
                        check=False
                    )
                    if success:
                        self.print_success(f"Pipeline {pipeline_name} deleted")
                        self.resources_found.append(f"Pipeline: {pipeline_name}")
                    else:
                        self.print_error(f"Failed to delete pipeline {pipeline_name}: {error}")
                        self.cleanup_errors.append(f"Pipeline {pipeline_name}: {error}")
        except json.JSONDecodeError:
            self.print_warning("Could not parse pipelines list")

    def cleanup_codebuild(self):
        """Delete CodeBuild projects"""
        self.print_info("Cleaning up CodeBuild projects...")
        
        # List projects
        success, output, _ = self.aws_command("codebuild list-projects", check=False)
        if not success:
            return
            
        try:
            projects = json.loads(output)
            for project_name in projects.get('projects', []):
                if 'demo' in project_name.lower():
                    self.print_info(f"Deleting CodeBuild project: {project_name}")
                    success, _, error = self.aws_command(f"codebuild delete-project --name {project_name}",
                        check=False
                    )
                    if success:
                        self.print_success(f"Project {project_name} deleted")
                        self.resources_found.append(f"CodeBuild Project: {project_name}")
                    else:
                        self.print_error(f"Failed to delete project {project_name}: {error}")
                        self.cleanup_errors.append(f"CodeBuild {project_name}: {error}")
        except json.JSONDecodeError:
            self.print_warning("Could not parse projects list")

    def cleanup_codeconnections(self):
        """Delete CodeConnections"""
        self.print_info("Cleaning up CodeConnections...")
        
        # List connections
        success, output, _ = self.aws_command("codeconnections list-connections", check=False)
        if not success:
            return
            
        try:
            connections = json.loads(output)
            for connection in connections.get('Connections', []):
                connection_name = connection.get('ConnectionName', '')
                connection_arn = connection.get('ConnectionArn', '')
                if 'demo' in connection_name.lower():
                    self.print_info(f"Deleting connection: {connection_name}")
                    success, _, error = self.aws_command(f"codeconnections delete-connection --connection-arn '{connection_arn}'",
                        check=False
                    )
                    if success:
                        self.print_success(f"Connection {connection_name} deleted")
                        self.resources_found.append(f"Connection: {connection_name}")
                    else:
                        self.print_error(f"Failed to delete connection {connection_name}: {error}")
                        self.cleanup_errors.append(f"Connection {connection_name}: {error}")
        except json.JSONDecodeError:
            self.print_warning("Could not parse connections list")

    def cleanup_codeartifact(self):
        """Delete CodeArtifact resources"""
        self.print_info("Cleaning up CodeArtifact resources...")
        
        # List domains
        success, output, _ = self.aws_command("codeartifact list-domains", check=False)
        if not success:
            return
            
        try:
            domains = json.loads(output)
            for domain in domains.get('domains', []):
                domain_name = domain.get('name', '')
                if 'demo' in domain_name.lower():
                    # List repositories in domain first
                    success, repo_output, _ = self.aws_command(f"codeartifact list-repositories-in-domain --domain {domain_name}",
                        check=False
                    )
                    if success:
                        try:
                            repos = json.loads(repo_output)
                            for repo in repos.get('repositories', []):
                                repo_name = repo.get('name', '')
                                self.print_info(f"Deleting repository: {repo_name}")
                                success, _, error = self.aws_command(f"codeartifact delete-repository --domain {domain_name} --repository {repo_name}",
                                    check=False
                                )
                                if success:
                                    self.print_success(f"Repository {repo_name} deleted")
                                    self.resources_found.append(f"CodeArtifact Repository: {repo_name}")
                                else:
                                    self.print_error(f"Failed to delete repository {repo_name}: {error}")
                        except json.JSONDecodeError:
                            pass
                    
                    # Delete domain
                    self.print_info(f"Deleting domain: {domain_name}")
                    success, _, error = self.aws_command(f"codeartifact delete-domain --domain {domain_name}",
                        check=False
                    )
                    if success:
                        self.print_success(f"Domain {domain_name} deleted")
                        self.resources_found.append(f"CodeArtifact Domain: {domain_name}")
                    else:
                        self.print_error(f"Failed to delete domain {domain_name}: {error}")
                        self.cleanup_errors.append(f"Domain {domain_name}: {error}")
        except json.JSONDecodeError:
            self.print_warning("Could not parse domains list")

    def cleanup_s3_buckets(self):
        """Delete S3 buckets"""
        self.print_info("Cleaning up S3 buckets...")
        
        buckets_to_delete = ['demo-buildspecs', 'demo-artif-bucket']
        
        for bucket_name in buckets_to_delete:
            # Check if bucket exists
            success, _, _ = self.aws_command(f"s3api head-bucket --bucket {bucket_name}",
                check=False
            )
            if not success:
                continue
                
            # Empty bucket first
            self.print_info(f"Emptying bucket: {bucket_name}")
            success, _, _ = self.aws_command(f"s3 rm s3://{bucket_name} --recursive",
                check=False
            )
            
            # Delete bucket
            self.print_info(f"Deleting bucket: {bucket_name}")
            success, _, error = self.aws_command(f"s3 rb s3://{bucket_name}",
                check=False
            )
            if success:
                self.print_success(f"Bucket {bucket_name} deleted")
                self.resources_found.append(f"S3 Bucket: {bucket_name}")
            else:
                self.print_error(f"Failed to delete bucket {bucket_name}: {error}")
                self.cleanup_errors.append(f"S3 {bucket_name}: {error}")

    def cleanup_iam_resources(self):
        """Delete IAM roles and policies"""
        self.print_info("Cleaning up IAM resources...")
        
        # List roles
        success, output, _ = self.aws_command("iam list-roles", check=False)
        if not success:
            return
            
        try:
            roles = json.loads(output)
            for role in roles.get('Roles', []):
                role_name = role.get('RoleName', '')
                if 'demo' in role_name.lower():
                    # Delete attached policies first
                    success, policy_output, _ = self.aws_command(f"iam list-role-policies --role-name {role_name}",
                        check=False
                    )
                    if success:
                        try:
                            policies = json.loads(policy_output)
                            for policy_name in policies.get('PolicyNames', []):
                                self.print_info(f"Deleting policy: {policy_name}")
                                self.aws_command(f"iam delete-role-policy --role-name {role_name} --policy-name {policy_name}",
                                    check=False
                                )
                        except json.JSONDecodeError:
                            pass
                    
                    # Delete role
                    self.print_info(f"Deleting IAM role: {role_name}")
                    success, _, error = self.aws_command(f"iam delete-role --role-name {role_name}",
                        check=False
                    )
                    if success:
                        self.print_success(f"Role {role_name} deleted")
                        self.resources_found.append(f"IAM Role: {role_name}")
                    else:
                        self.print_error(f"Failed to delete role {role_name}: {error}")
                        self.cleanup_errors.append(f"IAM Role {role_name}: {error}")
        except json.JSONDecodeError:
            self.print_warning("Could not parse roles list")

    def cleanup_local_files(self):
        """Clean up generated local files"""
        self.print_info("Cleaning up generated files...")
        
        files_to_remove = [
            'generated_pipeline.json',
            'workshop_config.json',
            'workshop_setup.log'
        ]
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.print_success(f"Removed file: {file_path}")
                    self.resources_found.append(f"File: {file_path}")
                except OSError as e:
                    self.print_error(f"Failed to remove {file_path}: {e}")

    def stop_localstack_container(self):
        """Stop and remove LocalStack container"""
        if self.keep_container:
            self.print_info("Keeping LocalStack container as requested")
            return
            
        self.print_info("Stopping LocalStack container...")
        
        # Stop container
        success, _, _ = self.run_command("docker stop localstack-workshop", check=False)
        if success:
            self.print_success("LocalStack container stopped")
            self.resources_found.append("LocalStack container")
        else:
            self.print_warning("LocalStack container was not running")
        
        # Remove container
        self.run_command("docker rm localstack-workshop", check=False)

    def confirm_cleanup(self) -> bool:
        """Ask user to confirm cleanup"""
        if self.force:
            return True
            
        self.print_warning("This will delete ALL workshop resources!")
        self.print_info("Resources that will be removed:")
        print("   • CodePipeline pipelines")
        print("   • CodeBuild projects") 
        print("   • CodeConnections")
        print("   • CodeArtifact domains and repositories")
        print("   • S3 buckets and contents")
        print("   • IAM roles and policies")
        print("   • Generated configuration files")
        if not self.keep_container:
            print("   • LocalStack container")
        print()
        
        try:
            response = input(f"{Colors.YELLOW}Are you sure? (y/N): {Colors.NC}").strip().lower()
            return response in ['y', 'yes']
        except EOFError:
            # Non-interactive mode - default to yes
            print("Non-interactive mode detected - proceeding with cleanup")
            return True

    def show_summary(self):
        """Show cleanup summary"""
        self.print_header("Cleanup Summary")
        
        if self.resources_found:
            self.print_success(f"Successfully cleaned up {len(self.resources_found)} resources:")
            for resource in self.resources_found:
                print(f"   • {resource}")
        else:
            self.print_info("No resources found to clean up")
            
        if self.cleanup_errors:
            print()
            self.print_error(f"Encountered {len(self.cleanup_errors)} errors:")
            for error in self.cleanup_errors:
                print(f"   • {error}")
                
        print()
        if self.keep_container:
            self.print_info("LocalStack container is still running")
            self.print_info("You can restart the workshop with: python3 setup_workshop.py")
        else:
            self.print_success("Workshop completely cleaned up!")
            self.print_info("To restart: python3 check_environment.py && python3 setup_workshop.py")

    def run_cleanup(self) -> bool:
        """Run the complete cleanup process"""
        self.print_header("LocalStack Workshop Cleanup")
        
        # Check if LocalStack is accessible
        if not self.check_localstack_connection():
            self.print_warning("LocalStack is not accessible - skipping AWS resource cleanup")
            self.cleanup_local_files()
            self.stop_localstack_container()
            self.show_summary()
            return True
        
        # Confirm with user
        if not self.confirm_cleanup():
            self.print_info("Cleanup cancelled")
            return False
            
        try:
            # Clean up AWS resources
            self.cleanup_codepipeline()
            self.cleanup_codebuild()
            self.cleanup_codeconnections()
            self.cleanup_codeartifact()
            self.cleanup_s3_buckets()
            self.cleanup_iam_resources()
            
            # Clean up local files
            self.cleanup_local_files()
            
            # Stop LocalStack container
            self.stop_localstack_container()
            
            self.show_summary()
            return len(self.cleanup_errors) == 0
            
        except KeyboardInterrupt:
            self.print_warning("Cleanup interrupted by user")
            return False
        except Exception as e:
            self.print_error(f"Unexpected error during cleanup: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Clean up LocalStack workshop resources')
    parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation prompt')
    parser.add_argument('--keep-container', '-k', action='store_true', help='Keep LocalStack container running')
    
    args = parser.parse_args()
    
    cleanup = WorkshopCleanup(force=args.force, keep_container=args.keep_container)
    
    try:
        success = cleanup.run_cleanup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Cleanup interrupted{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {e}{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()