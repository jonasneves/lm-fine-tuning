# LM Fine-Tuning

Experiment with fine-tuning language models using Hugging Face Skills and Claude Code.

## Overview

This repository uses [Hugging Face Skills](https://github.com/huggingface/skills) to enable conversational fine-tuning of language models. Instead of writing training scripts manually, you describe what you want in plain English, and Claude Code handles:

- Dataset validation
- Hardware selection (GPU sizing)
- Training script generation
- Job submission to Hugging Face Jobs
- Progress monitoring with Trackio
- Model conversion (e.g., to GGUF for local use)

## Prerequisites

- **Hugging Face Account**: Pro or Team/Enterprise plan (required for Hugging Face Jobs)
- **HF Token**: Write-access token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
- **Claude Code**: Or another compatible coding agent (Codex, Gemini CLI)

## Setup

### 1. Install Claude Code Plugin

Register the Hugging Face Skills marketplace plugin:

```bash
/plugin marketplace add huggingface/skills
```

Install the LLM trainer skill:

```bash
/plugin install hf-llm-trainer@huggingface-skills
```

### 2. Authenticate with Hugging Face

Set up your write-access token:

```bash
# Option 1: Using HF CLI
hf auth login

# Option 2: Environment variable
export HF_TOKEN=hf_your_write_access_token_here
```

### 3. Configure MCP Server (for Claude Code)

Connect the Hugging Face MCP server with your token:

```bash
claude mcp add --transport http hf-skills https://huggingface.co/mcp?bouquet=skills --header "Authorization: Bearer $HF_TOKEN"
```

## Usage

### Quick Start Example

Tell Claude Code:

```
Fine-tune Qwen/Qwen2.5-0.5B on the open-r1/codeforces-cots dataset for instruction following.
```

Claude will:
1. Analyze the model and dataset
2. Select appropriate hardware (e.g., t4-small for a 0.5B model)
3. Show you the estimated cost and time
4. Submit the job when you approve
5. Provide a job ID and monitoring link

### Training Methods

#### Supervised Fine-Tuning (SFT)
Train on demonstration data (input-output pairs):

```
Fine-tune Qwen2.5-0.5B on my-org/support-conversations for 3 epochs.
```

#### Direct Preference Optimization (DPO)
Train on preference pairs (chosen vs rejected responses):

```
Run DPO on my-org/preference-data with the model I just trained.
The dataset has 'chosen' and 'rejected' columns.
```

#### Group Relative Policy Optimization (GRPO)
Reinforcement learning with verifiable rewards:

```
Train a math reasoning model using GRPO on openai/gsm8k based on Qwen2.5-0.5B.
```

### Monitoring Training

Check job status anytime:

```
What's the status of my training job?
```

View real-time metrics at your Trackio dashboard:
```
https://huggingface.co/spaces/YOUR_USERNAME/trackio
```

### Convert to GGUF

After training, convert your model for local use with llama.cpp:

```
Convert my fine-tuned model to GGUF with Q4_K_M quantization.
Push to username/my-model-gguf.
```

Then run locally:

```bash
llama-server -hf username/my-model-gguf:Q4_K_M
```

## Hardware & Cost Guidelines

| Model Size | Recommended GPU | Est. Cost/Hour | Training Time | Est. Total Cost |
|-----------|----------------|---------------|---------------|-----------------|
| <1B       | t4-small       | ~$0.75        | 20-40 min     | $0.25-$0.50     |
| 1-3B      | t4-medium      | ~$1.00        | 1-3 hours     | $1-$3           |
| 3-7B      | a10g-large     | ~$2.50        | 2-6 hours     | $5-$15          |
| 7B+ (LoRA)| a100-large     | ~$5.00        | 4-8 hours     | $20-$40         |

**Tip**: Always start with a test run on 100 examples to validate your pipeline before committing to a full production run.

## Project Structure

```
lm-fine-tuning/
├── README.md                    # This file
├── .gitignore                   # Git ignore rules
├── configs/                     # Training configurations
│   ├── sft/                    # Supervised fine-tuning configs
│   ├── dpo/                    # DPO configs
│   └── grpo/                   # GRPO configs
├── datasets/                    # Dataset preparation scripts
├── models/                      # Model-specific notes and configs
└── experiments/                 # Training logs and results
```

## Example Workflows

### Test Run (Quick Validation)

```
Do a quick test run to SFT Qwen2.5-0.5B with 100 examples of my-org/support-conversations.
```

### Production Run

```
SFT Qwen2.5-0.5B for production on the full my-org/support-conversations.
Checkpoints every 500 steps, 3 epochs, cosine learning rate.
```

### Dataset Validation

```
Check if my-org/conversation-data works for SFT training.
```

### Multi-Stage Training

```
1. SFT on my-org/instructions
2. Then DPO on my-org/preferences
3. Convert to GGUF Q4_K_M
```

## Resources

- [HF Skills Documentation](https://github.com/huggingface/skills/blob/main/hf-llm-trainer/skills/model-trainer/SKILL.md)
- [Hugging Face Jobs](https://huggingface.co/jobs)
- [TRL Documentation](https://huggingface.co/docs/trl)
- [Trackio Monitoring](https://huggingface.co/spaces)
- [Original Blog Post](https://huggingface.co/blog/claude-fine-tune-llm)

## Tips & Best Practices

1. **Start Small**: Test with t4-small and 100 examples before scaling up
2. **Validate Datasets**: Use the validation feature before training
3. **Monitor Progress**: Check Trackio during training to catch issues early
4. **Use LoRA**: For models >3B, LoRA is automatically used to reduce memory
5. **Estimate Costs**: Review estimated costs before approving jobs
6. **Checkpoint Often**: For long runs, checkpoint every 500-1000 steps

## Troubleshooting

**Out of Memory**: Reduce batch size or upgrade to larger GPU
**Dataset Format Error**: Validate dataset format, check column names
**Job Timeout**: Increase duration or optimize training settings
**Authentication Error**: Verify HF_TOKEN has write access

## License

MIT
