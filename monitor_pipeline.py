#!/usr/bin/env python3
"""
Simple pipeline monitoring script for conference demos
"""

import json
import subprocess
import time
import sys
from datetime import datetime
from pathlib import Path

# Load .env file if it exists
import os
try:
    from dotenv import load_dotenv
    if Path('.env').exists():
        load_dotenv('.env')
        print(f"✅ Loaded environment variables from .env file")
except ImportError:
    # dotenv not installed, just use regular environment variables
    pass

# Ensure LOCALSTACK_AUTH_TOKEN is available
if not os.environ.get('LOCALSTACK_AUTH_TOKEN'):
    if Path('.env').exists():
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('LOCALSTACK_AUTH_TOKEN'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
                    break

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
        import os
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10, env=os.environ)
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, ""

def print_status(message, color=Colors.NC, emoji=""):
    print(f"{color}{emoji} {message}{Colors.NC}")

def get_pipeline_status():
    """Get current pipeline execution status"""
    success, output = run_command("AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codepipeline list-pipeline-executions --pipeline-name demo-pipeline")
    if not success:
        return None
        
    try:
        executions = json.loads(output)
        if executions.get('pipelineExecutionSummaries'):
            latest = executions['pipelineExecutionSummaries'][0]
            return {
                'id': latest['pipelineExecutionId'],
                'status': latest['status'],
                'start_time': latest.get('startTime', ''),
                'last_update': latest.get('lastUpdateTime', '')
            }
    except json.JSONDecodeError:
        pass
    return None

def get_stage_details(execution_id):
    """Get detailed stage information"""
    success, output = run_command(f"AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codepipeline get-pipeline-execution --pipeline-name demo-pipeline --pipeline-execution-id {execution_id}")
    if not success:
        return []
        
    try:
        execution = json.loads(output)
        stages = []
        
        # Get stage states
        success, stage_output = run_command(f"AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codepipeline list-action-executions --pipeline-name demo-pipeline --filter pipelineExecutionId={execution_id}")
        if success:
            try:
                actions = json.loads(stage_output)
                stage_map = {}
                for action in actions.get('actionExecutionDetails', []):
                    stage_name = action['stageName']
                    action_name = action['actionName']
                    status = action['status']
                    if stage_name not in stage_map:
                        stage_map[stage_name] = []
                    stage_map[stage_name].append({'name': action_name, 'status': status})
                
                for stage_name, actions in stage_map.items():
                    stages.append({'name': stage_name, 'actions': actions})
            except json.JSONDecodeError:
                pass
                
        return stages
    except json.JSONDecodeError:
        return []

def display_pipeline_status():
    """Display current pipeline status"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}📊 Pipeline Status{Colors.NC}")
    print("=" * 50)
    
    status = get_pipeline_status()
    if not status:
        print_status("No pipeline executions found", Colors.YELLOW, "⚠️")
        return
        
    # Status emoji mapping
    status_emoji = {
        'InProgress': '🔄',
        'Succeeded': '✅', 
        'Failed': '❌',
        'Cancelled': '⚪',
        'Superseded': '⏭️'
    }
    
    emoji = status_emoji.get(status['status'], '❓')
    color = Colors.GREEN if status['status'] == 'Succeeded' else Colors.YELLOW if status['status'] == 'InProgress' else Colors.RED
    
    print_status(f"Execution: {status['id'][:8]}...", Colors.BLUE, "🆔")
    print_status(f"Status: {status['status']}", color, emoji)
    
    # Show stage details
    stages = get_stage_details(status['id'])
    if stages:
        print(f"\n{Colors.BLUE}📋 Stages:{Colors.NC}")
        for i, stage in enumerate(stages, 1):
            stage_status = "COMPLETED" if all(a['status'] == 'Succeeded' for a in stage['actions']) else "IN_PROGRESS" if any(a['status'] == 'InProgress' for a in stage['actions']) else "PENDING"
            
            if stage_status == "COMPLETED":
                print_status(f"{i}. {stage['name']}: ✅ COMPLETED", Colors.GREEN)
            elif stage_status == "IN_PROGRESS":  
                print_status(f"{i}. {stage['name']}: 🔄 IN PROGRESS", Colors.YELLOW)
            else:
                print_status(f"{i}. {stage['name']}: ⏳ PENDING", Colors.BLUE)
                
            for action in stage['actions']:
                action_emoji = status_emoji.get(action['status'], '⏳')
                action_color = Colors.GREEN if action['status'] == 'Succeeded' else Colors.YELLOW if action['status'] == 'InProgress' else Colors.BLUE
                print(f"   └─ {action['name']}: {action_color}{action_emoji} {action['status']}{Colors.NC}")
    
    return status['status']

def monitor_pipeline():
    """Monitor pipeline execution with live updates"""
    print(f"{Colors.BLUE}{Colors.BOLD}🎬 LocalStack CI/CD Pipeline Monitor{Colors.NC}")
    print("Press Ctrl+C to stop monitoring")
    print("=" * 60)
    
    try:
        while True:
            current_status = display_pipeline_status()
            
            if current_status in ['Succeeded', 'Failed', 'Cancelled']:
                print(f"\n{Colors.BOLD}Pipeline execution completed: {current_status}{Colors.NC}")
                
                if current_status == 'Succeeded':
                    print_status("🎉 Success! Check your published package:", Colors.GREEN)
                    print("   python3 check_packages.py")
                elif current_status == 'Failed':
                    print_status("Check logs for details:", Colors.RED, "🔍")
                    print("   python3 view_logs.py")
                break
                
            print(f"\n{Colors.BLUE}Refreshing in 5 seconds...{Colors.NC}")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Monitoring stopped by user{Colors.NC}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor LocalStack CI/CD Pipeline')
    parser.add_argument('--status-only', action='store_true', help='Show status once and exit')
    
    args = parser.parse_args()
    
    # Check LocalStack connection
    success, output = run_command("awslocal sts get-caller-identity")
    if not success:
        print_status("LocalStack not accessible. Is it running?", Colors.RED, "❌")
        print("Start with: python3 setup_workshop.py")
        sys.exit(1)
    
    if args.status_only:
        display_pipeline_status()
    else:
        monitor_pipeline()

if __name__ == "__main__":
    main()