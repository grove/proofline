import app


def handle(payload):
    return app.process(payload)


def batch(payloads):
    """Process every payload in order, rejecting the entire invalid batch."""
    if not isinstance(payloads, list):
        raise ValueError("payloads must be a list")
    return [app.process(payload) for payload in payloads]
