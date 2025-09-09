#!/bin/bash

# Setup AWS profile for LocalStack workshop
# This script configures AWS CLI to work with LocalStack

echo "🔧 Setting up AWS CLI profile for LocalStack..."

# Create ~/.aws directory if it doesn't exist
mkdir -p ~/.aws

# Backup existing files if they exist
if [ -f ~/.aws/config ]; then
    echo "📋 Backing up existing AWS config to ~/.aws/config.backup"
    cp ~/.aws/config ~/.aws/config.backup
fi

if [ -f ~/.aws/credentials ]; then
    echo "📋 Backing up existing AWS credentials to ~/.aws/credentials.backup"
    cp ~/.aws/credentials ~/.aws/credentials.backup
fi

# Copy LocalStack configuration files
echo "📁 Installing LocalStack AWS configuration..."

# Check if files already have localstack profile
if grep -q "\[profile localstack\]" ~/.aws/config 2>/dev/null; then
    echo "⚠️  LocalStack profile already exists in ~/.aws/config"
else
    echo "" >> ~/.aws/config
    cat aws-config >> ~/.aws/config
    echo "✅ Added LocalStack profile to ~/.aws/config"
fi

if grep -q "\[localstack\]" ~/.aws/credentials 2>/dev/null; then
    echo "⚠️  LocalStack credentials already exist in ~/.aws/credentials"
else
    echo "" >> ~/.aws/credentials
    cat aws-credentials >> ~/.aws/credentials
    echo "✅ Added LocalStack credentials to ~/.aws/credentials"
fi

echo ""
echo "🎉 Setup complete! You can now use:"
echo ""
echo "   aws --profile localstack s3 ls"
echo "   aws --profile localstack sts get-caller-identity"
echo "   aws --profile localstack codepipeline list-pipelines"
echo ""
echo "💡 Or set as default:"
echo "   export AWS_PROFILE=localstack"
echo ""