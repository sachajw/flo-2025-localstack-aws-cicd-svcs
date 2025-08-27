# LocalStack AWS CI/CD Services Workshop

**Perfect for conference talks, workshops, and learning!** 

A hands-on demonstration of AWS CI/CD services running locally in a LocalStack container on your machine. Build complete pipelines with zero AWS costs - everything runs locally!

## 🚀 Super Quick Start (5 minutes)

**For conference attendees - just fork this repo and:**

```bash
# 1. Check prerequisites  
python3 check_environment.py

# 2. Set GitHub token
export CODEPIPELINE_GH_TOKEN="your_github_token"

# 3. Run everything!
python3 setup_workshop.py

# 4. Watch the magic
python3 monitor_pipeline.py
```

**That's it! See [QUICK_START.md](QUICK_START.md) for details.**

## Overview

This workshop explores LocalStack's CI/CD service emulation capabilities, allowing fully local development and testing of pipelines including:

- **CodeBuild** jobs for building and testing
- **CodePipeline** executions for orchestration  
- **CodeArtifact** repositories for package management
- **CodeConnections** for GitHub integration

## Workshop Scenario

We'll build an end-to-end pipeline for the Lodash JavaScript library that:

1. 🔄 **Retrieves source code** from GitHub via CodeConnections
2. 🧪 **Runs the test suite** using CodeBuild
3. 📦 **Publishes the npm package** to a private CodeArtifact repository

![Pipeline Architecture](https://via.placeholder.com/800x300/4CAF50/FFFFFF?text=GitHub+%E2%86%92+CodePipeline+%E2%86%92+CodeBuild+%E2%86%92+CodeArtifact)

## Prerequisites

- **Docker** installed and running (Docker Desktop recommended)
- **Python 3.8+** with pip
- **GitHub Personal Access Token** with repo permissions ([Get one here](https://github.com/settings/tokens))
- **Internet connection** (for initial LocalStack container download)
- **8GB+ RAM** recommended (LocalStack can be resource intensive)

**Note:** Node.js is NOT required - it runs inside the LocalStack container

## Alternative: Use Task Runner (Optional)

For even simpler commands:

```bash
# Install Task runner (one-time setup)
python3 install-task.py

# Then use simple commands
task start    # Complete setup and demo
task monitor  # Watch pipeline
task cleanup  # Clean everything
```

## Quick Start

### 1. Setup LocalStack

```bash
# Install awslocal wrapper
pip install awscli-local

# Set your GitHub token
export CODEPIPELINE_GH_TOKEN="your_github_token_here"

# Start LocalStack container
docker run --rm -d -p 4566:4566 \
  -e CODEPIPELINE_GH_TOKEN=$CODEPIPELINE_GH_TOKEN \
  localstack/localstack

# Verify LocalStack is running
awslocal sts get-caller-identity
```

### 2. Run the Workshop

Execute the setup script to create all resources:

```bash
./setup-workshop.sh
```

Or follow the step-by-step guide below.

## Step-by-Step Guide

### Step 1: Configure IAM Permissions

Create the required IAM role and policy:

```bash
# Create trust policy for services
cat > role.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "codebuild.amazonaws.com",
          "codepipeline.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create permissions policy
cat > policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "sts:GetServiceBearerToken",
        "codebuild:BatchGetBuilds",
        "codebuild:StartBuild",
        "codestar-connections:UseConnection",
        "codeconnections:UseConnection",
        "codeartifact:GetAuthorizationToken",
        "codeartifact:GetRepositoryEndpoint",
        "codeartifact:PublishPackageVersion",
        "logs:CreateLogStream",
        "logs:CreateLogGroup",
        "logs:PutLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Create role and attach policy
awslocal iam create-role --role-name demo-role --assume-role-policy-document file://role.json
awslocal iam put-role-policy --role-name demo-role --policy-name demo-policy --policy-document file://policy.json

export ROLE_ARN="arn:aws:iam::000000000000:role/demo-role"
```

### Step 2: Setup CodeArtifact Repository

```bash
# Create domain and repository for npm packages
awslocal codeartifact create-domain --domain demo-domain
awslocal codeartifact create-repository --domain demo-domain --repository demo-repo
```

### Step 3: Configure GitHub Connection

```bash
# Create connection to GitHub (token already set via environment)
awslocal codeconnections create-connection \
    --connection-name demo-connection \
    --provider-type GitHub
```

### Step 4: Create BuildSpec Files

Create the test BuildSpec:

```bash
cat > demo-test.yaml << EOF
version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: 22
  pre_build:
    commands:
      - npm ci
  build:
    commands:
      - npm test
EOF
```

Create the publish BuildSpec:

```bash
cat > demo-publish.yaml << EOF
version: 0.2
phases:
  install:
    runtime-versions:
      nodejs: 22
  pre_build:
    commands:
      - yum install -y jq
      - aws codeartifact login --tool npm --domain demo-domain --repository demo-repo
  build:
    commands:
      - jq -r '.private |= false' package.json > package2.json
      - jq -r '.name |= "my-lodash-fork"' package2.json > package.json
      - npm publish
EOF
```

### Step 5: Upload BuildSpecs and Create CodeBuild Projects

```bash
# Upload BuildSpecs to S3
awslocal s3 mb s3://demo-buildspecs
awslocal s3 cp demo-test.yaml s3://demo-buildspecs
awslocal s3 cp demo-publish.yaml s3://demo-buildspecs

# Create CodeBuild projects
awslocal codebuild create-project --name demo-test \
    --source type=CODEPIPELINE,buildspec=arn:aws:s3:::demo-buildspecs/demo-test.yaml \
    --artifacts type=CODEPIPELINE \
    --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL \
    --service-role ${ROLE_ARN}

awslocal codebuild create-project --name demo-publish \
    --source type=CODEPIPELINE,buildspec=arn:aws:s3:::demo-buildspecs/demo-publish.yaml \
    --artifacts type=CODEPIPELINE \
    --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL \
    --service-role ${ROLE_ARN}
```

### Step 6: Create the Pipeline

```bash
# Create artifact storage bucket
awslocal s3 mb s3://demo-artif-bucket

# Get connection ARN
CONNECTION_ARN=$(awslocal codeconnections list-connections --query 'Connections[0].ConnectionArn' --output text)

# Create pipeline definition
cat > demo-pipeline.json << EOF
{
  "pipelineType": "V1",
  "name": "demo-pipeline",
  "roleArn": "${ROLE_ARN}",
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
            "provider": "CodeStarSourceConnection",
            "version": "1"
          },
          "outputArtifacts": [
            {
              "name": "source-code"
            }
          ],
          "configuration": {
            "ConnectionArn": "${CONNECTION_ARN}",
            "FullRepositoryId": "lodash/lodash",
            "BranchName": "4.17.21"
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
EOF

# Create the pipeline
awslocal codepipeline create-pipeline --pipeline file://demo-pipeline.json
```

### Step 7: Monitor Pipeline Execution

```bash
# List pipeline executions
awslocal codepipeline list-pipeline-executions --pipeline-name demo-pipeline

# Get execution details
awslocal codepipeline get-pipeline-execution \
    --pipeline-name demo-pipeline \
    --pipeline-execution-id <execution-id>
```

### Step 8: Verify Package Publication

```bash
# List packages in CodeArtifact
awslocal codeartifact list-packages --domain demo-domain --repository demo-repo

# Configure npm to use local repository
awslocal codeartifact login --tool npm --domain demo-domain --repository demo-repo

# Download the published package
npm pack my-lodash-fork
```

## Workshop Outcomes

After completing this workshop, you will have:

✅ **Local CI/CD Pipeline** running entirely on LocalStack  
✅ **GitHub Integration** via CodeConnections  
✅ **Automated Testing** using CodeBuild  
✅ **Package Publishing** to private CodeArtifact repository  
✅ **Pipeline Orchestration** with CodePipeline  

## Extended Exercises

1. **Add Parallel Testing**: Modify the pipeline to run multiple test jobs in parallel
2. **Docker Integration**: Extend the pipeline to build Docker images and push to ECR
3. **Multi-Environment**: Create separate pipelines for dev/staging/prod environments
4. **Notification Integration**: Add SNS notifications for pipeline status updates

## Troubleshooting

### Common Issues

**Pipeline fails with authentication error:**
```bash
# Verify GitHub token is set correctly
echo $CODEPIPELINE_GH_TOKEN
```

**CodeBuild job fails:**
```bash
# Check build logs
awslocal logs describe-log-groups
awslocal logs describe-log-streams --log-group-name /aws/codebuild/demo-test
```

**npm package not found:**
```bash
# Verify CodeArtifact configuration
awslocal codeartifact describe-repository --domain demo-domain --repository demo-repo
```

### Cleanup

```bash
# Stop LocalStack container
docker stop $(docker ps -q --filter ancestor=localstack/localstack)

# Remove created files
rm -f role.json policy.json demo-*.yaml demo-pipeline.json
```

## Resources

- [LocalStack Documentation](https://docs.localstack.cloud/)
- [AWS CodePipeline User Guide](https://docs.aws.amazon.com/codepipeline/)
- [AWS CodeBuild User Guide](https://docs.aws.amazon.com/codebuild/)
- [AWS CodeArtifact User Guide](https://docs.aws.amazon.com/codeartifact/)

## License

This workshop is provided under the MIT License. See LICENSE file for details.