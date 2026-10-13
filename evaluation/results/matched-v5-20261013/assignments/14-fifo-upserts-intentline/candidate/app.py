"""Validated FIFO record-cache processing."""

from collections import OrderedDict
import math


def _copy_json_value(value, active=None):
    """Copy a JSON value without modifying the caller's containers."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("value must be a JSON value")
        return value
    if not isinstance(value, (list, dict)):
        raise ValueError("value must be a JSON value")

    if active is None:
        active = set()
    identity = id(value)
    if identity in active:
        raise ValueError("value must not contain cycles")
    active.add(identity)
    try:
        if isinstance(value, list):
            return [_copy_json_value(item, active) for item in value]
        if any(not isinstance(key, str) for key in value):
            raise ValueError("JSON object keys must be strings")
        return {key: _copy_json_value(item, active)
                for key, item in value.items()}
    finally:
        active.remove(identity)


def process(payload):
    """Return final FIFO records and ordered evictions for one payload."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if "capacity" not in payload or "events" not in payload:
        raise ValueError("payload must contain capacity and events")
    capacity = payload["capacity"]
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 0:
        raise ValueError("capacity must be a nonnegative integer")
    events = payload["events"]
    if not isinstance(events, list):
        raise ValueError("events must be a list")

    resident = OrderedDict()
    evicted = []
    for event in events:
        if not isinstance(event, dict) or "id" not in event or "value" not in event:
            raise ValueError("each event must be an object containing id and value")
        identifier = event["id"]
        if not isinstance(identifier, str) or not identifier:
            raise ValueError("event id must be a nonempty string")
        value = _copy_json_value(event["value"])
        # Replacing a value preserves the resident ID's insertion position.
        resident[identifier] = {"id": identifier, "value": value}
        if len(resident) > capacity:
            oldest, _ = resident.popitem(last=False)
            evicted.append(oldest)

    return {"items": list(resident.values()), "evicted": evicted}
