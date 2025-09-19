#!/bin/bash

# LocalStack CI/CD Workshop Setup using awslocal (the working approach!)

set -e

# Configure environment for awslocal
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test  
export AWS_DEFAULT_REGION=us-east-1

echo "🚀 Starting LocalStack CI/CD Workshop..."

# Start LocalStack if not running
if ! docker ps | grep -q localstack; then
    echo "📦 Starting LocalStack..."
    docker compose up -d localstack
    sleep 10
fi

echo "🧹 Cleaning up any existing resources..."

# Clean up existing resources to ensure fresh start
aws --endpoint-url=http://localhost:4566 codepipeline delete-pipeline --name demo-pipeline 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 codebuild delete-project --name demo-test 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 codebuild delete-project --name demo-publish 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 codeartifact delete-repository --domain demo-domain --repository demo-repo 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 codeartifact delete-domain --domain demo-domain 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 iam delete-role-policy --role-name demo-role --policy-name demo-policy 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 iam delete-role --role-name demo-role 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 s3 rm s3://demo-source-bucket --recursive 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 s3 rm s3://demo-buildspecs --recursive 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 s3 rm s3://demo-artif-bucket --recursive 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 s3 rb s3://demo-source-bucket 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 s3 rb s3://demo-buildspecs 2>/dev/null || true
aws --endpoint-url=http://localhost:4566 s3 rb s3://demo-artif-bucket 2>/dev/null || true

echo "🎯 Setting up workshop resources..."

# Create simple IAM role (LocalStack needs this for proper pipeline execution)
echo "🔐 Creating IAM role..."
aws --endpoint-url=http://localhost:4566 iam create-role --role-name demo-role --assume-role-policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": ["codebuild.amazonaws.com", "codepipeline.amazonaws.com"]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

aws --endpoint-url=http://localhost:4566 iam put-role-policy --role-name demo-role --policy-name demo-policy --policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}'

ROLE_ARN=$(aws --endpoint-url=http://localhost:4566 iam get-role --role-name demo-role --query Role.Arn --output text)

# Create CodeArtifact repository  
echo "📚 Creating CodeArtifact repository..."
aws --endpoint-url=http://localhost:4566 codeartifact create-domain --domain demo-domain
aws --endpoint-url=http://localhost:4566 codeartifact create-repository --domain demo-domain --repository demo-repo

# Create S3 buckets
echo "🗂️ Creating S3 buckets..."
aws --endpoint-url=http://localhost:4566 s3 mb s3://demo-source-bucket
aws --endpoint-url=http://localhost:4566 s3 mb s3://demo-buildspecs
aws --endpoint-url=http://localhost:4566 s3 mb s3://demo-artif-bucket

# Enable versioning on source bucket (required for CodePipeline)
echo "🔄 Enabling S3 bucket versioning..."
aws --endpoint-url=http://localhost:4566 s3api put-bucket-versioning --bucket demo-source-bucket --versioning-configuration Status=Enabled

# Upload source code
echo "📦 Uploading sample app..."
cd sample-app
zip -r ../source-code.zip . -x "*.git*"
cd ..
aws --endpoint-url=http://localhost:4566 s3 cp source-code.zip s3://demo-source-bucket/
aws --endpoint-url=http://localhost:4566 s3 cp sample-app/demo.html s3://demo-source-bucket/

# Upload BuildSpecs (using alternative approach to bypass LocalStack bug)
echo "⚙️ Uploading BuildSpecs..."
# Try direct upload with retries
for file in demo-test.yaml demo-publish.yaml; do
    echo "Uploading $file..."
    for i in {1..3}; do
        if aws --endpoint-url=http://localhost:4566 s3 cp templates/$file s3://demo-buildspecs/ 2>/dev/null; then
            echo "  ✅ $file uploaded successfully"
            break
        else
            echo "  ⚠️  Attempt $i failed, retrying..."
            sleep 2
        fi
    done
done

# Create CodeBuild projects using awslocal (the working approach!)
echo "🔨 Creating CodeBuild projects..."

# Fallback: If S3 uploads failed, use inline buildspec
TEST_BUILDSPEC="version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: 22
  pre_build:
    commands:
      - echo Installing dependencies...
      - npm install
  build:
    commands:
      - echo Running tests...
      - npm test"

PUBLISH_BUILDSPEC="version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: 22
  pre_build:
    commands:
      - echo Configuring CodeArtifact...
      - CODEARTIFACT_AUTH_TOKEN=\$(aws codeartifact get-authorization-token --domain demo-domain --query authorizationToken --output text)
      - npm config set registry https://demo-domain-000000000000.d.codeartifact.us-east-1.amazonaws.com/npm/demo-repo/
      - npm config set //demo-domain-000000000000.d.codeartifact.us-east-1.amazonaws.com/npm/demo-repo/:_authToken \$CODEARTIFACT_AUTH_TOKEN
      - npm install
  build:
    commands:
      - echo Publishing package...
      - npm publish"

# Try S3-based buildspec first, fallback to inline
if aws --endpoint-url=http://localhost:4566 s3 ls s3://demo-buildspecs/demo-test.yaml >/dev/null 2>&1; then
    echo "Using S3-based buildspecs..."
    aws --endpoint-url=http://localhost:4566 codebuild create-project --name demo-test \
        --source type=CODEPIPELINE,buildspec="arn:aws:s3:::demo-buildspecs/demo-test.yaml" \
        --artifacts type=CODEPIPELINE \
        --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL \
        --service-role "${ROLE_ARN}"

    aws --endpoint-url=http://localhost:4566 codebuild create-project --name demo-publish \
        --source type=CODEPIPELINE,buildspec="arn:aws:s3:::demo-buildspecs/demo-publish.yaml" \
        --artifacts type=CODEPIPELINE \
        --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL \
        --service-role "${ROLE_ARN}"
else
    echo "⚠️  S3 buildspecs not available, using inline buildspecs..."
    aws --endpoint-url=http://localhost:4566 codebuild create-project --name demo-test \
        --source type=CODEPIPELINE,buildspec="${TEST_BUILDSPEC}" \
        --artifacts type=CODEPIPELINE \
        --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL \
        --service-role "${ROLE_ARN}"

    aws --endpoint-url=http://localhost:4566 codebuild create-project --name demo-publish \
        --source type=CODEPIPELINE,buildspec="${PUBLISH_BUILDSPEC}" \
        --artifacts type=CODEPIPELINE \
        --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL \
        --service-role "${ROLE_ARN}"
fi

# Create pipeline using proper format and role
echo "📋 Creating pipeline..."
cat > simple-pipeline.json << 'EOF'
{
  "pipelineType": "V1", 
  "name": "demo-pipeline",
  "roleArn": "arn:aws:iam::000000000000:role/demo-role",
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
          "outputArtifacts": [{"name": "source-code"}],
          "configuration": {
            "S3Bucket": "demo-source-bucket",
            "S3ObjectKey": "source-code.zip"
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
          "inputArtifacts": [{"name": "source-code"}],
          "configuration": {"ProjectName": "demo-test"}
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
          "inputArtifacts": [{"name": "source-code"}],
          "configuration": {"ProjectName": "demo-publish"}
        }
      ]
    }
  ]
}
EOF

# Create the pipeline using awslocal
aws --endpoint-url=http://localhost:4566 codepipeline create-pipeline --pipeline file://simple-pipeline.json

# Start the pipeline and wait for completion (like the working reference!)
echo "▶️ Starting pipeline execution and monitoring..."
aws --endpoint-url=http://localhost:4566 codepipeline start-pipeline-execution --name demo-pipeline

# Wait for pipeline completion with polling
echo "⏳ Waiting for pipeline to complete..."
status=""
timeout=300  # 5 minutes timeout
elapsed=0
while [[ ! "$status" =~ (Succeeded|Failed) ]] && [ $elapsed -lt $timeout ]; do
    status=$(aws --endpoint-url=http://localhost:4566 codepipeline list-pipeline-executions --pipeline-name demo-pipeline --output text --query 'pipelineExecutionSummaries[0].status' 2>/dev/null || echo "")
    if [[ "$status" =~ (Succeeded|Failed) ]]; then
        break
    fi
    echo "  Status: ${status:-Pending...}"
    sleep 10
    elapsed=$((elapsed + 10))
done

if [[ "$status" == "Succeeded" ]]; then
    echo "✅ Pipeline completed successfully!"
    echo ""
    echo "📦 Check published packages:"
    aws --endpoint-url=http://localhost:4566 codeartifact list-packages --domain demo-domain --repository demo-repo
    echo ""
elif [[ "$status" == "Failed" ]]; then
    echo "❌ Pipeline failed. Check the logs for details."
    echo ""
else
    echo "⏰ Pipeline is still running or timed out."
    echo ""
fi

echo "🎉 Workshop setup complete!"
echo ""
echo "📊 Check pipeline status:"
echo "   aws --endpoint-url=http://localhost:4566 codepipeline list-pipeline-executions --pipeline-name demo-pipeline"
echo ""
echo "📦 Check published packages:"
echo "   aws --endpoint-url=http://localhost:4566 codeartifact list-packages --domain demo-domain --repository demo-repo" 
echo ""
echo "🌐 View demo app:"
echo "   open http://localhost:4566/demo-source-bucket/demo.html"
echo ""