# Datasets Directory

This directory contains dataset preparation scripts and notes about datasets used for training.

## Dataset Sources

### Public Datasets (Hugging Face Hub)

Most datasets are loaded directly from Hugging Face Hub - no need to download locally.

#### Instruction Following
- `HuggingFaceH4/no_robots` - High-quality instruction-response pairs
- `open-r1/codeforces-cots` - Coding problems with chain-of-thought
- `Anthropic/hh-rlhf` - Helpful and harmless conversations

#### Code Generation
- `bigcode/the-stack-smol` - Curated code snippets
- `openai/humaneval` - Python code problems with tests
- `bigcode/apps` - Competitive programming problems

#### Math & Reasoning
- `openai/gsm8k` - Grade school math word problems
- `hendrycks/math` - Advanced mathematics problems
- `microsoft/orca-math-word-problems-200k` - Math reasoning

#### Preference Data (for DPO)
- `Anthropic/hh-rlhf` - Human preferences on helpfulness/harmlessness
- `Intel/orca_dpo_pairs` - Instruction following preferences
- `argilla/ultrafeedback-binarized-preferences` - General quality preferences

## Dataset Formats

### SFT Format

#### Messages (Recommended)
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"},
    {"role": "assistant", "content": "Python is a programming language..."}
  ]
}
```

#### Text Format
```json
{
  "text": "<s>[INST] What is Python? [/INST] Python is a programming language...</s>"
}
```

#### Prompt-Completion
```json
{
  "prompt": "What is Python?",
  "completion": "Python is a programming language..."
}
```

### DPO Format

```json
{
  "prompt": "How do I learn programming?",
  "chosen": "Start with fundamentals like variables, loops...",
  "rejected": "Just copy code from Stack Overflow."
}
```

### GRPO Format

```json
{
  "question": "If x + 5 = 12, what is x?",
  "answer": "7"
}
```

## Validation

Before training, validate your dataset:

```
Check if my-org/dataset-name is suitable for SFT training.
```

Claude will check:
- Column names and format
- Data types
- Example quality
- Compatibility with training method

## Preparing Custom Datasets

### 1. Create Dataset on Hub

```python
from datasets import Dataset, load_dataset
import pandas as pd

# From pandas DataFrame
df = pd.DataFrame({
    "messages": [
        [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ],
        # ... more examples
    ]
})

dataset = Dataset.from_pandas(df)

# Push to Hub
dataset.push_to_hub("username/my-dataset")
```

### 2. Validate Format

```bash
claude
# Then:
Check if username/my-dataset works for SFT training.
```

### 3. Use in Training

```
Fine-tune Qwen2.5-0.5B on username/my-dataset.
```

## Dataset Best Practices

1. **Quality > Quantity**: 1,000 high-quality examples beats 10,000 noisy ones
2. **Diverse Examples**: Cover different aspects of your use case
3. **Consistent Format**: Stick to one format throughout
4. **Validation Split**: Include validation data to monitor overfitting
5. **Clean Data**: Remove duplicates, fix formatting issues
6. **Balanced**: For preferences, balance positive/negative examples

## Data Collection

### For SFT
- Human-written demonstrations
- Curated from existing sources
- Generated with strong models (GPT-4, Claude) with human review

### For DPO
- Human preference annotations
- AI comparison (use strong model to rank outputs)
- Rule-based preferences (e.g., shorter is better)

### For GRPO
- Problems with verifiable solutions
- Programmatic correctness checks
- Ground truth answers

## Filtering & Cleaning

Before uploading to Hub:

```python
from datasets import load_dataset

# Load raw data
dataset = load_dataset("path/to/raw")

# Filter short responses
dataset = dataset.filter(lambda x: len(x["text"]) > 100)

# Remove duplicates
dataset = dataset.unique("text")

# Remove bad words/content
dataset = dataset.filter(lambda x: not contains_bad_content(x["text"]))

# Push cleaned version
dataset.push_to_hub("username/my-clean-dataset")
```

## Example Preparation Scripts

See the `scripts/` directory (create as needed) for:
- `convert_format.py` - Convert between dataset formats
- `validate_dataset.py` - Check dataset compatibility
- `split_dataset.py` - Create train/val/test splits
- `filter_dataset.py` - Quality filtering

## Troubleshooting

### "Column not found"
Your dataset uses different column names. Ask Claude to map them:
```
My dataset has 'question' and 'answer' columns instead of 'messages'.
How do I map this for SFT training?
```

### "Invalid format"
Dataset structure doesn't match expected format:
```
Show me the correct format for SFT with multi-turn conversations.
```

### "Dataset too large"
If dataset is very large, use streaming:
```
Fine-tune on username/huge-dataset using streaming mode.
Don't load entire dataset into memory.
```

## Resources

- [Hugging Face Datasets](https://huggingface.co/docs/datasets)
- [Dataset Viewer](https://huggingface.co/docs/datasets/dataset_viewer)
- [Data Preparation Guide](https://huggingface.co/docs/trl/dataset_formats)
