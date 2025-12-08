# Cloudflare Tunnel Setup Guide

Complete guide for setting up Cloudflare Tunnels to expose the Dashboard and MCP Server running on GitHub Actions.

## Overview

- **Dashboard**: Runs on `localhost:8000` (web interface)
- **MCP Server**: Runs on `localhost:3000` (API for Claude Code)

## Step 1: Create Cloudflare Tunnels

### 1.1 Access Cloudflare Zero Trust Dashboard

Go to [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/)

### 1.2 Create Dashboard Tunnel

1. Navigate to **Networks → Tunnels**
2. Click **Create a tunnel**
3. Choose **Cloudflared** as connector type
4. Name: `lm-training-dashboard`
5. Click **Save tunnel**
6. **Copy the tunnel token** - you'll need this for GitHub Secrets

### 1.3 Configure Dashboard Public Hostname

1. In the tunnel configuration, go to **Public Hostname** tab
2. Click **Add a public hostname**
3. Configure:
   - **Subdomain**: `lm-training` (or your choice)
   - **Domain**: Select your Cloudflare domain
   - **Service Type**: `HTTP`
   - **URL**: `localhost:8000`
4. Click **Save hostname**

Your dashboard will be accessible at: `https://lm-training.yourdomain.com`

### 1.4 Create MCP Server Tunnel (Optional)

Repeat the process for MCP Server:
1. Create new tunnel named `lm-training-mcp`
2. Copy the tunnel token
3. Configure public hostname:
   - **Subdomain**: `lm-mcp` (or your choice)
   - **Domain**: Select your Cloudflare domain
   - **Service Type**: `HTTP`
   - **URL**: `localhost:3000`

Your MCP server will be accessible at: `https://lm-mcp.yourdomain.com`

## Step 2: Add Tunnel Tokens to GitHub Secrets

### 2.1 Add Dashboard Token

```bash
gh secret set CLOUDFLARE_TUNNEL_TOKEN_DASHBOARD
# Paste the dashboard tunnel token when prompted
```

### 2.2 Add MCP Server Token (Optional)

```bash
gh secret set CLOUDFLARE_TUNNEL_TOKEN_MCP
# Paste the MCP tunnel token when prompted
```

### 2.3 Add Service URLs for Health Checks (Optional)

```bash
gh secret set DASHBOARD_API_URL
# Enter: https://lm-training.yourdomain.com

gh secret set MCP_SERVER_URL
# Enter: https://lm-mcp.yourdomain.com
```

### 2.4 Verify Secrets

```bash
gh secret list
```

You should see:
- `CLOUDFLARE_TUNNEL_TOKEN_DASHBOARD`
- `CLOUDFLARE_TUNNEL_TOKEN_MCP` (if configured)
- `DASHBOARD_API_URL` (if configured)
- `MCP_SERVER_URL` (if configured)
- `HF_TOKEN` (required for training)
- `GH_TOKEN` (required for workflow automation)

## Step 3: Test the Setup

### 3.1 Start Dashboard Workflow

```bash
gh workflow run dashboard.yml
```

### 3.2 Check Workflow Status

```bash
gh run list --workflow=dashboard.yml
```

### 3.3 Access Dashboard

Open your browser to: `https://lm-training.yourdomain.com`

You should see the LM Fine-Tuning Dashboard interface.

### 3.4 Test Health Endpoint

```bash
curl https://lm-training.yourdomain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-12-08T12:34:56Z",
  "hf_token_configured": true,
  "version": "1.0.0"
}
```

## Step 4: Configure Claude Code (MCP Client)

### 4.1 Update MCP Settings

Edit `~/.claude/mcp_settings.json`:

```json
{
  "mcpServers": {
    "lm-fine-tuning": {
      "url": "https://lm-mcp.yourdomain.com",
      "apiKey": "optional-if-you-add-auth"
    }
  }
}
```

### 4.2 Test MCP Server

```bash
curl https://lm-mcp.yourdomain.com/health
```

## Troubleshooting

### Tunnel Won't Start

**Error**: `CLOUDFLARE_TUNNEL_TOKEN is not set`
- **Solution**: Make sure you added the secret to GitHub (Step 2.1)

**Error**: `Incorrect Usage: flag needs an argument: -token`
- **Solution**: The tunnel token is empty or invalid. Regenerate and re-add the secret.

### Can't Access Public URL

**Issue**: 404 or connection timeout
- **Check**: Tunnel status in Cloudflare dashboard (should show "Healthy")
- **Check**: Workflow is running on GitHub Actions
- **Check**: Public hostname is configured correctly in Cloudflare

### Health Check Returns 502

**Issue**: Service is not responding
- **Check**: Dashboard/MCP server started successfully in GitHub Actions logs
- **Check**: Correct port is configured in Cloudflare (8000 for dashboard, 3000 for MCP)

## Security Recommendations

### 1. Add Authentication (TODO)

The current setup has no authentication. Consider adding:
- Cloudflare Access policies
- API key authentication
- OAuth integration

### 2. Restrict Access by IP (Optional)

In Cloudflare Access:
1. Go to **Access → Applications**
2. Add your public hostname
3. Create policy to allow only specific IPs or email domains

### 3. Enable Rate Limiting

In Cloudflare dashboard:
1. Go to **Security → WAF**
2. Add rate limiting rules for API endpoints

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│ GitHub Actions Runner (Free Tier)                      │
│                                                         │
│  ┌──────────────────┐      ┌─────────────────┐        │
│  │ Dashboard API    │      │ MCP Server      │        │
│  │ localhost:8000   │      │ localhost:3000  │        │
│  └────────┬─────────┘      └────────┬────────┘        │
│           │                         │                  │
│           │                         │                  │
│  ┌────────▼─────────┐      ┌────────▼────────┐        │
│  │ cloudflared      │      │ cloudflared     │        │
│  │ (tunnel agent)   │      │ (tunnel agent)  │        │
│  └────────┬─────────┘      └────────┬────────┘        │
└───────────┼─────────────────────────┼─────────────────┘
            │                         │
            │ Encrypted Tunnel        │
            │                         │
┌───────────▼─────────────────────────▼─────────────────┐
│ Cloudflare Edge Network                               │
│                                                        │
│  ┌──────────────────────┐    ┌────────────────────┐  │
│  │ lm-training.domain   │    │ lm-mcp.domain      │  │
│  │ (Public Hostname)    │    │ (Public Hostname)  │  │
│  └──────────┬───────────┘    └─────────┬──────────┘  │
└─────────────┼──────────────────────────┼─────────────┘
              │                          │
              │ HTTPS                    │
              │                          │
      ┌───────▼──────┐          ┌────────▼────────┐
      │ Web Browser  │          │ Claude Code     │
      │ (Dashboard)  │          │ (MCP Client)    │
      └──────────────┘          └─────────────────┘
```

## Cost

- **Cloudflare Tunnel**: Free (unlimited bandwidth)
- **GitHub Actions**: Free tier (2,000 minutes/month)
- **Cloudflare DNS**: Free

Total monthly cost: **$0** (within free tier limits)

## Auto-Restart Behavior

Both workflows automatically restart before the 6-hour GitHub Actions timeout:

1. **Default Runtime**: 5.5 hours
2. **Auto-Restart**: Triggers new workflow run
3. **Seamless Handoff**: ~10-30 second downtime during restart
4. **Health Check**: Monitors and restarts if services go down (every 10 minutes)

## Next Steps

After setup is complete:
1. Access dashboard at your public URL
2. Create your first training job
3. Monitor costs and job progress
4. Set up authentication (recommended for production)
5. Configure MCP client in Claude Code for AI-assisted training
