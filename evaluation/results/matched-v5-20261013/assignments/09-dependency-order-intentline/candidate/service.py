import app


def handle(payload):
    return app.process(payload)


def batch(payloads):
    """Process a list of graphs in input order without modifying them."""
    if not isinstance(payloads, list):
        raise ValueError("payloads must be a list")
    return [app.process(payload) for payload in payloads]
