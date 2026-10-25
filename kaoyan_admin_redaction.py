"""Preserve field names while removing credentials from raw and nested records."""
import base64
import json
import re

MASK = "[••••掩码脱敏 / REDACTED]"
SECRET_KEYS = {
    "password", "passcode", "oldpassword", "newpassword", "oldpasscode", "newpasscode",
    "passcodehash", "passcodesalt", "passwordhash", "passwordsalt", "tokensecret",
    "token", "accesstoken", "refreshtoken", "authorization", "cookie", "setcookie",
    "apikey", "secret", "clientsecret",
}


def sensitive(name):
    return re.sub(r"[^a-z0-9]", "", str(name).lower()) in SECRET_KEYS


def redact(value):
    if isinstance(value, dict):
        out = {}
        # Cluster receipts contain a base64 HTTP response body, including login tokens.
        envelope = "body" in value and ("code" in value or "headers" in value)
        for key, item in value.items():
            if sensitive(key):
                out[key] = MASK if item is not None else None
            elif envelope and key == "body" and isinstance(item, str):
                try:
                    decoded = base64.b64decode(item, validate=True).decode("utf-8")
                    out[key] = redact(json.loads(decoded))
                except (ValueError, UnicodeError, RecursionError):
                    out[key] = MASK + " (encoded response)"
            else:
                out[key] = redact(item)
        return out
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str) and value.lstrip().startswith(("{", "[")):
        try:
            return json.dumps(redact(json.loads(value)), ensure_ascii=False)
        except (ValueError, RecursionError):
            return MASK + " (invalid structured payload)"
    if isinstance(value, bytes):
        return {"encoding": "base64", "value": base64.b64encode(value).decode()}
    return value


def mask_sensitive_row_fields(table_name, row_dict):
    # The rule applies to every table, including WAL payloads and replay receipts.
    return redact(dict(row_dict))
