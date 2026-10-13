from collections import OrderedDict
import math


def _validate_value(value):
    """Validate JSON values without changing them or recursing on containers."""
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
                raise ValueError("value must contain only JSON values")
            continue
        if not isinstance(current, (list, dict)):
            raise ValueError("value must contain only JSON values")
        if id(current) in active:
            raise ValueError("value must not contain circular containers")
        if isinstance(current, dict):
            if any(not isinstance(key, str) for key in current):
                raise ValueError("value object keys must be strings")
            children = current.values()
        else:
            children = current
        active.add(id(current))
        pending.append((current, True))
        pending.extend((child, False) for child in children)


def process(payload):
    """Return the final FIFO cache and its ordered eviction history."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    capacity = payload.get("capacity")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
        raise ValueError("capacity must be a nonnegative integer")
    events = payload.get("events")
    if not isinstance(events, list):
        raise ValueError("events must be a list")

    resident = OrderedDict()
    evicted = []
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("each event must be an object")
        identifier = event.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("each event must have a nonempty string id")
        if "value" not in event:
            raise ValueError("each event must contain value")
        value = event["value"]
        _validate_value(value)

        # Replacing a value preserves its existing insertion position.
        resident[identifier] = value
        if len(resident) > capacity:
            oldest, _ = resident.popitem(last=False)
            evicted.append(oldest)

    return {
        "items": [{"id": identifier, "value": value}
                  for identifier, value in resident.items()],
        "evicted": evicted,
    }
