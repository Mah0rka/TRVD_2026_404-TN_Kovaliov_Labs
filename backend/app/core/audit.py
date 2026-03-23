import logging

from app.core.request_context import get_request_id

audit_logger = logging.getLogger("fcms.audit")


def log_audit_event(action: str, outcome: str, **fields: str | int | None) -> None:
    payload = " ".join(
        f"{key}={value}"
        for key, value in sorted(fields.items())
        if value is not None
    )
    audit_logger.info(
        "audit action=%s outcome=%s request_id=%s %s",
        action,
        outcome,
        get_request_id(),
        payload,
    )
