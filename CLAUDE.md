# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository is designed for a LocalStack AWS CI/CD services workshop. The project demonstrates how to emulate AWS CI/CD services locally using LocalStack, including:

- **CodeBuild** - Build service for running isolated environments and commands
- **CodePipeline** - CI/CD pipeline orchestration service
- **CodeArtifact** - Package repository management
- **CodeConnections** - Integration with external source repositories (GitHub)
- **CodeDeploy** - Deployment service (potential future addition)

## Architecture

The workshop demonstrates a complete CI/CD pipeline that:
1. Retrieves source code from S3 storage
2. Runs tests using CodeBuild
3. Publishes npm packages to a private CodeArtifact repository
4. Uses S3 for artifact storage between pipeline stages

Key AWS services integrated:
- S3 for BuildSpec storage and pipeline artifacts
- CloudWatch Logs for build logging (when deployed to AWS)

## Essential Commands

### LocalStack Setup
```bash
# Install awslocal wrapper (optional)
pip install awscli-local

# Start LocalStack container (requires CODEPIPELINE_GH_TOKEN env var)
docker run --rm -d -p 4566:4566 -e CODEPIPELINE_GH_TOKEN=<your-token> localstack/localstack

# Verify LocalStack is running
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 sts get-caller-identity
```


### CodeArtifact Operations
```bash
# Create domain and repository
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codeartifact create-domain --domain demo-domain
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codeartifact create-repository --domain demo-domain --repository demo-repo

# List packages in repository
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codeartifact list-packages --domain demo-domain --repository demo-repo

# Configure npm to use CodeArtifact
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codeartifact login --tool npm --domain demo-domain --repository demo-repo
```

### CodeBuild Operations
```bash
# Upload BuildSpecs to S3
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 mb s3://demo-buildspecs
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 cp demo-test.yaml s3://demo-buildspecs
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 cp demo-publish.yaml s3://demo-buildspecs

# Create CodeBuild projects (no IAM roles needed in LocalStack)
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codebuild create-project --name demo-test --source type=CODEPIPELINE,buildspec=arn:aws:s3:::demo-buildspecs/demo-test.yaml --artifacts type=CODEPIPELINE --environment type=LINUX_CONTAINER,image=aws/codebuild/amazonlinux-x86_64-standard:5.0,computeType=BUILD_GENERAL1_SMALL
```

### CodePipeline Operations
```bash
# Create artifact storage bucket
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 s3 mb s3://demo-artif-bucket

# Create pipeline from JSON definition
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codepipeline create-pipeline --pipeline file://demo-pipeline.json

# Monitor pipeline executions
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codepipeline list-pipeline-executions --pipeline-name demo-pipeline
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codepipeline get-pipeline-execution --pipeline-name demo-pipeline --pipeline-execution-id <execution-id>
```

### CodeConnections Setup
```bash
# Create GitHub connection (requires CODEPIPELINE_GH_TOKEN)
AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 codeconnections create-connection --connection-name demo-connection --provider-type GitHub
```

## Key Configuration Files

- **pipeline-template.json** - Pipeline definition template with stages and actions
- **demo-test.yaml** - BuildSpec for running tests (Node.js project)
- **demo-publish.yaml** - BuildSpec for publishing to CodeArtifact

## BuildSpec Specifications

BuildSpecs use YAML format with phases:
- `install` - Runtime versions and system dependencies
- `pre_build` - Authentication and setup commands  
- `build` - Main build/test/publish commands
- `post_build` - Cleanup and reporting (optional)

Common runtime environments:
- `nodejs: 22` for JavaScript/npm projects
- `python: 3.x` for Python projects
- `java: corretto17` for Java/Maven projects

## Development Workflow

1. **Setup LocalStack** with required environment variables
2. **Set up CodeArtifact** domain and repositories
3. **Upload BuildSpecs** to S3 for CodeBuild reference
4. **Create CodeBuild projects** for each pipeline stage
5. **Define pipeline structure** in JSON format
6. **Create and execute pipeline** through CodePipeline
7. **Monitor execution** and access artifacts

## Troubleshooting

- For S3 operations, ensure buckets are created before use: `aws --endpoint-url=http://localhost:4566 s3 mb s3://bucket-name`
- Use `AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 aws --endpoint-url=http://localhost:4566 logs describe-log-groups` to debug CodeBuild issues
- LocalStack uses `000000000000` as default account ID in ARNs
- If `awslocal` commands fail with endpoint errors, use the direct AWS CLI approach with `--endpoint-url=http://localhost:4566`
- No IAM roles required for LocalStack CI/CD services - they work without authentication

## LocalStack Service Versions

- CodeBuild, CodePipeline, CodeConnections: Available from LocalStack v4.5+
- CodeArtifact: Available from LocalStack v4.6+
- Full CI/CD integration requires LocalStack Pro features
- to memorize
- to memorize
- to memorize
- to memorize
- to memorize