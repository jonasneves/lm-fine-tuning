# Supervised Fine-Tuning (SFT) Configurations

SFT is the most common starting point for fine-tuning. You provide demonstration data showing inputs and desired outputs.

## When to Use SFT

- You have high-quality examples of desired behavior
- Customer support conversations
- Code generation pairs
- Domain-specific Q&A
- Task-specific instructions

## Dataset Requirements

Your dataset should have one of these formats:

### Format 1: Messages Column (Recommended)
```json
{
  "messages": [
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a high-level programming language..."}
  ]
}
```

### Format 2: Text Column
```json
{
  "text": "User: What is Python?\nAssistant: Python is a high-level programming language..."
}
```

### Format 3: Prompt/Completion
```json
{
  "prompt": "What is Python?",
  "completion": "Python is a high-level programming language..."
}
```

## Example Commands

### Quick Test Run
```
Do a quick test run to SFT Qwen2.5-0.5B with 100 examples of open-r1/codeforces-cots.
```

### Production Run
```
Fine-tune Qwen2.5-0.5B on my-org/support-conversations for 3 epochs.
Use a10g-small GPU. Checkpoint every 500 steps.
```

### With Custom Learning Rate
```
SFT Qwen2.5-1.5B on my-org/instructions with:
- Learning rate: 2e-5
- Batch size: 8
- 3 epochs
- Cosine scheduler
```

## Hardware Recommendations

| Model Size | GPU | Memory | Cost/Hour | Typical Training Time |
|-----------|-----|--------|-----------|---------------------|
| 0.5-1B | t4-small | 16GB | $0.75 | 20-40 min |
| 1-3B | t4-medium | 24GB | $1.00 | 1-3 hours |
| 3-7B | a10g-large | 24GB | $2.50 | 2-6 hours |
| 7B+ | a100-large + LoRA | 40GB | $5.00 | 4-8 hours |

## Common Parameters

- **Epochs**: 1-5 (start with 3)
- **Learning Rate**: 1e-5 to 5e-5 (2e-5 is a good default)
- **Batch Size**: 4-16 (depends on GPU memory)
- **Max Sequence Length**: 512-2048 (longer = more memory)
- **Warmup Steps**: 10% of total steps
- **LoRA Rank** (for large models): 8-64 (16 is typical)

## Tips

1. **Start Small**: Test with 100 examples before full training
2. **Monitor Loss**: Training loss should steadily decrease
3. **Avoid Overfitting**: If validation loss increases, reduce epochs
4. **Use LoRA**: For models >3B, LoRA reduces memory and cost
5. **Checkpoint Often**: Every 500-1000 steps for long runs
