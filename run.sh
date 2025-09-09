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
}' || true

aws --endpoint-url=http://localhost:4566 iam put-role-policy --role-name demo-role --policy-name demo-policy --policy-document '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}' || true

ROLE_ARN=$(aws --endpoint-url=http://localhost:4566 iam get-role --role-name demo-role --query Role.Arn --output text)

# Create CodeArtifact repository  
echo "📚 Creating CodeArtifact repository..."
aws --endpoint-url=http://localhost:4566 codeartifact create-domain --domain demo-domain || true
aws --endpoint-url=http://localhost:4566 codeartifact create-repository --domain demo-domain --repository demo-repo || true

# Create S3 buckets
echo "🗂️ Creating S3 buckets..."
aws --endpoint-url=http://localhost:4566 s3 mb s3://demo-source-bucket || true
aws --endpoint-url=http://localhost:4566 s3 mb s3://demo-buildspecs || true
aws --endpoint-url=http://localhost:4566 s3 mb s3://demo-artif-bucket || true

# Upload source code
echo "📦 Uploading sample app..."
cd sample-app
zip -r ../source-code.zip . -x "*.git*"
cd ..
aws --endpoint-url=http://localhost:4566 s3 cp source-code.zip s3://demo-source-bucket/
aws --endpoint-url=http://localhost:4566 s3 cp sample-app/demo.html s3://demo-source-bucket/

# Upload BuildSpecs
echo "⚙️ Uploading BuildSpecs..."
aws --endpoint-url=http://localhost:4566 s3 cp templates/demo-test.yaml s3://demo-buildspecs/
aws --endpoint-url=http://localhost:4566 s3 cp templates/demo-publish.yaml s3://demo-buildspecs/

# Create CodeBuild projects using awslocal (the working approach!)
echo "🔨 Creating CodeBuild projects..."
aws --endpoint-url=http://localhost:4566 codebuild create-project --name demo-test \
    --source type=CODEPIPELINE,buildspec=arn:aws:s3:::demo-buildspecs/demo-test.yaml \
    --artifacts type=CODEPIPELINE \
    --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL \
    --service-role ${ROLE_ARN} || echo "demo-test exists"

aws --endpoint-url=http://localhost:4566 codebuild create-project --name demo-publish \
    --source type=CODEPIPELINE,buildspec=arn:aws:s3:::demo-buildspecs/demo-publish.yaml \
    --artifacts type=CODEPIPELINE \
    --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL \
    --service-role ${ROLE_ARN} || echo "demo-publish exists"

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
aws --endpoint-url=http://localhost:4566 codepipeline create-pipeline --pipeline file://simple-pipeline.json || echo "Pipeline might already exist"

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