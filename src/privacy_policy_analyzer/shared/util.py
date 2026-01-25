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
