from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class EntitlementSource(str, Enum):
    PURCHASE = "purchase"
    CASE_PASS = "case_pass"
    PROMO = "promo"
    FOUNDER_LIFETIME = "founder_lifetime_grant"
    STAFF = "staff"
    SCHOLARSHIP = "scholarship"
    INSTITUTION = "institution"


class Entitlement(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    subject_id: str
    tier: str
    source: EntitlementSource
    revocable: bool = True
    billing_required: bool = True
    starts_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    revoked_at: datetime | None = None

    @classmethod
    def founder_lifetime(cls, subject_id: str, *, tier: str = "premium") -> "Entitlement":
        return cls(
            subject_id=subject_id,
            tier=tier,
            source=EntitlementSource.FOUNDER_LIFETIME,
            revocable=False,
            billing_required=False,
            expires_at=None,
        )

    def active(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        if self.revoked_at is not None:
            return False
        if self.starts_at > now:
            return False
        return self.expires_at is None or self.expires_at > now


class EntitlementLedger:
    """In-memory domain ledger; persistence adapters can wrap this interface."""

    def __init__(self) -> None:
        self._items: dict[str, Entitlement] = {}

    def grant(self, entitlement: Entitlement) -> Entitlement:
        if entitlement.id in self._items:
            raise ValueError(f"entitlement already exists: {entitlement.id}")
        self._items[entitlement.id] = entitlement.model_copy(deep=True)
        return self._items[entitlement.id]

    def revoke(self, entitlement_id: str) -> Entitlement:
        entitlement = self._items[entitlement_id]
        if not entitlement.revocable:
            raise PermissionError("entitlement is immutable and cannot be revoked")
        updated = entitlement.model_copy(update={"revoked_at": datetime.now(timezone.utc)})
        self._items[entitlement_id] = updated
        return updated

    def active_for(self, subject_id: str, tier: str) -> bool:
        return any(
            item.subject_id == subject_id and item.tier == tier and item.active()
            for item in self._items.values()
        )

    def list_for(self, subject_id: str) -> list[Entitlement]:
        return [item.model_copy(deep=True) for item in self._items.values() if item.subject_id == subject_id]
