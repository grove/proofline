import app


def handle(payload):
    return app.process(payload)


def batch(payloads):
    """Process each graph in input order, rejecting any invalid member."""
    if not isinstance(payloads, list):
        raise ValueError("Batch payloads must be a list")
    return [app.process(payload) for payload in payloads]
