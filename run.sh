#!/bin/bash

# Super Simple LocalStack CI/CD Workshop Setup
# No IAM, no roles, no security - just the basics!

set -e

echo "🚀 Starting LocalStack CI/CD Workshop..."

# Start LocalStack if not running
if ! docker ps | grep -q localstack; then
    echo "📦 Starting LocalStack..."
    docker compose up -d localstack
    sleep 10
fi

echo "🎯 Setting up workshop resources..."

# Create CodeArtifact repository  
echo "📚 Creating CodeArtifact repository..."
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codeartifact create-domain --domain demo-domain || true
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codeartifact create-repository --domain demo-domain --repository demo-repo || true

# Create S3 buckets
echo "🗂️ Creating S3 buckets..."
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 mb s3://demo-source-bucket || true
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 mb s3://demo-buildspecs || true
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 mb s3://demo-artif-bucket || true

# Upload source code
echo "📦 Uploading sample app..."
cd sample-app
zip -r ../source-code.zip . -x "*.git*"
cd ..
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 cp source-code.zip s3://demo-source-bucket/
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 cp sample-app/demo.html s3://demo-source-bucket/

# Upload BuildSpecs
echo "⚙️ Uploading BuildSpecs..."
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 cp templates/demo-test.yaml s3://demo-buildspecs/
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 cp templates/demo-publish.yaml s3://demo-buildspecs/

# Create CodeBuild projects (without service roles)
echo "🔨 Creating CodeBuild projects..."
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codebuild create-project --name demo-test \
    --source type=CODEPIPELINE,buildspec=arn:aws:s3:::demo-buildspecs/demo-test.yaml \
    --artifacts type=CODEPIPELINE \
    --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL \
    --service-role arn:aws:iam::000000000000:role/dummy || echo "demo-test exists"

AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codebuild create-project --name demo-publish \
    --source type=CODEPIPELINE,buildspec=arn:aws:s3:::demo-buildspecs/demo-publish.yaml \
    --artifacts type=CODEPIPELINE \
    --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL \
    --service-role arn:aws:iam::000000000000:role/dummy || echo "demo-publish exists"

# Create simple pipeline definition without roles
echo "📋 Creating pipeline..."
cat > simple-pipeline.json << 'EOF'
{
  "pipeline": {
    "pipelineType": "V1", 
    "name": "demo-pipeline",
    "roleArn": "arn:aws:iam::000000000000:role/dummy",
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
}
EOF

# Create the pipeline
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codepipeline create-pipeline --cli-input-json file://simple-pipeline.json || echo "Pipeline might already exist"

# Start the pipeline
echo "▶️ Starting pipeline execution..."
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codepipeline start-pipeline-execution --name demo-pipeline || true

echo ""
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