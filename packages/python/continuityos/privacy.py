from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


DEFAULT_SENSITIVE_KEYS = {
    "name", "full_name", "first_name", "last_name", "email", "phone", "address",
    "case", "case_id", "case_number", "docket", "docket_number", "police_report",
    "location", "latitude", "longitude", "precise_location", "contacts", "clipboard",
    "prompt", "response", "conversation", "message", "document", "document_text",
    "audio", "video", "image", "photo", "evidence", "ssn", "password", "secret",
    "token", "api_key", "authorization", "cookie",
}


class DiagnosticPolicy(BaseModel):
    allowed_fields: set[str] = Field(default_factory=lambda: {
        "event", "timestamp", "app_version", "platform", "module", "error_code",
        "duration_ms", "provider", "model_alias", "network_state", "metadata",
    })
    forbidden_keys: set[str] = Field(default_factory=lambda: set(DEFAULT_SENSITIVE_KEYS))
    forbidden_terms: set[str] = Field(default_factory=lambda: {"password", "secret", "token", "api_key"})
    max_string_length: int = Field(default=512, ge=1)


class TelemetryFirewall:
    """Allow-list based telemetry sanitizer. Unknown top-level fields are dropped."""

    def __init__(self, policy: DiagnosticPolicy | None = None) -> None:
        self.policy = policy or DiagnosticPolicy()

    def sanitize(self, event: dict[str, Any]) -> dict[str, Any]:
        clean: dict[str, Any] = {}
        for key, value in event.items():
            if key not in self.policy.allowed_fields:
                continue
            if self._sensitive_key(key):
                continue
            sanitized = self._sanitize_value(value)
            if sanitized is not _DROP:
                clean[key] = sanitized
        return clean

    def _sanitize_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            nested: dict[str, Any] = {}
            for key, item in value.items():
                if self._sensitive_key(str(key)):
                    continue
                sanitized = self._sanitize_value(item)
                if sanitized is not _DROP:
                    nested[str(key)] = sanitized
            return nested
        if isinstance(value, list):
            return [item for raw in value if (item := self._sanitize_value(raw)) is not _DROP]
        if isinstance(value, str):
            lowered = value.lower()
            if any(term.lower() in lowered for term in self.policy.forbidden_terms):
                return _DROP
            return value[: self.policy.max_string_length]
        if value is None or isinstance(value, (bool, int, float)):
            return value
        return _DROP

    def _sensitive_key(self, key: str) -> bool:
        normalized = key.lower().strip()
        return normalized in self.policy.forbidden_keys or any(
            term.lower() in normalized for term in self.policy.forbidden_terms
        )


class _Drop:
    pass


_DROP = _Drop()
