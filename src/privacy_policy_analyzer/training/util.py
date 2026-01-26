import logging
import os
import random

import numpy as np
import torch
from datasets.utils import disable_progress_bar
from transformers import set_seed
from transformers.utils import logging as hf_logging


def set_global_seed(seed: int):
    """Set the global random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    set_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_optimal_precision():
    """
    Determine optimal precision with detailed GPU information.
    """
    if not torch.cuda.is_available():
        return {"precision": {}, "info": "No CUDA available"}

    device_name = torch.cuda.get_device_name(0)
    device_capability = torch.cuda.get_device_capability(0)
    major, minor = device_capability

    info = f"GPU: {device_name} (compute capability {major}.{minor})"

    # Ampere and newer (A100, A10, RTX 30xx/40xx, etc.)
    if major >= 8:
        return {
            "precision": {"bf16": True},
            "info": f"{info} - Using BF16 (better numeric stability)",
        }

    # Volta and Turing (V100, T4, RTX 20xx, etc.)
    elif major >= 7:
        return {"precision": {"fp16": True}, "info": f"{info} - Using FP16"}

    # Pascal and older
    else:
        return {
            "precision": {},
            "info": f"{info} - Using FP32 (mixed precision not recommended)",
        }


def disable_logging():
    """Disable logging from transformers and datasets libraries."""
    disable_progress_bar()
    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "true"
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    os.environ["HF_DATASETS_NO_ADVISORY_WARNINGS"] = "true"
    os.environ["HF_DATASETS_DISABLE_PROGRESS_BAR"] = "true"

    hf_logging.set_verbosity_error()
    hf_logging.disable_progress_bar()
    logging.getLogger("transformers").setLevel(logging.ERROR)
    logging.getLogger("transformers.trainer").setLevel(logging.ERROR)
    logging.getLogger("datasets").setLevel(logging.ERROR)
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)
