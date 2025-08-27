# 🚀 3-MINUTE QUICK START

**Perfect for conference talks and demos!**

## Setup (1 minute)

**You need:**
- Docker running (Docker Desktop)
- Python 3.8+ 
- GitHub token ([get here](https://github.com/settings/tokens))
- 8GB+ RAM (LocalStack needs resources)

```bash
# 1. Install Task runner (one-time)
python3 install-task.py

# 2. Set your GitHub token
export CODEPIPELINE_GH_TOKEN="your_token_here"
```

## Demo (2 minutes)
```bash
# Run complete demo - does everything!
task demo
```

**That's it!** This single command:
- ✅ Checks prerequisites
- ✅ Sets up LocalStack + all AWS services  
- ✅ Runs the pipeline
- ✅ Shows published packages

## Individual Commands
```bash
task check      # Check prerequisites only
task setup      # Setup workshop only  
task monitor    # Monitor pipeline only
task packages   # Check packages only
task cleanup    # Clean everything up
```

## Fallback: Python Commands

If Task runner fails to install:

```bash
python3 check_environment.py    # Check prerequisites
python3 setup_workshop.py       # Setup everything
python3 monitor_pipeline.py     # Watch pipeline  
python3 check_packages.py       # View results
python3 cleanup_workshop.py     # Clean up
```

---

## What This Demo Shows

1. **CodePipeline** - Orchestrates the CI/CD workflow
2. **CodeBuild** - Runs tests and builds  
3. **CodeArtifact** - Hosts private npm packages
4. **CodeConnections** - Integrates with GitHub
5. **Everything runs in LocalStack container on YOUR machine** - No AWS costs, all local!

## Conference Talk Flow

1. **Show Prerequisites** (1 min)
   ```bash
   python3 check_environment.py
   ```

2. **One Command Setup** (1 min)
   ```bash
   python3 setup_workshop.py
   ```

3. **Watch Pipeline Execute** (2 min)
   ```bash
   python3 monitor_pipeline.py
   ```

4. **Show Published Package** (1 min)
   ```bash
   python3 check_packages.py
   npm pack my-lodash-fork
   ```

**Total: 5 minutes + Q&A**

---

## Troubleshooting

**"Docker not running"**
→ Start Docker Desktop

**"No GitHub token"**  
→ `export CODEPIPELINE_GH_TOKEN="ghp_xxx"`

**"Command not found"**  
→ Use `python3` instead of `python`

**"LocalStack failed"**  
→ `python3 cleanup_workshop.py --force && python3 setup_workshop.py`

---

## What Attendees Get

- Complete working CI/CD pipeline
- All source code and templates  
- Step-by-step documentation
- Production-ready patterns
- Zero AWS costs

**This is the power of LocalStack! 🎉**