"""Security and sensitive data masking for Self-Healing Engine."""
import re
from typing import Any, Dict, List, Union

SENSITIVE_KEY_PATTERNS = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"passwd", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"api[_-]?key", re.IGNORECASE),
    re.compile(r"auth", re.IGNORECASE),
    re.compile(r"bearer", re.IGNORECASE),
    re.compile(r"credential", re.IGNORECASE),
    re.compile(r"cookie", re.IGNORECASE),
    re.compile(r"private[_-]?key", re.IGNORECASE),
    re.compile(r"card[_-]?number", re.IGNORECASE),
    re.compile(r"cvv", re.IGNORECASE),
    re.compile(r"ssn", re.IGNORECASE),
]

SENSITIVE_VALUE_REGEXES = [
    (re.compile(r'(password[\'"]?\s*[:=]\s*[\'"])([^\'"]+)([\'"])', re.IGNORECASE), r'\1******\3'),
    (re.compile(r'(pass[\'"]?\s*[:=]\s*[\'"])([^\'"]+)([\'"])', re.IGNORECASE), r'\1******\3'),
    (re.compile(r'(bearer\s+)[a-zA-Z0-9_\-\.]+', re.IGNORECASE), r'\1******'),
    (re.compile(r'(--password=)[^\s]+', re.IGNORECASE), r'\1******'),
    (re.compile(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'), r'\1'), # emails are okay or can be left
]

def is_sensitive_key(key: str) -> bool:
    """Checks whether a key name represents sensitive information."""
    if not isinstance(key, str):
        return False
    return any(pattern.search(key) for pattern in SENSITIVE_KEY_PATTERNS)

def mask_value(val: Any) -> Any:
    """Masks a sensitive scalar value."""
    if isinstance(val, (str, int, float, bool)):
        return "******"
    return val

def mask_sensitive_data(data: Any) -> Any:
    """
    Recursively traverses dictionaries, lists, and strings to mask sensitive values.
    Returns a sanitized copy safe for logging, reporting, and history persistence.
    """
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if is_sensitive_key(str(k)):
                sanitized[k] = "******"
            else:
                sanitized[k] = mask_sensitive_data(v)
        return sanitized
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(mask_sensitive_data(item) for item in data)
    elif isinstance(data, str):
        text = data
        for pattern, repl in SENSITIVE_VALUE_REGEXES:
            text = pattern.sub(repl, text)
        return text
    return data

