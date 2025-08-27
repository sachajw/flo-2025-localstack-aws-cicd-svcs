# Build Locally Deploy Globally - LocalStack AWS CI/CD Services Workshop

**Perfect for conference talks, workshops, and learning!**

A hands-on demonstration of AWS CI/CD services running locally in a LocalStack container on your machine. Build complete pipelines with zero AWS costs - everything runs locally!

## 🚀 Super Quick Start (3 minutes)

**For conference attendees - just fork this repo and:**

```bash
# 1. Get LocalStack Pro API key (14-day free trial)
export LOCALSTACK_AUTH_TOKEN="your_api_key"

# 2. Install Task runner (one-time)
python3 install-task.py

# 3. Run complete demo!
task demo
```

**That's it! No GitHub tokens, no internet dependencies after setup, purely local!**

### Alternative: Python Commands (if Task fails)

```bash
python3 setup_workshop.py       # Setup everything  
python3 monitor_pipeline.py     # Watch pipeline
python3 check_packages.py       # View results
```

## Overview

This workshop demonstrates LocalStack's CI/CD service emulation capabilities with a complete Node.js application pipeline:

- **S3** - Local source code storage
- **CodeBuild** - Automated testing and building
- **CodePipeline** - Pipeline orchestration
- **CodeArtifact** - Private package repository

## Workshop Scenario

We build an end-to-end pipeline for our included Node.js demo app that:

1. 🔄 **Retrieves source code** from local S3 storage  
2. 🧪 **Runs the test suite** using CodeBuild
3. 📦 **Publishes the npm package** to a private CodeArtifact repository

![Pipeline Architecture](https://via.placeholder.com/800x300/4CAF50/FFFFFF?text=S3+%E2%86%92+CodePipeline+%E2%86%92+CodeBuild+%E2%86%92+CodeArtifact)

## Prerequisites

- **Docker** installed and running (Docker Desktop recommended)
- **Python 3.8+** with pip
- **LocalStack Pro license** (required for CodePipeline, CodeArtifact, CodeBuild)
- **Internet connection** (for initial LocalStack container download only)
- **8GB+ RAM** recommended (LocalStack can be resource intensive)

**Note:** This workshop uses LocalStack Pro features (CodePipeline, CodeArtifact, CodeBuild). LocalStack Pro offers a **14-day free trial** - perfect for workshops and learning!

**No GitHub tokens or Node.js required - everything runs locally!**

## Task Commands (Recommended)

Once you have Task installed, everything becomes simple:

```bash
task demo      # Complete conference demo (does everything!)
task check     # Check prerequisites only
task setup     # Setup workshop only  
task monitor   # Watch pipeline execution
task packages  # Check published packages
task cleanup   # Clean everything up
task help      # Show all available commands
```

## What This Demo Shows

After running the workshop, you'll have experienced:

✅ **Local CI/CD Pipeline** running entirely on LocalStack Pro  
✅ **Automated Testing** using CodeBuild with our sample Node.js app  
✅ **Package Publishing** to private CodeArtifact repository  
✅ **Pipeline Orchestration** with CodePipeline  
✅ **Zero AWS Costs** - everything runs in your LocalStack container  

## Sample Application

The workshop includes a complete Node.js demo app (`sample-app/`) with:

- **Utility functions** - Math, date, string operations
- **Comprehensive tests** - 11 test cases covering all functionality  
- **Package.json** - Ready for npm publishing
- **Professional structure** - Follows Node.js best practices

You can test the app locally:

```bash
cd sample-app
node test.js    # Run tests
node index.js   # Run demo
```

## Workshop Files Structure

```
├── README.md                    # This file
├── QUICK_START.md              # 2-minute setup guide
├── Taskfile.yml                # Task runner commands
├── setup_workshop.py           # Main setup script
├── check_environment.py        # Prerequisites checker
├── monitor_pipeline.py         # Pipeline monitoring
├── check_packages.py           # Package verification
├── cleanup_workshop.py         # Resource cleanup
├── install-task.py             # Task installer
├── sample-app/                 # Demo Node.js application
│   ├── package.json
│   ├── index.js
│   ├── test.js
│   └── README.md
└── templates/                  # AWS resource templates
    ├── role.json              # IAM role
    ├── policy.json            # IAM policy
    ├── demo-test.yaml         # Test BuildSpec
    ├── demo-publish.yaml      # Publish BuildSpec
    └── pipeline-template.json # Pipeline definition
```

## Troubleshooting

**"Docker not running"**  
→ Start Docker Desktop

**"Sample app not found"**  
→ Make sure you cloned the complete repo with `sample-app/` directory

**"Command not found"**  
→ Use `python3` instead of `python`

**"LocalStack services not available"**  
→ Ensure you have a valid LocalStack Pro API key set

**"Pipeline execution failed"**  
→ Check logs with `task logs` or `python3 view_logs.py`

### Cleanup

```bash
# Remove everything
task cleanup

# Or manually
python3 cleanup_workshop.py --force
```

## Extended Exercises

1. **Modify the sample app** - Add new functions and tests
2. **Add parallel testing** - Run multiple CodeBuild jobs
3. **Docker integration** - Build and push container images  
4. **Multi-environment** - Create dev/staging/prod pipelines
5. **Notification integration** - Add SNS/SES notifications

## Resources

- [LocalStack Documentation](https://docs.localstack.cloud/)
- [LocalStack Pro Pricing](https://www.localstack.cloud/pricing) (14-day free trial)
- [AWS CodePipeline User Guide](https://docs.aws.amazon.com/codepipeline/)
- [AWS CodeBuild User Guide](https://docs.aws.amazon.com/codebuild/)
- [AWS CodeArtifact User Guide](https://docs.aws.amazon.com/codeartifact/)

## License

This workshop is provided under the MIT License.