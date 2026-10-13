from collections import OrderedDict
import math


def _validate_value(value):
    """Validate JSON values without changing them, including nested containers."""
    pending = [(value, False)]
    active = set()
    while pending:
        current, leaving = pending.pop()
        if leaving:
            active.remove(id(current))
            continue
        if current is None or isinstance(current, (str, bool, int)):
            continue
        if isinstance(current, float):
            if not math.isfinite(current):
                raise ValueError("value must contain only finite JSON numbers")
            continue
        if not isinstance(current, (list, dict)):
            raise ValueError("value must be a JSON value")
        if id(current) in active:
            raise ValueError("value must not contain circular references")
        if isinstance(current, dict):
            if any(not isinstance(key, str) for key in current):
                raise ValueError("JSON object keys must be strings")
            children = current.values()
        else:
            children = current
        active.add(id(current))
        pending.append((current, True))
        pending.extend((child, False) for child in children)


def process(payload):
    """Apply FIFO inserts and in-place updates to an initially empty cache."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    capacity = payload.get("capacity")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
        raise ValueError("capacity must be a nonnegative integer")
    events = payload.get("events")
    if not isinstance(events, list):
        raise ValueError("events must be a list")

    residents = OrderedDict()
    evicted = []
    for event in events:
        if not isinstance(event, dict) or "id" not in event or "value" not in event:
            raise ValueError("each event must be an object containing id and value")
        record_id = event["id"]
        if not isinstance(record_id, str) or not record_id:
            raise ValueError("event id must be a nonempty string")
        _validate_value(event["value"])
        # Assigning an existing key preserves its original insertion position.
        residents[record_id] = {"id": record_id, "value": event["value"]}
        if len(residents) > capacity:
            oldest_id, _ = residents.popitem(last=False)
            evicted.append(oldest_id)

    return {"items": list(residents.values()), "evicted": evicted}
