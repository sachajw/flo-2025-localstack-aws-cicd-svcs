# 🚀 5-MINUTE QUICK START

**Perfect for conference talks and demos!**

## Prerequisites (2 minutes)

**You need:**
- Docker running (Docker Desktop)
- Python 3.8+ 
- GitHub token ([get here](https://github.com/settings/tokens))
- 8GB+ RAM (LocalStack needs resources)

```bash
# 1. Check you have everything
python3 check_environment.py

# 2. Set your GitHub token
export CODEPIPELINE_GH_TOKEN="your_token_here"
```

## Demo (3 minutes)
```bash
# 1. Setup everything (auto-installs LocalStack, creates pipeline)
python3 setup_workshop.py

# 2. Watch the magic happen
python3 monitor_pipeline.py

# 3. See your published package
python3 check_packages.py
```

## Clean Up
```bash
# Remove everything
python3 cleanup_workshop.py --force
```

---

## Even Simpler with Task Runner

```bash
# Install Task (one-time)
python3 install-task.py

# Run the demo
task start         # Does everything
task monitor       # Watch pipeline
task packages      # Check results
task cleanup       # Clean up
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