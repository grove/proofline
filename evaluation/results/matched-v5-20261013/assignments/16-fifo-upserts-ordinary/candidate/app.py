from collections import OrderedDict
import math


def _validate_json_value(value):
    """Reject non-JSON values, including circular containers."""
    pending = [(value, False)]
    ancestors = set()
    while pending:
        current, leaving = pending.pop()
        if leaving:
            ancestors.remove(id(current))
            continue
        if current is None or isinstance(current, (str, bool, int)):
            continue
        if isinstance(current, float):
            if not math.isfinite(current):
                raise ValueError("value must be valid JSON")
            continue
        if not isinstance(current, (list, dict)):
            raise ValueError("value must be valid JSON")

        identity = id(current)
        if identity in ancestors:
            raise ValueError("value must not contain circular containers")
        ancestors.add(identity)
        pending.append((current, True))
        if isinstance(current, dict):
            if any(not isinstance(key, str) for key in current):
                raise ValueError("JSON object keys must be strings")
            children = current.values()
        else:
            children = current
        pending.extend((child, False) for child in children)


def process(payload):
    """Apply events to a FIFO cache without changing the input."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    capacity = payload.get("capacity")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
        raise ValueError("capacity must be a nonnegative integer")
    events = payload.get("events")
    if not isinstance(events, list):
        raise ValueError("events must be a list")

    items = OrderedDict()
    evicted = []
    for event in events:
        if not isinstance(event, dict) or "id" not in event or "value" not in event:
            raise ValueError("each event must be an object containing id and value")
        identifier = event["id"]
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("event id must be a nonempty string")
        _validate_json_value(event["value"])

        # Assigning an existing key preserves its original FIFO position.
        items[identifier] = {"id": identifier, "value": event["value"]}
        if len(items) > capacity:
            oldest, _ = items.popitem(last=False)
            evicted.append(oldest)

    return {"items": list(items.values()), "evicted": evicted}
