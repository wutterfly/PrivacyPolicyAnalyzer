from types import SimpleNamespace

from privacy_policy_analyzer.shared.util import DEFAULT_MAX_LENGTH, cap_max_length


def test_tokenizer_without_limit_gets_default():
    tokenizer = SimpleNamespace(model_max_length=int(1e30))  # DeBERTa-v3's placeholder
    cap_max_length(tokenizer)
    assert tokenizer.model_max_length == DEFAULT_MAX_LENGTH


def test_tokenizer_limit_is_kept():
    for limit in (128, 512, 4096):
        tokenizer = SimpleNamespace(model_max_length=limit)
        cap_max_length(tokenizer)
        assert tokenizer.model_max_length == limit
