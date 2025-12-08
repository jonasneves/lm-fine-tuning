# LM Fine-Tuning Interface & Automation

Complete interface and GitHub Actions integration for managing training jobs.

## Overview

This interface provides a web dashboard (matching your serverless-llm theme) for:
- **Training Job Management**: Create, monitor, and manage HF Jobs training runs
- **Cost Tracking**: Real-time cost estimates and budget monitoring
- **Dataset Validation**: Check dataset compatibility before training
- **Model Conversion**: Submit GGUF conversion jobs
- **GitHub Actions Integration**: Trigger and monitor jobs via workflows

## Components

### 1. Web Dashboard (`app/dashboard/`)

#### `/` - Training Dashboard
- **Job Cards**: Visual cards for each training job (similar to your workflow cards)
- **Status Monitoring**: Real-time status updates (pending, running, completed, failed)
- **Cost Tracking**: Display estimated and actual costs
- **Quick Actions**: Start, stop, view logs, convert to GGUF

#### `/jobs` - Job List
- Table view of all training jobs
- Filter by status, training method (SFT/DPO/GRPO), model size
- Search by job ID, model name, dataset

#### `/create` - New Training Job
- Form to create new training jobs
- Model selector (0.5B-7B)
- Dataset input with validation
- Hardware selection with cost estimates
- Training method (SFT, DPO, GRPO) configuration

#### `/datasets` - Dataset Manager
- List uploaded/available datasets
- Validation status for SFT/DPO/GRPO compatibility
- Upload new datasets or link to HF Hub
- Preview dataset samples

### 2. API Server (`app/dashboard/api/server.py`)

FastAPI backend providing:

```
GET  /api/jobs              - List all training jobs
POST /api/jobs              - Create new training job
GET  /api/jobs/{id}         - Get job details
POST /api/jobs/{id}/cancel  - Cancel running job
GET  /api/jobs/{id}/logs    - Stream training logs

GET  /api/datasets          - List datasets
POST /api/datasets/validate - Validate dataset format
GET  /api/datasets/{id}     - Get dataset info

GET  /api/models            - List fine-tuned models
POST /api/convert/gguf      - Submit GGUF conversion

GET  /api/costs             - Get cost summary
GET  /api/costs/{id}        - Get job cost details
```

### 3. GitHub Actions Workflows (`.github/workflows/`)

#### `train-model.yml`
Trigger via:
- **Manual dispatch**: From GitHub UI or CLI
- **API**: Via workflow dispatch from dashboard
- **Claude Code**: Using HF Skills

Inputs:
- `model_name`: Base model (e.g., Qwen2.5-0.5B)
- `dataset`: HF Hub dataset ID
- `training_method`: sft | dpo | grpo
- `hardware`: t4-small | t4-medium | a10g-small | a10g-large
- `config_json`: JSON string with training parameters

#### `validate-dataset.yml`
Quick validation job (runs on GitHub runners, not HF):
- Check dataset format
- Verify columns for training method
- Report compatibility

#### `convert-to-gguf.yml`
Post-training conversion:
- Merge LoRA adapters
- Convert to GGUF
- Apply quantization (Q4_K_M, Q5_K_M, Q8_0)
- Push to HF Hub

## Theme & Design

Matches your `serverless-llm` theme:
- **Primary Color**: #1e3a5f (dark blue)
- **Accent**: #2c4f7c
- **Success**: #059669 (green)
- **Warning**: #D97706 (orange)
- **Danger**: #DC2626 (red)
- **Info**: #0284C7 (blue)

## File Structure

```
lm-fine-tuning/
├── app/
│   └── dashboard/
│       ├── static/
│       │   ├── common.css              # Shared styles (serverless-llm theme)
│       │   ├── index.html              # Main dashboard
│       │   ├── jobs.html               # Job list view
│       │   ├── create.html             # New job form
│       │   ├── datasets.html           # Dataset manager
│       │   └── dashboard.js            # Frontend logic
│       ├── api/
│       │   ├── server.py               # FastAPI backend
│       │   ├── huggingface.py          # HF API integration
│       │   └── requirements.txt        # Python dependencies
│       └── README.md                   # Setup instructions
├── .github/
│   └── workflows/
│       ├── train-model.yml             # Training job workflow
│       ├── validate-dataset.yml        # Dataset validation
│       ├── convert-to-gguf.yml         # Model conversion
│       └── dashboard-server.yml        # Deploy dashboard (optional)
└── scripts/
    ├── trigger_training.py             # CLI script to trigger jobs
    └── monitor_job.py                  # CLI script to monitor progress
```

## Usage Examples

### 1. Via Web Dashboard

1. Start the dashboard:
   ```bash
   cd app/dashboard/api
   pip install -r requirements.txt
   export HF_TOKEN=your_token_here
   python server.py
   ```

2. Open http://localhost:8080

3. Click "New Training Job"

4. Fill in:
   - Model: Qwen2.5-0.5B
   - Dataset: open-r1/codeforces-cots
   - Method: SFT
   - Hardware: t4-small

5. Review cost estimate (~$0.50)

6. Click "Start Training"

### 2. Via GitHub Actions

```bash
# Trigger training via gh CLI
gh workflow run train-model.yml \
  -f model_name="Qwen2.5-0.5B" \
  -f dataset="open-r1/codeforces-cots" \
  -f training_method="sft" \
  -f hardware="t4-small" \
  -f config_json='{"epochs": 3, "learning_rate": "2e-5"}'

# Monitor job
gh run list --workflow=train-model.yml
gh run view <run_id> --log
```

### 3. Via Python Script

```python
# scripts/trigger_training.py
from huggingface_hub import HfApi

api = HfApi(token="your_token")

# Submit training job
job = api.create_training_job(
    model_id="Qwen/Qwen2.5-0.5B",
    dataset_id="open-r1/codeforces-cots",
    training_type="sft",
    hardware="t4-small",
    hyperparameters={
        "epochs": 3,
        "learning_rate": 2e-5,
    }
)

print(f"Job ID: {job.job_id}")
print(f"Monitor: https://huggingface.co/jobs/{job.job_id}")
```

### 4. Via Claude Code

```
Fine-tune Qwen2.5-0.5B on open-r1/codeforces-cots using SFT.
Use t4-small GPU, 3 epochs.
```

Claude will:
1. Use HF Skills to configure the job
2. Show cost estimate
3. Submit to HF Jobs when approved
4. Provide job ID and monitoring links

## Monitoring & Costs

### Dashboard Stats
- **Active Jobs**: Currently running
- **Completed (24h)**: Finished in last 24 hours
- **Total Cost (Month)**: MTD spending
- **Budget Remaining**: If budget set

### Job Card Details
Each job shows:
- Status (running/completed/failed/pending)
- Progress (% complete, steps/total)
- Elapsed time
- Estimated cost / Actual cost
- Training loss (real-time)
- ETA to completion
- Actions: View Logs, Cancel, Convert to GGUF

### Cost Tracking
- Real-time cost calculation based on hardware + duration
- Budget alerts when approaching limit
- Historical cost charts
- Export cost reports (CSV)

## Deployment Options

### Option 1: Local Development
```bash
cd app/dashboard/api
python server.py
# Access at http://localhost:8080
```

### Option 2: GitHub Actions (Self-Hosted Runner)
Deploy dashboard to a GitHub Actions runner:
- Runs 24/7 on your infrastructure
- Accessible via Cloudflare Tunnel (like serverless-llm)
- Auto-restart workflow

### Option 3: Cloud Deployment
Deploy to:
- **Hugging Face Spaces** (Gradio/Streamlit)
- **Vercel/Netlify** (Static frontend + serverless functions)
- **Railway/Render** (Full-stack)

## Integration with Serverless-LLM

Potential workflow:
1. **Train** model using this repo
2. **Convert** to GGUF (automatic)
3. **Deploy** to serverless-llm for inference
4. **Monitor** via serverless-llm status page

Cross-repo automation:
- Webhook trigger when model training completes
- Auto-push GGUF to serverless-llm models directory
- Update serverless-llm workflows to use new model
- Send notification to Discord/Slack

## Security

- **HF Token**: Store in GitHub Secrets or environment variables
- **API Authentication**: Optional JWT-based auth for dashboard
- **Rate Limiting**: Prevent abuse of training job submissions
- **Budget Limits**: Hard caps on spending per day/month

## Next Steps

1. Create the web interface files (HTML/CSS/JS)
2. Build the FastAPI backend
3. Set up GitHub Actions workflows
4. Test end-to-end training flow
5. Add cost tracking and monitoring
6. Integrate with serverless-llm deployment

Would you like me to:
A. Create the full dashboard HTML files?
B. Build the FastAPI backend server?
C. Set up GitHub Actions workflows first?
D. Create CLI scripts for quick testing?
