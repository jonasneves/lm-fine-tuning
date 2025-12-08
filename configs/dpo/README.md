# Direct Preference Optimization (DPO) Configurations

DPO trains models on preference pairs where one response is "chosen" (preferred) and another is "rejected". This aligns model outputs with human preferences.

## When to Use DPO

- You have preference annotations from human labelers
- You want to align a model after initial SFT
- You have automated preference comparisons (e.g., based on correctness, helpfulness)
- Improving response quality and reducing harmful outputs

## Typical Pipeline

1. **Start with SFT**: Train a base model on demonstrations
2. **Generate responses**: Create candidate responses
3. **Get preferences**: Human annotators rank responses
4. **Apply DPO**: Train on preference pairs

## Dataset Requirements

Your dataset MUST have these columns:

```json
{
  "prompt": "How do I learn Python?",
  "chosen": "Start with the official Python tutorial at python.org. Practice daily with small projects...",
  "rejected": "Just Google it."
}
```

### Required Columns
- `prompt`: The input/question
- `chosen`: The preferred response
- `rejected`: The less preferred response

### Alternative Format
Some datasets use `messages` format:

```json
{
  "chosen": [
    {"role": "user", "content": "How do I learn Python?"},
    {"role": "assistant", "content": "Start with the official Python tutorial..."}
  ],
  "rejected": [
    {"role": "user", "content": "How do I learn Python?"},
    {"role": "assistant", "content": "Just Google it."}
  ]
}
```

## Example Commands

### Basic DPO
```
Run DPO on my-org/preference-data using the SFT model I just trained.
The dataset has 'chosen' and 'rejected' columns.
```

### DPO with Custom Base Model
```
Apply DPO to Qwen2.5-1.5B using my-org/helpfulness-preferences.
Use a10g-small, 2 epochs, learning rate 5e-6.
```

### Validate Dataset First
```
Check if my-org/preference-data is formatted correctly for DPO.
```

## Hardware Recommendations

DPO typically requires similar resources to SFT:

| Model Size | GPU | Memory | Cost/Hour | Typical Training Time |
|-----------|-----|--------|-----------|---------------------|
| 0.5-1B | t4-small | 16GB | $0.75 | 30-60 min |
| 1-3B | t4-medium | 24GB | $1.00 | 1-3 hours |
| 3-7B | a10g-large | 24GB | $2.50 | 3-6 hours |
| 7B+ | a100-large + LoRA | 40GB | $5.00 | 5-10 hours |

## Common Parameters

- **Epochs**: 1-3 (DPO usually needs fewer epochs than SFT)
- **Learning Rate**: 5e-7 to 5e-6 (lower than SFT!)
- **Beta**: 0.1-0.5 (controls preference strength, 0.1 is default)
- **Batch Size**: 4-16
- **Max Sequence Length**: Match your SFT training

## Important Notes

1. **Dataset Sensitivity**: DPO is very sensitive to dataset format - validate first!
2. **Lower Learning Rate**: Use 10x lower LR than SFT (e.g., 5e-6 instead of 5e-5)
3. **Start from SFT**: DPO works best when applied to an already-fine-tuned model
4. **Quality Matters**: Preference quality is critical - bad preferences make worse models
5. **Beta Parameter**: Higher beta = stronger preference enforcement

## Column Mapping

If your dataset uses different column names:

```
My DPO dataset uses 'good_response' and 'bad_response' instead of 'chosen' and 'rejected'.
Map 'good_response' to 'chosen' and 'bad_response' to 'rejected'.
```

## Public DPO Datasets

- `Anthropic/hh-rlhf` - Helpful and harmless preferences
- `Intel/orca_dpo_pairs` - Instruction following preferences
- `argilla/ultrafeedback-binarized-preferences` - General helpfulness

## Tips

1. **Validate Format**: Always validate dataset format before training
2. **Use Base Model**: Start from your SFT model, not a pre-trained base
3. **Small Beta**: Start with beta=0.1, increase if needed
4. **Monitor Carefully**: DPO can overfit quickly, watch validation metrics
5. **Test Outputs**: Generate samples during training to check quality
