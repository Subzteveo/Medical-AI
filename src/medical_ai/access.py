from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status


ACCESS_CONFIG_ENV = "MEDICAL_AI_PILOT_ACCESS_JSON"
SESSION_SECRET_ENV = "MEDICAL_AI_PILOT_SESSION_SECRET"
COOKIE_SECURE_ENV = "MEDICAL_AI_PILOT_COOKIE_SECURE"
SESSION_TTL_ENV = "MEDICAL_AI_PILOT_SESSION_TTL_SECONDS"
SESSION_COOKIE_NAME = "medical_ai_pilot_session"

_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AccessConfigurationError(RuntimeError):
    pass


@dataclass(frozen=True)
class PilotParticipant:
    participant_id: str
    credential_id: str
    token_sha256: str
    expires_at: datetime
    revoked: bool = False


@dataclass(frozen=True)
class PilotAccessConfig:
    participants: tuple[PilotParticipant, ...]
    session_secret: bytes
    cookie_secure: bool
    session_ttl_seconds: int


def _parse_bool(value: str, *, default: bool) -> bool:
    if value == "":
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise AccessConfigurationError(f"{COOKIE_SECURE_ENV} must be true or false")


def _parse_expiry(value: object) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise AccessConfigurationError("participant expires_at must be a non-empty ISO-8601 timestamp")
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AccessConfigurationError("participant expires_at must be a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise AccessConfigurationError("participant expires_at must include a timezone offset")
    return parsed.astimezone(timezone.utc)


def load_access_config() -> PilotAccessConfig:
    raw = os.getenv(ACCESS_CONFIG_ENV, "")
    secret = os.getenv(SESSION_SECRET_ENV, "")
    if not raw:
        raise AccessConfigurationError(f"{ACCESS_CONFIG_ENV} is required")
    if len(secret.encode("utf-8")) < 32:
        raise AccessConfigurationError(f"{SESSION_SECRET_ENV} must contain at least 32 bytes")

    try:
        document = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AccessConfigurationError(f"{ACCESS_CONFIG_ENV} must be valid JSON") from exc
    if not isinstance(document, dict) or not isinstance(document.get("participants"), list):
        raise AccessConfigurationError(f"{ACCESS_CONFIG_ENV} must contain a participants array")
    if not document["participants"]:
        raise AccessConfigurationError("pilot participant allowlist must not be empty")

    participants: list[PilotParticipant] = []
    participant_ids: set[str] = set()
    credential_ids: set[str] = set()
    token_hashes: set[str] = set()
    for item in document["participants"]:
        if not isinstance(item, dict):
            raise AccessConfigurationError("each participant entry must be an object")
        participant_id = item.get("participant_id")
        credential_id = item.get("credential_id")
        token_sha256 = item.get("token_sha256")
        revoked = item.get("revoked", False)
        if not isinstance(participant_id, str) or not _IDENTIFIER_RE.fullmatch(participant_id):
            raise AccessConfigurationError("participant_id must use 1-128 safe identifier characters")
        if not isinstance(credential_id, str) or not _IDENTIFIER_RE.fullmatch(credential_id):
            raise AccessConfigurationError("credential_id must use 1-128 safe identifier characters")
        if not isinstance(token_sha256, str) or not _SHA256_RE.fullmatch(token_sha256):
            raise AccessConfigurationError("token_sha256 must be a lowercase SHA-256 hex digest")
        if not isinstance(revoked, bool):
            raise AccessConfigurationError("revoked must be true or false")
        if participant_id in participant_ids:
            raise AccessConfigurationError("participant_id values must be unique")
        if credential_id in credential_ids:
            raise AccessConfigurationError("credential_id values must be unique")
        if token_sha256 in token_hashes:
            raise AccessConfigurationError("token_sha256 values must be unique")
        participant_ids.add(participant_id)
        credential_ids.add(credential_id)
        token_hashes.add(token_sha256)
        participants.append(
            PilotParticipant(
                participant_id=participant_id,
                credential_id=credential_id,
                token_sha256=token_sha256,
                expires_at=_parse_expiry(item.get("expires_at")),
                revoked=revoked,
            )
        )

    ttl_raw = os.getenv(SESSION_TTL_ENV, "28800")
    try:
        ttl = int(ttl_raw)
    except ValueError as exc:
        raise AccessConfigurationError(f"{SESSION_TTL_ENV} must be an integer") from exc
    if ttl < 300 or ttl > 43200:
        raise AccessConfigurationError(f"{SESSION_TTL_ENV} must be between 300 and 43200 seconds")

    return PilotAccessConfig(
        participants=tuple(participants),
        session_secret=secret.encode("utf-8"),
        cookie_secure=_parse_bool(os.getenv(COOKIE_SECURE_ENV, ""), default=True),
        session_ttl_seconds=ttl,
    )


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _active_participant(
    participant: PilotParticipant, *, now: datetime | None = None
) -> PilotParticipant | None:
    current = now or datetime.now(timezone.utc)
    if participant.revoked or participant.expires_at <= current:
        return None
    return participant


def authenticate_invite_token(
    token: str, config: PilotAccessConfig, *, now: datetime | None = None
) -> PilotParticipant | None:
    supplied_digest = token_digest(token)
    matched: PilotParticipant | None = None
    for participant in config.participants:
        if hmac.compare_digest(supplied_digest, participant.token_sha256):
            matched = participant
    if matched is None:
        return None
    return _active_participant(matched, now=now)


def _participant_by_id(config: PilotAccessConfig, participant_id: str) -> PilotParticipant | None:
    for participant in config.participants:
        if hmac.compare_digest(participant.participant_id, participant_id):
            return participant
    return None


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def create_session_token(
    participant: PilotParticipant,
    config: PilotAccessConfig,
    *,
    now: datetime | None = None,
) -> tuple[str, int]:
    current = now or datetime.now(timezone.utc)
    session_expiry = min(
        participant.expires_at,
        current + timedelta(seconds=config.session_ttl_seconds),
    )
    max_age = max(1, int((session_expiry - current).total_seconds()))
    payload = {
        "v": 1,
        "participant_id": participant.participant_id,
        "credential_id": participant.credential_id,
        "exp": int(session_expiry.timestamp()),
    }
    encoded_payload = _b64url_encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = hmac.new(
        config.session_secret, encoded_payload.encode("ascii"), hashlib.sha256
    ).digest()
    return f"{encoded_payload}.{_b64url_encode(signature)}", max_age


def authenticate_session_token(
    session_token: str,
    config: PilotAccessConfig,
    *,
    now: datetime | None = None,
) -> PilotParticipant | None:
    try:
        encoded_payload, encoded_signature = session_token.split(".", 1)
        supplied_signature = _b64url_decode(encoded_signature)
        expected_signature = hmac.new(
            config.session_secret, encoded_payload.encode("ascii"), hashlib.sha256
        ).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            return None
        payload = json.loads(_b64url_decode(encoded_payload))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError, binascii.Error):
        return None

    if not isinstance(payload, dict) or payload.get("v") != 1:
        return None
    participant_id = payload.get("participant_id")
    credential_id = payload.get("credential_id")
    expiry = payload.get("exp")
    if not isinstance(participant_id, str) or not isinstance(credential_id, str):
        return None
    if not isinstance(expiry, int):
        return None

    current = now or datetime.now(timezone.utc)
    if expiry <= int(current.timestamp()):
        return None

    participant = _participant_by_id(config, participant_id)
    participant = _active_participant(participant, now=current) if participant else None
    if participant is None:
        return None
    if not hmac.compare_digest(participant.credential_id, credential_id):
        return None
    return participant


def _configuration_or_503() -> PilotAccessConfig:
    try:
        return load_access_config()
    except AccessConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pilot access is not configured",
        ) from exc


def _bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization")
    if authorization is None:
        return None
    scheme, separator, value = authorization.partition(" ")
    if not separator or scheme.lower() != "bearer" or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid pilot credential",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return value.strip()


def require_pilot_participant(request: Request) -> PilotParticipant:
    config = _configuration_or_503()

    bearer = _bearer_token(request)
    if bearer is not None:
        participant = authenticate_invite_token(bearer, config)
        if participant is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive pilot credential",
                headers={"WWW-Authenticate": "Bearer"},
            )
        request.state.pilot_participant_id = participant.participant_id
        return participant

    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    participant = (
        authenticate_session_token(session_token, config) if session_token else None
    )
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Pilot access required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    request.state.pilot_participant_id = participant.participant_id
    return participant


def optional_pilot_participant(request: Request) -> PilotParticipant | None:
    config = _configuration_or_503()

    bearer = _bearer_token(request)
    if bearer is not None:
        participant = authenticate_invite_token(bearer, config)
        if participant is None:
            return None
        request.state.pilot_participant_id = participant.participant_id
        return participant

    session_token = request.cookies.get(SESSION_COOKIE_NAME)
    participant = (
        authenticate_session_token(session_token, config) if session_token else None
    )
    if participant is not None:
        request.state.pilot_participant_id = participant.participant_id
    return participant
