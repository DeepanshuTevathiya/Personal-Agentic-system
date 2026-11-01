import logging
import os
import re
import unicodedata
from functools import lru_cache

logger = logging.getLogger(__name__)

SAFE_RESPONSE = (
    "I can’t provide that response. "
    "Please try asking about your health or productivity."
)

SHINGLE_SIZE = 7

SECRET_PATTERNS = (
    re.compile(r"\bsb_(?:secret|publishable)_[\w\-]{10,}"),
    re.compile(r"\bsk-[\w\-]{16,}"),
    re.compile(r"\bgsk_[A-Za-z0-9]{20,}"),
    re.compile(r"\blsv2_(?:pt|sk)_[A-Za-z0-9_]{16,}"),
    re.compile(r"\bAIza[\w\-]{30,}"),
    re.compile(r"\beyJ[\w\-]{10,}\.[\w\-]{10,}\.[\w\-]{10,}"),
    re.compile(r"\bBearer\s+[\w\-\.]{20,}"),
    re.compile(r"\bpostgres(?:ql)?://[^\s:@/]+:[^\s@/]+@", re.IGNORECASE),
    re.compile(
        r"\b(?:api[_ \-]?key|secret[_ \-]?key|access[_ \-]?token|"
        r"service[_ \-]?role|password)\s*[:=]\s*\S+",
        re.IGNORECASE,
    ),
)

_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"), None)
_SENSITIVE_ENV_NAME = re.compile(
    r"KEY|SECRET|TOKEN|PASSWORD|DATABASE_URL|DB_URL|CONNECTION", re.IGNORECASE
)
_PROMPT_SHINGLES: frozenset[str] = frozenset()


def _words(text: str) -> list[str]:
    text = unicodedata.normalize("NFKC", text).translate(_INVISIBLE).casefold()
    return re.sub(r"[^\w\s]", " ", text).split()


def _shingles(words: list[str]) -> set[str]:
    return {
        " ".join(words[i:i + SHINGLE_SIZE])
        for i in range(len(words) - SHINGLE_SIZE + 1)
    }


def register_prompts(*prompts: str) -> None:
    """Call once at startup with the real prompt strings."""
    global _PROMPT_SHINGLES
    found: set[str] = set()
    for prompt in prompts:
        found |= _shingles(_words(prompt))
    _PROMPT_SHINGLES = frozenset(found)


@lru_cache(maxsize=1)
def _env_secrets() -> tuple[str, ...]:
    return tuple(
        v for k, v in os.environ.items()
        if _SENSITIVE_ENV_NAME.search(k) and len(v) >= 8
    )


def check_output(response: str) -> str | None:
    if any(secret in response for secret in _env_secrets()):
        return "env_secret"
    if any(p.search(response) for p in SECRET_PATTERNS):
        return "secret_pattern"
    if _PROMPT_SHINGLES and not _PROMPT_SHINGLES.isdisjoint(
        _shingles(_words(response))
    ):
        return "prompt_leak"
    return None


def filter_sensitive_output(response: str) -> str:
    reason = check_output(response)
    if reason is None:
        return response
    logger.warning("Blocked model output: %s", reason)
    return SAFE_RESPONSE