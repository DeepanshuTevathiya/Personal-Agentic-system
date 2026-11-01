import re
import unicodedata

_INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"), None)

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(_INVISIBLE).lower()
    text = re.sub(r"['’`]", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()

_EXTRACT = (
    r"(?:show|reveal|print|tell|give|share|display|output|repeat|leak|dump|"
    r"expose|read|send|list|whats|what is|what are)"
)
_PROTECTED = (
    r"(?:system prompt|system message|system instructions|initial prompt|"
    r"hidden prompt|hidden instructions|developer message|developer prompt|"
    r"your prompt|your instructions|your rules|your guidelines|"
    r"api keys?|secret keys?|access tokens?|service role|env file|"
    r"environment variables|credentials)"
)

RULES = [
    ("extract_protected", re.compile(
        rf"\b{_EXTRACT}\b(?:\s+\w+){{0,5}}?\s+{_PROTECTED}\b"), False),
    ("override_instructions", re.compile(
        r"\b(?:ignore|disregard|forget|override|bypass)\b(?:\s+\w+){0,3}?\s+"
        r"(?:previous|prior|above|earlier|original|initial|your|system)\s+"
        r"(?:system\s+)?(?:instructions|rules|prompts?|guidelines|"
        r"restrictions|directives|guardrails)\b"), False),
    ("jailbreak_mode", re.compile(
        r"\b(?:developer mode|jailbreak|jailbroken|do anything now|dan mode)\b|"
        r"\bpretend\b(?:\s+\w+){0,4}\s+(?:no|without)\s+"
        r"(?:restrictions|rules|limits|guardrails)\b"), False),
    ("other_users", re.compile(
        r"\b(?:other|another|different)\s+users?\b|\buser\s*id\b"), False),
    ("fake_role_marker", re.compile(
        r"<\|?\s*(?:system|im_start|im_end)|\[\s*(?:system|inst)\s*\]|"
        r"###\s*(?:system|instruction)"), True),
]

def is_prompt_injection(message: str) -> str | None:
    raw = message.lower()
    norm = normalize(message)
    for name, pattern, use_raw in RULES:
        if pattern.search(raw if use_raw else norm):
            return name

# def is_prompt_injection(message: str) -> bool:
#     normalized_message = " ".join(message.lower().split())

#     return any(
#         re.search(pattern, normalized_message) for pattern in PROMPT_INJECTION_PATTERNS
#     )