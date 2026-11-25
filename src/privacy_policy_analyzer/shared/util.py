import gc
from typing import Literal

import torch


def get_device() -> Literal["cuda", "cpu"]:
    return "cuda" if torch.cuda.is_available() else "cpu"


def cleanup_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
        torch.cuda.ipc_collect()


# The input length the training module cuts sentences to by default.
DEFAULT_MAX_LENGTH = 512
# Tokenizers without a length limit report a huge placeholder instead
# (transformers' VERY_LARGE_INTEGER, about 1e30).
_NO_MAX_LENGTH = 1_000_000


def cap_max_length(tokenizer) -> None:
    """Gives a tokenizer without a length limit DEFAULT_MAX_LENGTH, so that
    truncation=True truncates. DeBERTa-v3's tokenizer sets no limit and its
    relative positions accept any length, so a long segment would otherwise be
    classified whole (in training it was cut to 512 tokens) or exhaust GPU memory."""
    if tokenizer.model_max_length >= _NO_MAX_LENGTH:
        tokenizer.model_max_length = DEFAULT_MAX_LENGTH
