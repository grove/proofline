import re


def process(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("titles"), list):
        raise ValueError("payload must contain a titles list")

    slugs = []
    used = set()
    next_suffix = {}
    for title in payload["titles"]:
        if not isinstance(title, str):
            raise ValueError("each title must be a string")
        base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        if not base:
            raise ValueError("each title must normalize to a nonempty slug")

        slug = base
        if slug in used:
            suffix = next_suffix.get(base, 2)
            while f"{base}-{suffix}" in used:
                suffix += 1
            slug = f"{base}-{suffix}"
            next_suffix[base] = suffix + 1
        used.add(slug)
        slugs.append(slug)

    return {"slugs": slugs}
