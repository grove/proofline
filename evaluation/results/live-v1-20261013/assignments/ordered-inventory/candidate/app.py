def process(payload):
    """Apply inventory events in order, rejecting invalid stock transitions."""
    if not isinstance(payload, dict) or set(payload) != {"starting", "events"}:
        raise ValueError("payload must contain starting and events")

    starting = payload["starting"]
    events = payload["events"]
    if not isinstance(starting, dict):
        raise ValueError("starting must be an object")
    if not isinstance(events, list):
        raise ValueError("events must be a list")

    stock = {}
    for sku, quantity in starting.items():
        if not isinstance(sku, str) or not sku:
            raise ValueError("SKU must be a nonempty string")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0:
            raise ValueError("starting quantity must be a nonnegative integer")
        stock[sku] = quantity

    for event in events:
        if not isinstance(event, dict) or set(event) != {"sku", "delta"}:
            raise ValueError("each event must contain sku and delta")
        sku = event["sku"]
        delta = event["delta"]
        if not isinstance(sku, str) or not sku:
            raise ValueError("SKU must be a nonempty string")
        if isinstance(delta, bool) or not isinstance(delta, int):
            raise ValueError("delta must be an integer")
        quantity = stock.get(sku, 0) + delta
        if quantity < 0:
            raise ValueError("event would make stock negative")
        stock[sku] = quantity

    return {"stock": stock}
