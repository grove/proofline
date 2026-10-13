import app


def handle(payload):
    return app.process(payload)


def batch(payloads):
    """Return transfer results in input order, rejecting invalid batches."""
    if not isinstance(payloads, list):
        raise ValueError("payloads must be a list")
    return [app.process(payload) for payload in payloads]
