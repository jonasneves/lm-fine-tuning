# Example Training Prompts

Real-world examples you can copy/paste to Claude Code.

## Quick Test Runs (Validation)

### Validate Your Setup
```
Check if the dataset open-r1/codeforces-cots is suitable for SFT training.
```

### Minimal Test Run
```
Do a quick test run to fine-tune Qwen2.5-0.5B on 100 examples from open-r1/codeforces-cots.
Use t4-small GPU.
```

### Estimate Costs
```
Estimate the cost to fine-tune Qwen2.5-1.5B on my-org/custom-dataset.
Dataset has 10,000 examples, I want 3 epochs.
```

## Supervised Fine-Tuning (SFT)

### Basic Instruction Tuning
```
Fine-tune Qwen2.5-0.5B on HuggingFaceH4/no_robots for instruction following.
Use 3 epochs and checkpoint every 500 steps.
```

### Code Generation
```
SFT mistralai/Mistral-7B-v0.3 on bigcode/the-stack-smol (Python subset).
Use LoRA with rank 16, a100-large GPU, 2 epochs.
```

### Domain Adaptation
```
Fine-tune Qwen2.5-1.5B on my-org/medical-qa for healthcare QA.
Use a10g-small, learning rate 2e-5, 3 epochs.
Monitor with Trackio.
```

### Multi-turn Conversations
```
SFT Qwen2.5-0.5B on my-org/support-conversations.
Dataset has 'messages' column with user/assistant turns.
Use t4-medium, 3 epochs, cosine learning rate schedule.
```

## Direct Preference Optimization (DPO)

### Basic DPO After SFT
```
Run DPO on Anthropic/hh-rlhf using the model username/qwen-sft I just trained.
The dataset has 'chosen' and 'rejected' columns.
Use learning rate 5e-6, beta 0.1, 2 epochs.
```

### Custom Preference Dataset
```
Apply DPO to my fine-tuned model using my-org/helpfulness-preferences.
Map 'preferred' column to 'chosen' and 'dispreferred' to 'rejected'.
Use a10g-small, 2 epochs.
```

### Alignment for Safety
```
Align mistralai/Mistral-7B-v0.3 using Intel/orca_dpo_pairs.
Use LoRA rank 16, a100-large, learning rate 1e-6, beta 0.2.
```

## Group Relative Policy Optimization (GRPO)

### Math Reasoning
```
Train a math reasoning model using GRPO on openai/gsm8k.
Start from Qwen2.5-1.5B, use a10g-small.
Generate 8 samples per prompt, verify correctness of final answer.
```

### Code Generation with Tests
```
Apply GRPO to username/code-model using openai/humaneval.
Run unit tests to calculate rewards.
Use a100-large with LoRA, 1000 iterations.
```

### Custom Reward Function
```
Train with GRPO on my-org/logic-puzzles using username/base-model.
Use custom reward: +1.0 for correct, +0.5 for partial, 0.0 for wrong.
Generate 4 samples per prompt, temperature 0.8.
```

## Multi-Stage Pipelines

### SFT → DPO
```
1. First, fine-tune Qwen2.5-1.5B on my-org/instructions using SFT.
   Use a10g-small, 3 epochs, learning rate 2e-5.

2. Then apply DPO using my-org/preferences.
   Use learning rate 5e-6, beta 0.1, 2 epochs.

3. Push final model to username/qwen-aligned.
```

### SFT → GRPO
```
1. SFT Qwen2.5-0.5B on openai/gsm8k demonstrations.
   Use t4-medium, 3 epochs.

2. Apply GRPO on openai/gsm8k for reinforcement.
   Generate 8 samples per prompt, 500 iterations.

3. Evaluate on gsm8k test set and report accuracy.
```

### Full Pipeline with GGUF
```
1. Fine-tune Qwen2.5-1.5B on my-org/data using SFT.
2. Apply DPO using my-org/preferences.
3. Convert to GGUF with Q4_K_M quantization.
4. Push to username/my-model-gguf for local deployment.
```

## Model Conversion

### Basic GGUF Conversion
```
Convert username/my-finetuned-model to GGUF format.
Use Q4_K_M quantization.
Push to username/my-model-gguf.
```

### Multiple Quantizations
```
Convert username/my-model to GGUF with:
- Q4_K_M (4-bit, balanced)
- Q5_K_M (5-bit, higher quality)
- Q8_0 (8-bit, best quality)

Push all to username/my-model-gguf.
```

## Monitoring & Debugging

### Check Job Status
```
What's the status of my training job?
```

```
Show me the training logs for job abc123xyz.
```

### Debug Failed Job
```
My job abc123xyz failed. What went wrong?
```

```
Job had out-of-memory error. Suggest a fix.
```

### Resume Training
```
Resume training job abc123xyz from the last checkpoint.
```

## Dataset Preparation

### Validate Format
```
Check if my-org/custom-data works for SFT training.
Show me the first 3 examples.
```

### Format Conversion
```
My dataset has 'question' and 'answer' columns.
Convert to the format needed for SFT training.
Show me the conversion code.
```

### Split Dataset
```
Split my-org/full-dataset into:
- 90% train
- 5% validation
- 5% test

Push splits to my-org/dataset-splits.
```

## Cost Optimization

### Compare Hardware Options
```
Compare cost and time for fine-tuning Qwen2.5-3B on my-org/data using:
- a10g-small
- a10g-large
- a100-large with LoRA

Dataset has 5,000 examples, 3 epochs.
```

### Reduce Costs
```
Fine-tune Qwen2.5-1.5B on my-org/data but optimize for cost.
Suggest: smaller GPU, LoRA, reduced batch size, etc.
```

## Advanced Configurations

### Custom Hyperparameters
```
SFT Qwen2.5-1.5B on my-org/data with:
- Learning rate: 3e-5
- Batch size: 16
- Gradient accumulation: 4
- Weight decay: 0.01
- Warmup ratio: 0.1
- Max sequence length: 1024
- LoRA rank: 32
```

### Scheduled Learning Rate
```
Fine-tune with:
- Initial LR: 5e-5
- Cosine annealing schedule
- Warmup for first 10% of steps
- Minimum LR: 1e-6
```

### Early Stopping
```
Train Qwen2.5-1.5B on my-org/data with early stopping:
- Monitor validation loss
- Patience: 3 checkpoints
- Save best model based on validation perplexity
```

## Troubleshooting Examples

### Authentication Issue
```
I'm getting "authentication failed" error.
How do I fix my Hugging Face token?
```

### Dataset Format Error
```
My dataset validation failed with "missing 'messages' column".
My dataset has 'conversations' column instead.
How do I map it correctly?
```

### Out of Memory
```
Training failed with CUDA out of memory error.
Model: Qwen2.5-3B
GPU: a10g-small
Batch size: 16

Suggest fixes.
```

### Slow Training
```
My training is very slow (1 hour per epoch).
Model: Qwen2.5-1.5B
Dataset: 10,000 examples
GPU: t4-small

How can I speed it up?
```

## Tips for Prompting

1. **Be Specific**: Include model name, dataset, and hardware preferences
2. **State Goals**: Mention if it's a test run or production
3. **Include Constraints**: Budget limits, time constraints
4. **Ask Questions**: Claude can help you decide parameters
5. **Iterate**: Start with test runs, then scale up

## Common Patterns

### Test → Production Flow
```
# Step 1: Validate
Check if my-org/data works for SFT.

# Step 2: Quick test
Do a test run on 100 examples with t4-small.

# Step 3: Review and adjust
[Review results, adjust parameters]

# Step 4: Production
Run full training on entire dataset with a10g-large.
```

### Cost-Conscious Training
```
I want to fine-tune Qwen2.5-1.5B on my-org/data.
I have a $10 budget.
Suggest the best configuration for quality within budget.
```

### Quality-First Training
```
Fine-tune Qwen2.5-3B on my-org/premium-data.
Cost is not a concern. Optimize for best quality.
Use best hardware, optimal hyperparameters.
```
