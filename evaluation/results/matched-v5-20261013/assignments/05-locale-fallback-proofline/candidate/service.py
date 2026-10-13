import app


def handle(payload):
    return app.process(payload)


def batch(payloads):
    """Process a list of payloads in order without changing any member."""
    if not isinstance(payloads, list):
        raise ValueError("payloads must be a list")
    return [app.process(payload) for payload in payloads]
