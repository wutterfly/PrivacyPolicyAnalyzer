class ModelLoadError(Exception):
    """Returned when a HuggingFace model/tokenizer fails to load."""

    model_name: str
    reason: str
    description: str
    code: str

    def __init__(self, model_name: str, reason: str):
        self.model_name = model_name
        self.reason = reason
        self.description = f"Failed to load model={model_name}: {reason}"
        self.code = "MODEL_LOAD_ERROR"

    def __repr__(self) -> str:
        return f"ModelLoadError: [{self.code} |-- {self.description}]"

    def __str__(self) -> str:
        return f"ModelLoadError: [{self.code} |-- {self.description}]"
