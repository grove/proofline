import app


def handle(payload):
    return app.process(payload)


def batch(payloads):
    """Return independent results in order, rejecting any invalid payload."""
    if not isinstance(payloads, list):
        raise ValueError("payloads must be a list")
    return [app.process(payload) for payload in payloads]
