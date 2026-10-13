import app


def handle(payload):
    return app.process(payload)


def batch(payloads):
    """Process a list of independent cache requests in input order."""
    if not isinstance(payloads, list):
        raise ValueError("payloads must be a list")
    return [app.process(payload) for payload in payloads]
