# LM Fine-Tuning Architecture

Complete architecture for managing language model fine-tuning with zero infrastructure cost using GitHub Actions.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interaction                         │
│  Claude Code / Gemini CLI / Web Browser / gh CLI                │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              MCP Server (GitHub Actions Runner)                  │
│  • Runs 24/7 as long-running GH Actions job                     │
│  • Auto-restarts before 6hr timeout                             │
│  • Exposed via Cloudflare Tunnel                                │
│  • Tools: create_job, validate_dataset, monitor_status          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ├──────────────┬──────────────┬─────────────────┐
                 ▼              ▼              ▼                 ▼
    ┌─────────────────┐  ┌────────────┐  ┌─────────────┐  ┌─────────┐
    │ HF Jobs API     │  │ GitHub API │  │ REST API    │  │ Trackio │
    │ (Training)      │  │ (Workflows)│  │ (Dashboard) │  │ (Metrics)│
    └─────────────────┘  └────────────┘  └─────────────┘  └─────────┘
```

## Core Components

### 1. MCP Server (Primary Interface)

**GitHub Actions Live Management** (similar to serverless-llm):

```yaml
# .github/workflows/mcp-server.yml
name: MCP Server
on:
  workflow_dispatch:
    inputs:
      duration_hours:
        default: '5.5'
      auto_restart:
        default: true

jobs:
  run-mcp-server:
    runs-on: ubuntu-latest
    timeout-minutes: 360  # 6 hours max

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r mcp-server/requirements.txt

      - name: Start MCP Server with Cloudflare Tunnel
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
          CLOUDFLARE_TUNNEL_TOKEN: ${{ secrets.CLOUDFLARE_TUNNEL_TOKEN_MCP }}
        run: |
          # Start MCP server in background
          python mcp-server/server.py &
          MCP_PID=$!

          # Start Cloudflare tunnel
          cloudflared tunnel run &
          TUNNEL_PID=$!

          # Monitor and restart before timeout
          python scripts/keep_alive.py \
            --duration ${{ inputs.duration_hours }} \
            --auto-restart ${{ inputs.auto_restart }} \
            --pids "$MCP_PID,$TUNNEL_PID"
```

**Benefits:**
- ✅ Zero infrastructure cost (GitHub Actions free tier)
- ✅ 24/7 availability with auto-restart
- ✅ Same architecture as serverless-llm
- ✅ Easy integration between repos
- ✅ Cloudflare Tunnel for public access

### 2. REST API Server (Secondary Interface)

**Also runs as GitHub Actions job:**

```yaml
# .github/workflows/api-server.yml
name: REST API Server
on:
  workflow_dispatch:
    inputs:
      duration_hours:
        default: '5.5'

jobs:
  run-api-server:
    runs-on: ubuntu-latest
    timeout-minutes: 360

    steps:
      - name: Start FastAPI Server with Tunnel
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
          CLOUDFLARE_TUNNEL_TOKEN: ${{ secrets.CLOUDFLARE_TUNNEL_TOKEN_API }}
        run: |
          uvicorn app.dashboard.api.server:app --host 0.0.0.0 --port 8000 &
          API_PID=$!

          cloudflared tunnel run &
          TUNNEL_PID=$!

          python scripts/keep_alive.py \
            --duration ${{ inputs.duration_hours }} \
            --pids "$API_PID,$TUNNEL_PID"
```

### 3. Web Dashboard (Web Interface)

**Runs as static site or lightweight server:**

```yaml
# .github/workflows/dashboard.yml
name: Web Dashboard
on:
  workflow_dispatch:
    inputs:
      duration_hours:
        default: '5.5'

jobs:
  run-dashboard:
    runs-on: ubuntu-latest
    timeout-minutes: 360

    steps:
      - name: Start Dashboard Server
        env:
          CLOUDFLARE_TUNNEL_TOKEN: ${{ secrets.CLOUDFLARE_TUNNEL_TOKEN_DASHBOARD }}
          MCP_API_URL: ${{ secrets.MCP_API_URL }}
        run: |
          # Simple Python HTTP server for static files
          cd app/dashboard/static
          python -m http.server 8080 &
          SERVER_PID=$!

          cloudflared tunnel run &
          TUNNEL_PID=$!

          python ../../../scripts/keep_alive.py \
            --duration ${{ inputs.duration_hours }} \
            --pids "$SERVER_PID,$TUNNEL_PID"
```

### 4. Training Job Workflows (On-Demand)

**Triggered by MCP Server or manually:**

```yaml
# .github/workflows/train-model.yml
name: Train Model
on:
  workflow_dispatch:
    inputs:
      model_name:
        required: true
      dataset:
        required: true
      training_method:
        required: true
      hardware:
        required: true
      config_json:
        required: false

  repository_dispatch:
    types: [trigger_training]

jobs:
  train:
    runs-on: ubuntu-latest
    steps:
      - name: Submit to Hugging Face Jobs
        env:
          HF_TOKEN: ${{ secrets.HF_TOKEN }}
        run: |
          python scripts/submit_training_job.py \
            --model "${{ inputs.model_name }}" \
            --dataset "${{ inputs.dataset }}" \
            --method "${{ inputs.training_method }}" \
            --hardware "${{ inputs.hardware }}" \
            --config '${{ inputs.config_json }}'

      - name: Monitor Job Progress
        run: |
          python scripts/monitor_job.py \
            --job-id $JOB_ID \
            --stream-logs
```

## File Structure

```
lm-fine-tuning/
├── mcp-server/                          # MCP Server (Claude Code integration)
│   ├── server.py                        # MCP protocol implementation
│   ├── tools/
│   │   ├── training.py                  # Training job tools
│   │   ├── validation.py                # Dataset validation
│   │   ├── monitoring.py                # Job status & costs
│   │   └── conversion.py                # GGUF conversion
│   ├── manifest.json                    # MCP tool definitions
│   └── requirements.txt
│
├── app/
│   └── dashboard/
│       ├── api/                         # REST API Server
│       │   ├── server.py                # FastAPI application
│       │   ├── routes/
│       │   │   ├── jobs.py              # Job endpoints
│       │   │   ├── datasets.py          # Dataset endpoints
│       │   │   └── models.py            # Model endpoints
│       │   ├── services/
│       │   │   ├── huggingface.py       # HF API client
│       │   │   ├── github.py            # GitHub API client
│       │   │   └── costs.py             # Cost calculation
│       │   ├── openapi.yaml             # API specification
│       │   └── requirements.txt
│       │
│       └── static/                      # Web Dashboard (Frontend)
│           ├── index.html               # Main dashboard
│           ├── jobs.html                # Job list view
│           ├── create.html              # New job form
│           ├── datasets.html            # Dataset manager
│           ├── common.css               # Shared styles
│           └── dashboard.js             # Frontend logic
│
├── .github/
│   └── workflows/
│       ├── mcp-server.yml               # MCP Server (24/7)
│       ├── api-server.yml               # REST API Server (24/7)
│       ├── dashboard.yml                # Web Dashboard (24/7)
│       ├── train-model.yml              # Training job (on-demand)
│       ├── validate-dataset.yml         # Dataset validation (on-demand)
│       ├── convert-to-gguf.yml          # Model conversion (on-demand)
│       └── health-check.yml             # Monitor all services
│
├── scripts/
│   ├── keep_alive.py                    # Auto-restart handler
│   ├── submit_training_job.py           # Submit job to HF
│   ├── monitor_job.py                   # Monitor job progress
│   ├── validate_dataset.py              # Validate dataset
│   └── trigger_workflow.py              # Trigger GH workflows
│
├── configs/                             # Training configurations
│   ├── sft/
│   ├── dpo/
│   └── grpo/
│
├── docs/
│   ├── ARCHITECTURE.md                  # This file
│   ├── MCP_SERVER.md                    # MCP server setup
│   ├── API_REFERENCE.md                 # API documentation
│   └── GITHUB_ACTIONS.md                # Workflow documentation
│
├── README.md
├── SETUP.md
├── EXAMPLES.md
└── INTERFACE.md
```

## Service URLs (via Cloudflare Tunnels)

```
MCP Server:    https://lm-training-mcp.yourdomain.com
REST API:      https://lm-training-api.yourdomain.com
Dashboard:     https://lm-training.yourdomain.com
```

## Integration Flow

### Flow 1: User → Claude Code → MCP Server → HF Jobs

```
1. User: "Fine-tune Qwen2.5-0.5B on my-dataset"
   ↓
2. Claude Code connects to MCP Server (via Cloudflare Tunnel)
   ↓
3. MCP Server calls: validate_dataset("my-dataset")
   ↓
4. MCP Server calls: estimate_cost(model, dataset, hardware)
   ↓
5. Claude shows estimate: "$0.75, ~25min, t4-small"
   ↓
6. User: "Approve"
   ↓
7. MCP Server triggers:
   - Option A: Direct HF Jobs API call
   - Option B: GitHub workflow dispatch (train-model.yml)
   ↓
8. Training starts on HF Jobs
   ↓
9. MCP Server monitors progress (polling or webhooks)
   ↓
10. Claude streams updates: "Step 350/1000, Loss: 1.23, ETA: 15min"
    ↓
11. Training completes
    ↓
12. MCP Server returns: job_id, model_url, cost_actual
    ↓
13. Claude: "Training complete! Model: username/model-name, Cost: $0.73"
```

### Flow 2: User → Web Dashboard → REST API → HF Jobs

```
1. User opens: https://lm-training.yourdomain.com
   ↓
2. Dashboard fetches active jobs from REST API
   ↓
3. User clicks "New Training Job"
   ↓
4. Form: Model, Dataset, Method, Hardware
   ↓
5. Dashboard calls: POST /api/jobs/estimate
   ↓
6. Shows cost estimate
   ↓
7. User clicks "Start Training"
   ↓
8. Dashboard calls: POST /api/jobs
   ↓
9. REST API submits to HF Jobs or triggers workflow
   ↓
10. Dashboard polls: GET /api/jobs/{id}
    ↓
11. Shows real-time progress updates
```

### Flow 3: Automated Training Pipeline

```
1. Serverless-LLM detects model needs fine-tuning
   ↓
2. Webhook triggers: lm-fine-tuning workflow
   ↓
3. Workflow runs training job
   ↓
4. On completion: converts to GGUF
   ↓
5. Pushes GGUF to serverless-llm repo
   ↓
6. Triggers serverless-llm workflow to deploy new model
   ↓
7. New model available for inference
```

## GitHub Secrets Required

```bash
# Hugging Face
HF_TOKEN=hf_...                          # Write access token

# Cloudflare Tunnels
CLOUDFLARE_TUNNEL_TOKEN_MCP=...          # For MCP server
CLOUDFLARE_TUNNEL_TOKEN_API=...          # For REST API
CLOUDFLARE_TUNNEL_TOKEN_DASHBOARD=...    # For web dashboard

# Service URLs (for cross-communication)
MCP_API_URL=https://lm-training-mcp.yourdomain.com
REST_API_URL=https://lm-training-api.yourdomain.com

# Optional
GH_TOKEN=ghp_...                         # For triggering workflows
SLACK_WEBHOOK=...                        # For notifications
BUDGET_LIMIT_USD=100                     # Monthly budget cap
```

## High Availability Setup

Similar to serverless-llm, run multiple instances:

```bash
# Start 2 MCP server instances
gh workflow run mcp-server.yml -f instance=1
gh workflow run mcp-server.yml -f instance=2

# Cloudflare load-balances between them
# Zero downtime during restarts
```

## Cost Tracking & Budget Management

### Real-Time Cost Calculation

```python
# mcp-server/tools/monitoring.py
def get_job_cost(job_id: str):
    """Calculate current job cost"""
    job = hf_api.get_job(job_id)

    hardware_cost = {
        "t4-small": 0.75,    # $/hour
        "t4-medium": 1.00,
        "a10g-small": 1.50,
        "a10g-large": 2.50,
        "a100-large": 5.00
    }

    elapsed_hours = (now() - job.start_time).total_seconds() / 3600
    cost = hardware_cost[job.hardware] * elapsed_hours

    return {
        "elapsed_hours": elapsed_hours,
        "cost_usd": round(cost, 2),
        "hardware": job.hardware,
        "hourly_rate": hardware_cost[job.hardware]
    }
```

### Budget Alerts

```python
# Check before starting new job
def check_budget(estimated_cost: float):
    """Prevent overspending"""
    monthly_spend = get_monthly_total()
    budget_limit = float(os.getenv("BUDGET_LIMIT_USD", 1000))

    if monthly_spend + estimated_cost > budget_limit:
        return {
            "approved": False,
            "reason": "Budget exceeded",
            "current": monthly_spend,
            "limit": budget_limit,
            "requested": estimated_cost
        }

    return {"approved": True}
```

## Monitoring & Health Checks

### Health Check Workflow

```yaml
# .github/workflows/health-check.yml
name: Health Check
on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes

jobs:
  check-services:
    runs-on: ubuntu-latest
    steps:
      - name: Check MCP Server
        run: |
          curl -f https://lm-training-mcp.yourdomain.com/health || \
          gh workflow run mcp-server.yml

      - name: Check REST API
        run: |
          curl -f https://lm-training-api.yourdomain.com/health || \
          gh workflow run api-server.yml

      - name: Check Dashboard
        run: |
          curl -f https://lm-training.yourdomain.com/health || \
          gh workflow run dashboard.yml
```

## Integration with Serverless-LLM

### Cross-Repo Automation

```yaml
# .github/workflows/deploy-to-serverless-llm.yml
name: Deploy Model to Serverless-LLM
on:
  workflow_dispatch:
    inputs:
      model_name:
        required: true
      gguf_url:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Clone serverless-llm repo
        uses: actions/checkout@v4
        with:
          repository: yourusername/serverless-llm
          token: ${{ secrets.GH_TOKEN }}

      - name: Download GGUF model
        run: |
          wget ${{ inputs.gguf_url }} -O models/${{ inputs.model_name }}.gguf

      - name: Update model config
        run: |
          python scripts/add_model.py \
            --name "${{ inputs.model_name }}" \
            --path "models/${{ inputs.model_name }}.gguf"

      - name: Commit and push
        run: |
          git add models/ config/
          git commit -m "Add fine-tuned model: ${{ inputs.model_name }}"
          git push

      - name: Trigger deployment
        run: |
          gh workflow run deploy-model.yml \
            -f model_name="${{ inputs.model_name }}"
```

## Next Steps

### Phase 1: Foundation (Week 1)
- [x] Documentation (ARCHITECTURE.md, INTERFACE.md)
- [ ] MCP Server implementation
- [ ] Basic tool definitions (create_job, validate_dataset, get_status)
- [ ] GitHub Actions workflows (mcp-server.yml, train-model.yml)
- [ ] Cloudflare Tunnel setup

### Phase 2: Core Features (Week 2)
- [ ] REST API server (FastAPI)
- [ ] Cost tracking & budget management
- [ ] Dataset validation tools
- [ ] Job monitoring with real-time updates

### Phase 3: Web Dashboard (Week 3)
- [ ] Dashboard HTML/CSS/JS
- [ ] Job list and detail views
- [ ] Create job form with validation
- [ ] Cost tracking dashboard

### Phase 4: Integration (Week 4)
- [ ] Serverless-LLM integration
- [ ] Automated model deployment
- [ ] Health monitoring & alerts
- [ ] Documentation & examples

## Security Considerations

1. **Token Management**
   - Store HF_TOKEN in GitHub Secrets
   - Rotate tokens regularly
   - Use read-only tokens where possible

2. **Budget Protection**
   - Hard cap on monthly spending
   - Require approval for jobs > $10
   - Alert on unusual spending patterns

3. **Access Control**
   - Optional: Add authentication to MCP/API
   - Rate limiting on endpoints
   - Audit log for all training jobs

4. **Network Security**
   - Cloudflare Tunnel for secure access
   - No public GitHub Actions runner
   - HTTPS only

## FAQ

**Q: Why GitHub Actions instead of dedicated servers?**
A: Zero cost, same approach as serverless-llm, easy integration, proven reliability.

**Q: What about GitHub Actions usage limits?**
A: Free tier provides 2000 minutes/month for private repos, unlimited for public. Our servers are long-running but lightweight.

**Q: Can this scale to many concurrent jobs?**
A: Yes - MCP/API servers are stateless, HF Jobs handles actual training compute. We just orchestrate.

**Q: How does this integrate with serverless-llm?**
A: Train models here → Convert to GGUF → Auto-deploy to serverless-llm → Serve via serverless inference.

**Q: What if a service crashes?**
A: Health check workflow detects and auto-restarts within 5 minutes.
