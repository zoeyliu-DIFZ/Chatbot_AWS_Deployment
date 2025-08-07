#!/usr/bin/env python3
"""
YAML-based SAM deployment script for AI Chat Assistant
Usage: python deploy.py [environment]
Default environment: prod
"""

import yaml
import subprocess
import sys
import os
from pathlib import Path

def load_config():
    """Load deployment configuration from YAML file"""
    config_file = Path(__file__).parent / "deploy-config.yaml"
    try:
        with open(config_file, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_file}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing YAML configuration: {e}")
        sys.exit(1)

def check_prerequisites():
    """Check if required tools are installed"""
    # Check SAM CLI
    try:
        subprocess.run(['sam', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ SAM CLI is not installed. Please install it first:")
        print("   brew install aws-sam-cli")
        sys.exit(1)
    
    # Check AWS CLI configuration
    try:
        subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ AWS CLI is not configured. Please run 'aws configure' first.")
        sys.exit(1)

def deploy(environment='prod'):
    """Deploy the application using SAM"""
    config = load_config()
    
    if environment not in config['environments']:
        print(f"❌ Environment '{environment}' not found in configuration")
        print(f"Available environments: {list(config['environments'].keys())}")
        sys.exit(1)
    
    env_config = config['environments'][environment]
    
    print(f"🚀 Deploying {config['name']} to {environment} environment...")
    
    # Build
    print("📦 Building SAM application...")
    try:
        subprocess.run(['sam', 'build'], check=True)
    except subprocess.CalledProcessError:
        print("❌ Build failed")
        sys.exit(1)
    
    # Deploy
    print("🚀 Deploying to AWS...")
    deploy_cmd = [
        'sam', 'deploy',
        '--config-env', environment
    ]
    
    try:
        subprocess.run(deploy_cmd, check=True)
    except subprocess.CalledProcessError:
        print("❌ Deployment failed")
        sys.exit(1)
    
    print("✅ Deployment completed successfully!")
    
    # Show stack outputs
    print("\n📋 Stack outputs:")
    try:
        subprocess.run([
            'aws', 'cloudformation', 'describe-stacks',
            '--stack-name', env_config['stack_name'],
            '--query', 'Stacks[0].Outputs[*].[OutputKey,OutputValue]',
            '--output', 'table'
        ], check=True)
    except subprocess.CalledProcessError:
        print("⚠️  Could not retrieve stack outputs")

def main():
    """Main function"""
    environment = sys.argv[1] if len(sys.argv) > 1 else 'prod'
    
    check_prerequisites()
    deploy(environment)

if __name__ == '__main__':
    main() 