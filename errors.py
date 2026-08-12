"""Shared application errors."""

from __future__ import annotations


class FeatureError(Exception):
    def __init__(self, code: str, status: int) -> None:
        super().__init__(code)
        self.code = code
        self.status = status


class InputError(FeatureError):
    def __init__(self, code: str = "invalid_request") -> None:
        super().__init__(code, 400)


class ValidationError(FeatureError):
    def __init__(self, code: str = "invalid_model_schema") -> None:
        super().__init__(code, 422)


class OllamaError(FeatureError):
    def __init__(self, code: str = "ollama_unavailable") -> None:
        super().__init__(code, 502)
