import hashlib


def content_hash(type_: str, content: str | bytes) -> str:
    if isinstance(content, bytes):
        payload = content
    else:
        payload = content.strip().encode("utf-8")
    return hashlib.sha256(f"{type_}:".encode() + payload).hexdigest()
