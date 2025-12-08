# MCP Server Setup Guide

Complete guide for setting up the MCP Server for Claude Code integration.

## Prerequisites

1. **Hugging Face Account** with Pro/Team plan
2. **Write-access HF Token**: Get from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
3. **GitHub Personal Access Token**: For workflow triggers
4. **Cloudflare Tunnel**: For public access (optional for local dev)

## Quick Start (Local Development)

### 1. Install Dependencies

```bash
cd mcp-server
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export HF_TOKEN="hf_your_write_access_token"
export GH_TOKEN="ghp_your_github_token"  # Optional
```

### 3. Start MCP Server

```bash
python server.py
```

Server will start on `http://localhost:3000`

### 4. Test the Server

```bash
# Health check
curl http://localhost:3000/health

# List available tools
curl http://localhost:3000/mcp/tools

# Test tool call
curl -X POST http://localhost:3000/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "validate_dataset",
    "parameters": {
      "dataset": "open-r1/codeforces-cots",
      "method": "sft"
    }
  }'
```

## Production Setup (GitHub Actions)

### 1. Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

```
HF_TOKEN=hf_...                           # Hugging Face write token
GH_TOKEN=ghp_...                          # GitHub personal access token
CLOUDFLARE_TUNNEL_TOKEN_MCP=...           # Cloudflare tunnel token
```

### 2. Create Cloudflare Tunnel

1. Go to [Cloudflare Zero Trust](https://one.dash.cloudflare.com/)
2. Navigate to **Access → Tunnels**
3. Create a new tunnel named "lm-training-mcp"
4. Configure to route to `localhost:3000`
5. Copy the tunnel token to GitHub Secrets

### 3. Start the MCP Server

```bash
# Via GitHub CLI
gh workflow run mcp-server.yml

# Or manually trigger from GitHub UI
# Actions → MCP Server → Run workflow
```

### 4. Verify It's Running

Your MCP server will be accessible at your Cloudflare Tunnel URL:
```
https://lm-training-mcp.yourdomain.com/health
```

## Integrating with Claude Code

### 1. Register the MCP Server

```bash
claude mcp add lm-training \
  https://lm-training-mcp.yourdomain.com \
  --header "Authorization: Bearer $HF_TOKEN"
```

For local development:
```bash
claude mcp add lm-training http://localhost:3000
```

### 2. Verify Connection

```bash
claude mcp list
```

You should see `lm-training` in the list.

### 3. Use in Claude Code

Start a conversation with Claude:

```
You: "Fine-tune Qwen2.5-0.5B on open-r1/codeforces-cots"

Claude will:
1. Connect to your MCP server
2. Call validate_dataset tool
3. Call estimate_cost tool
4. Show you the estimate
5. After approval, call create_training_job tool
6. Return job ID and monitoring URL
```

## Available MCP Tools

### 1. `create_training_job`

Create a new fine-tuning job.

**Parameters:**
- `model` (string, required): Base model name
- `dataset` (string, required): Dataset ID
- `method` (string, required): sft | dpo | grpo
- `hardware` (string, required): GPU type
- `config` (object, optional): Training config

**Example:**
```json
{
  "tool": "create_training_job",
  "parameters": {
    "model": "Qwen/Qwen2.5-0.5B",
    "dataset": "open-r1/codeforces-cots",
    "method": "sft",
    "hardware": "t4-small",
    "config": {
      "epochs": 3,
      "learning_rate": "2e-5",
      "batch_size": 8
    }
  }
}
```

### 2. `validate_dataset`

Validate dataset format before training.

**Parameters:**
- `dataset` (string, required): Dataset ID
- `method` (string, required): Training method

### 3. `estimate_cost`

Estimate training cost and time.

**Parameters:**
- `model` (string, required)
- `dataset` (string, required)
- `hardware` (string, required)
- `epochs` (integer, optional)

### 4. `get_job_status`

Get real-time job status and progress.

**Parameters:**
- `job_id` (string, required)

### 5. `list_jobs`

List all training jobs with filtering.

**Parameters:**
- `status` (string, optional): Filter by status
- `limit` (integer, optional): Max results

### 6. `cancel_job`

Cancel a running job.

**Parameters:**
- `job_id` (string, required)

### 7. `convert_to_gguf`

Convert model to GGUF format.

**Parameters:**
- `model` (string, required)
- `quantization` (string, optional): Q4_K_M | Q5_K_M | Q8_0
- `output_repo` (string, optional)

## Monitoring

### View Server Logs

```bash
# If running locally
# Logs appear in terminal

# If running on GitHub Actions
gh run list --workflow=mcp-server.yml
gh run view <run-id> --log
```

### Health Checks

The MCP server exposes a health endpoint:

```bash
curl https://lm-training-mcp.yourdomain.com/health
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

### Auto-Restart

The server automatically restarts before GitHub Actions' 6-hour timeout:

- Runs for 5.5 hours by default
- Triggers new workflow before shutdown
- Ensures zero downtime with multiple instances

## Troubleshooting

### "HF_TOKEN not set"

Set the environment variable or GitHub Secret:
```bash
export HF_TOKEN="hf_your_token"
```

### "Cannot connect to MCP server"

Check:
1. Server is running: `curl http://localhost:3000/health`
2. Cloudflare Tunnel is active
3. Firewall rules allow connections

### "Tool call failed"

Check server logs for detailed error messages:
```bash
# Local
# Check terminal output

# GitHub Actions
gh run view <run-id> --log
```

### "Job submission failed"

Verify:
1. HF_TOKEN has write access
2. Model and dataset names are correct
3. Hardware selection is valid

## Advanced Configuration

### Custom Port

```bash
PORT=8080 python server.py
```

### Multiple Instances

Run multiple MCP servers for high availability:

```bash
gh workflow run mcp-server.yml -f instance=1
gh workflow run mcp-server.yml -f instance=2
```

Cloudflare Tunnel load-balances between instances.

### Budget Limits

Set monthly spending limit:

```bash
export BUDGET_LIMIT_USD=100
```

Jobs exceeding budget will be rejected.

## Next Steps

- Try the [example prompts](EXAMPLES.md)
- Read the [full architecture](ARCHITECTURE.md)
- Integrate with [serverless-llm](../serverless-llm)

## Support

- **Issues**: [GitHub Issues](https://github.com/jonasneves/lm-fine-tuning/issues)
- **Docs**: [README.md](README.md), [ARCHITECTURE.md](ARCHITECTURE.md)
- **HF Skills**: [Hugging Face Skills](https://github.com/huggingface/skills)
