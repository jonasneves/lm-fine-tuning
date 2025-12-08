# Setup Guide

Complete walkthrough for setting up your LM fine-tuning environment.

## 1. Install Claude Code

If you haven't already:

```bash
# macOS/Linux
curl -sSL https://dl.anthropic.com/claude-code/install.sh | bash

# Follow the installation prompts
```

## 2. Create Hugging Face Account

1. Go to [huggingface.co](https://huggingface.co)
2. Sign up for an account
3. Upgrade to Pro (required for Jobs): [huggingface.co/pricing](https://huggingface.co/pricing)
   - Pro: $9/month
   - Includes GPU job access

## 3. Get Write Token

1. Visit [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Name it: "claude-code-training"
4. Permissions: Select **"Write"** access
5. Copy the token (starts with `hf_...`)

## 4. Authenticate

Save your token securely:

```bash
# Option 1: HF CLI (recommended)
pip install huggingface-hub
huggingface-cli login
# Paste your token when prompted

# Option 2: Environment variable
export HF_TOKEN="hf_your_token_here"
# Add to ~/.zshrc or ~/.bashrc to persist
```

Verify authentication:

```bash
huggingface-cli whoami
```

## 5. Install Hugging Face Skills

Add the marketplace plugin:

```bash
claude
# Then in Claude Code:
/plugin marketplace add huggingface/skills
```

Install the LLM trainer skill:

```bash
/plugin install hf-llm-trainer@huggingface-skills
```

Verify installation:

```bash
/plugin list
# Should show: hf-llm-trainer@huggingface-skills
```

## 6. Configure MCP Server

Connect the Hugging Face MCP server with authentication:

```bash
claude mcp add --transport http hf-skills \
  https://huggingface.co/mcp?bouquet=skills \
  --header "Authorization: Bearer $HF_TOKEN"
```

If using a different shell (e.g., fish):

```bash
# Fish shell
claude mcp add --transport http hf-skills \
  https://huggingface.co/mcp?bouquet=skills \
  --header "Authorization: Bearer $HF_TOKEN"
```

Verify MCP connection:

```bash
claude mcp list
# Should show: hf-skills
```

## 7. Test Your Setup

Start Claude Code:

```bash
claude
```

Try a validation command:

```
Check if the dataset open-r1/codeforces-cots is suitable for SFT training.
```

If everything is set up correctly, Claude will:
1. Connect to Hugging Face
2. Analyze the dataset
3. Report compatibility

## 8. Run Your First Job

Try a quick test run:

```
Do a quick test run to fine-tune Qwen2.5-0.5B on 100 examples from open-r1/codeforces-cots.
```

Claude will:
1. Configure a training job
2. Show estimated cost (should be <$0.50)
3. Ask for approval
4. Submit the job
5. Provide monitoring links

## Troubleshooting

### "Authentication failed"

**Problem**: HF_TOKEN not set or invalid

**Solution**:
```bash
# Re-authenticate
huggingface-cli login

# Or set environment variable
export HF_TOKEN="hf_your_token_here"

# Verify
huggingface-cli whoami
```

### "Plugin not found"

**Problem**: Skill not installed correctly

**Solution**:
```bash
# Remove and reinstall
/plugin uninstall hf-llm-trainer@huggingface-skills
/plugin install hf-llm-trainer@huggingface-skills

# Verify
/plugin list
```

### "Write permission required"

**Problem**: Token doesn't have write access

**Solution**:
1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Delete old token
3. Create new token with **Write** permission
4. Re-authenticate with new token

### "MCP server not responding"

**Problem**: MCP server not configured or token not passed

**Solution**:
```bash
# Remove old config
claude mcp remove hf-skills

# Re-add with token
claude mcp add --transport http hf-skills \
  https://huggingface.co/mcp?bouquet=skills \
  --header "Authorization: Bearer $HF_TOKEN"
```

### "Pro subscription required"

**Problem**: Free tier doesn't have job access

**Solution**:
- Upgrade to Pro at [huggingface.co/pricing](https://huggingface.co/pricing)
- Or use Hugging Face Teams/Enterprise

## Verification Checklist

- [ ] Claude Code installed
- [ ] Hugging Face account created
- [ ] Pro subscription active
- [ ] Write token created
- [ ] Authenticated via `huggingface-cli login`
- [ ] Skills marketplace added
- [ ] `hf-llm-trainer` skill installed
- [ ] MCP server configured with token
- [ ] Test dataset validation successful

## Next Steps

Once setup is complete:

1. Read the [README.md](README.md) for usage examples
2. Review training methods in [configs/](configs/)
3. Try a quick test run to validate everything works
4. Run your first production training job

## Useful Links

- [Hugging Face Jobs](https://huggingface.co/jobs)
- [HF Skills Repository](https://github.com/huggingface/skills)
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [TRL Documentation](https://huggingface.co/docs/trl)
- [Trackio Monitoring](https://huggingface.co/spaces)
