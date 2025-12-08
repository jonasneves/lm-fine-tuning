# LM Fine-Tuning Dashboard

Web interface for managing language model fine-tuning jobs.

## Features

- **Job Management**: Create, monitor, and cancel training jobs
- **Cost Tracking**: Real-time cost estimates and budget monitoring
- **Dataset Validation**: Check dataset compatibility before training
- **Progress Monitoring**: Live progress updates with status indicators
- **Model Conversion**: Convert trained models to GGUF format

## Quick Start

### Local Development

```bash
# 1. Install dependencies
cd app/dashboard/api
pip install -r requirements.txt

# 2. Set environment variables
export HF_TOKEN="hf_your_token"
export GH_TOKEN="ghp_your_token"  # Optional

# 3. Start the server
python server.py

# 4. Open browser
open http://localhost:8000
```

### Production (GitHub Actions)

```bash
# 1. Configure GitHub Secrets
# - HF_TOKEN
# - GH_TOKEN
# - CLOUDFLARE_TUNNEL_TOKEN_DASHBOARD

# 2. Start dashboard
gh workflow run dashboard.yml

# 3. Access via Cloudflare Tunnel
# https://lm-training.yourdomain.com
```

## API Endpoints

### Jobs
- `POST /api/jobs` - Create training job
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{id}` - Get job details
- `POST /api/jobs/{id}/cancel` - Cancel job
- `GET /api/jobs/{id}/logs` - Get job logs

### Datasets
- `POST /api/datasets/validate` - Validate dataset format
- `GET /api/datasets` - List available datasets

### Costs
- `POST /api/costs/estimate` - Estimate training cost
- `GET /api/costs` - Get cost summary

### Models
- `GET /api/models` - List base models
- `GET /api/models/fine-tuned` - List fine-tuned models

### Conversion
- `POST /api/convert/gguf` - Convert to GGUF format

### System
- `GET /health` - Health check
- `GET /api/system/stats` - System statistics

## Architecture

```
Browser → Cloudflare Tunnel → Dashboard API Server → HF Jobs API
                                       ↓
                              MCP Server (for tool reuse)
                                       ↓
                              GitHub Actions (workflows)
```

## Theme

Matches serverless-llm design:
- Primary color: #1e3a5f (dark blue)
- Clean card-based interface
- Real-time status indicators
- Mobile-responsive layout

## Development

### Adding New Features

1. **API Route**: Add to `api/server.py`
2. **Frontend**: Update `static/index.html` or create new page
3. **Styling**: Use classes from `static/common.css`

### Testing

```bash
# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/jobs

# Test with sample job
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Qwen/Qwen2.5-0.5B",
    "dataset": "open-r1/codeforces-cots",
    "method": "sft",
    "hardware": "t4-small"
  }'
```

## Deployment

### Cloudflare Tunnel Setup

1. Create tunnel at [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
2. Configure to route to `localhost:8000`
3. Copy tunnel token to GitHub Secrets
4. Start dashboard workflow

### Environment Variables

```bash
HF_TOKEN=hf_...                    # Required
GH_TOKEN=ghp_...                   # For workflow triggers
PORT=8000                          # Default port
HOST=0.0.0.0                       # Default host
BUDGET_LIMIT_USD=1000              # Monthly budget limit
```

## Security

- HF_TOKEN stored in GitHub Secrets
- CORS configured for specific origins in production
- Rate limiting on API endpoints (TODO)
- Optional authentication (TODO)

## Monitoring

Dashboard exposes health endpoint:
```bash
curl https://lm-training.yourdomain.com/health
```

Returns:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-08T12:34:56Z",
  "hf_token_configured": true,
  "version": "1.0.0"
}
```

## Next Steps

- [ ] Add user authentication
- [ ] Implement persistent job database
- [ ] Add real-time WebSocket updates
- [ ] Create job detail page
- [ ] Add dataset upload feature
- [ ] Implement cost alerts
- [ ] Add model comparison view

## Support

See main [README](../../../README.md) and [ARCHITECTURE](../../../ARCHITECTURE.md) for more details.
