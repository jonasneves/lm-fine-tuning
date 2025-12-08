# Group Relative Policy Optimization (GRPO) Configurations

GRPO is a reinforcement learning approach that works well for tasks with verifiable rewards - problems where you can programmatically determine if an answer is correct.

## When to Use GRPO

- **Math reasoning**: Check if the final answer is correct
- **Code generation**: Run tests to verify correctness
- **Logic puzzles**: Validate solutions programmatically
- **Factual QA**: Compare against ground truth

## How GRPO Works

1. Model generates multiple responses
2. Responses receive rewards based on correctness
3. Model learns from successful attempts
4. Process repeats, gradually improving success rate

## Dataset Requirements

GRPO datasets need:
- **Problem/Question**: The input
- **Ground Truth**: The correct answer (for reward calculation)

Example for math:
```json
{
  "question": "If x + 5 = 12, what is x?",
  "answer": "7"
}
```

Example for code:
```json
{
  "problem": "Write a function to check if a number is prime",
  "tests": ["assert is_prime(7) == True", "assert is_prime(4) == False"],
  "solution": "def is_prime(n):\n    if n < 2: return False\n    ..."
}
```

## Example Commands

### Math Reasoning
```
Train a math reasoning model using GRPO on openai/gsm8k based on Qwen2.5-0.5B.
```

### Code Generation
```
Apply GRPO to my-org/coding-problems using my fine-tuned model.
Verify correctness by running unit tests.
```

### Custom Reward Function
```
Train with GRPO on my-org/logic-puzzles.
Use custom reward function: +1 for correct, -0.5 for partial, 0 for wrong.
```

## Hardware Recommendations

GRPO is more compute-intensive than SFT/DPO because it generates multiple responses:

| Model Size | GPU | Memory | Cost/Hour | Typical Training Time |
|-----------|-----|--------|-----------|---------------------|
| 0.5-1B | t4-medium | 24GB | $1.00 | 1-2 hours |
| 1-3B | a10g-small | 24GB | $1.50 | 2-4 hours |
| 3-7B | a10g-large | 24GB | $2.50 | 4-8 hours |
| 7B+ | a100-large + LoRA | 40GB | $5.00 | 8-16 hours |

## Common Parameters

- **Iterations**: 100-1000 (more iterations = more learning opportunities)
- **Samples per Prompt**: 4-16 (how many responses to generate)
- **Learning Rate**: 1e-6 to 1e-5 (similar to DPO)
- **Temperature**: 0.7-1.0 (higher = more diverse samples)
- **Reward Scale**: 1.0 (adjust based on your reward range)

## Reward Functions

### Binary (Correct/Incorrect)
```python
def reward(generated, ground_truth):
    return 1.0 if generated == ground_truth else 0.0
```

### Partial Credit
```python
def reward(generated, ground_truth):
    if exact_match(generated, ground_truth):
        return 1.0
    elif partial_match(generated, ground_truth):
        return 0.5
    else:
        return 0.0
```

### Code Correctness
```python
def reward(generated_code, test_cases):
    passed = run_tests(generated_code, test_cases)
    return passed / len(test_cases)
```

## Public GRPO-Suitable Datasets

- `openai/gsm8k` - Grade school math problems
- `hendrycks/math` - Mathematical reasoning
- `openai/humaneval` - Code generation
- `bigcode/apps` - Programming problems

## Important Notes

1. **Reward Design**: Quality of reward function is critical
2. **Exploration**: Model needs to explore to find correct solutions
3. **Computation**: GRPO is 2-4x more expensive than SFT due to sampling
4. **Base Model**: Start from a good SFT model for faster convergence
5. **Verification**: Ensure reward calculation is correct and deterministic

## Tips

1. **Start Simple**: Use binary rewards (correct/wrong) before adding complexity
2. **Verify Rewards**: Test reward function on known examples first
3. **Monitor Success Rate**: Track % of correct solutions during training
4. **Sample Diversity**: Higher temperature = better exploration
5. **Computational Budget**: GRPO takes longer - plan for 2x SFT time
6. **Pre-train with SFT**: Start with SFT on demonstrations, then apply GRPO

## Example Pipeline

```
1. SFT on openai/gsm8k demonstrations (show the model how to solve)
2. GRPO on openai/gsm8k (reinforce correct mathematical reasoning)
3. Evaluate on gsm8k test set
```

## Debugging GRPO

**Low Success Rate**: Model might need more SFT first
**No Improvement**: Check reward function, increase temperature
**Slow Training**: Reduce samples per prompt, use smaller GPU
**Memory Issues**: Decrease batch size or sequence length
