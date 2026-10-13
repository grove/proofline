_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


def _decode_component(component):
    """Decode form text as one strict UTF-8 byte stream."""
    decoded = bytearray()
    index = 0
    while index < len(component):
        character = component[index]
        if character == "%":
            escape = component[index + 1:index + 3]
            if len(escape) != 2 or any(c not in _HEX_DIGITS for c in escape):
                raise ValueError("Malformed percent escape")
            decoded.append(int(escape, 16))
            index += 3
        else:
            decoded.extend((" " if character == "+" else character).encode("utf-8"))
            index += 1
    return decoded.decode("utf-8")


def process(payload):
    """Parse a form query, retaining every value in occurrence order."""
    if not isinstance(payload, dict) or not isinstance(payload.get("query"), str):
        raise TypeError("payload must contain a string query")

    fields = {}
    for segment in payload["query"].split("&"):
        if not segment:
            continue
        name, _, value = segment.partition("=")
        name = _decode_component(name)
        if not name:
            raise ValueError("Field names must not be empty")
        fields.setdefault(name, []).append(_decode_component(value))
    return {"fields": fields}
