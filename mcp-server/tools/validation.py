"""
Validation Tools - Dataset format validation
"""
import logging
from typing import Dict, Any, Optional
from huggingface_hub import HfApi
from datasets import load_dataset

logger = logging.getLogger(__name__)


class ValidationTools:
    """Tools for validating datasets before training"""

    def __init__(self, hf_api: Optional[HfApi] = None):
        self.hf_api = hf_api

    async def validate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate dataset format for training compatibility

        Checks:
        - Dataset exists and is accessible
        - Has required columns for training method
        - Data types are correct
        - Sample a few examples to verify format
        """
        dataset_name = params.get("dataset")
        method = params.get("method")

        if not dataset_name or not method:
            raise ValueError("Missing required parameters: dataset, method")

        logger.info(f"Validating dataset {dataset_name} for {method}")

        try:
            # Load a small sample (first 10 examples)
            dataset = load_dataset(dataset_name, split="train[:10]")

            # Get column names
            columns = dataset.column_names

            # Check format based on training method
            if method == "sft":
                result = self._validate_sft(dataset, columns)
            elif method == "dpo":
                result = self._validate_dpo(dataset, columns)
            elif method == "grpo":
                result = self._validate_grpo(dataset, columns)
            else:
                raise ValueError(f"Unknown training method: {method}")

            result["dataset"] = dataset_name
            result["method"] = method
            result["sample_count"] = len(dataset)

            return result

        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            return {
                "valid": False,
                "dataset": dataset_name,
                "method": method,
                "error": str(e),
                "suggestion": "Check dataset name and ensure it's publicly accessible"
            }

    def _validate_sft(self, dataset, columns: list) -> Dict[str, Any]:
        """Validate dataset for Supervised Fine-Tuning"""

        # Check for common SFT formats
        has_messages = "messages" in columns
        has_text = "text" in columns
        has_prompt_completion = "prompt" in columns and "completion" in columns

        if has_messages:
            # Verify messages format
            sample = dataset[0]["messages"]
            if not isinstance(sample, list):
                return {
                    "valid": False,
                    "error": "'messages' column must contain list of message dicts",
                    "format_found": type(sample).__name__
                }

            return {
                "valid": True,
                "format": "messages",
                "columns": columns,
                "message": "Dataset is ready for SFT training (messages format)"
            }

        elif has_text:
            return {
                "valid": True,
                "format": "text",
                "columns": columns,
                "message": "Dataset is ready for SFT training (text format)"
            }

        elif has_prompt_completion:
            return {
                "valid": True,
                "format": "prompt_completion",
                "columns": columns,
                "message": "Dataset is ready for SFT training (prompt/completion format)"
            }

        else:
            return {
                "valid": False,
                "error": "No SFT-compatible format found",
                "columns_found": columns,
                "expected": ["messages", "text", "prompt + completion"],
                "suggestion": "Dataset should have 'messages', 'text', or 'prompt'+'completion' columns"
            }

    def _validate_dpo(self, dataset, columns: list) -> Dict[str, Any]:
        """Validate dataset for Direct Preference Optimization"""

        required_columns = {"chosen", "rejected"}
        has_required = required_columns.issubset(set(columns))

        if not has_required:
            return {
                "valid": False,
                "error": "Missing required columns for DPO",
                "columns_found": columns,
                "required_columns": list(required_columns),
                "suggestion": "DPO requires 'chosen' and 'rejected' columns with preferred and rejected responses"
            }

        # Verify data format
        sample = dataset[0]
        if not isinstance(sample["chosen"], (str, list)):
            return {
                "valid": False,
                "error": "'chosen' column has incorrect format",
                "format_found": type(sample["chosen"]).__name__,
                "expected": "str or list"
            }

        return {
            "valid": True,
            "format": "dpo",
            "columns": columns,
            "message": "Dataset is ready for DPO training"
        }

    def _validate_grpo(self, dataset, columns: list) -> Dict[str, Any]:
        """Validate dataset for Group Relative Policy Optimization"""

        # GRPO typically needs question and answer (ground truth)
        has_question = any(col in columns for col in ["question", "problem", "input", "prompt"])
        has_answer = any(col in columns for col in ["answer", "solution", "output", "target"])

        if not (has_question and has_answer):
            return {
                "valid": False,
                "error": "Missing required columns for GRPO",
                "columns_found": columns,
                "required": "question/problem/input + answer/solution/output",
                "suggestion": "GRPO requires input and ground truth answer columns"
            }

        return {
            "valid": True,
            "format": "grpo",
            "columns": columns,
            "message": "Dataset is ready for GRPO training"
        }
