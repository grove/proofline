def _is_nonnegative_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_name(value):
    return isinstance(value, str) and bool(value)


def process(payload):
    """Apply ordered transfers atomically, without modifying the payload."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    balances = payload.get("balances")
    transfers = payload.get("transfers")
    if not isinstance(balances, dict):
        raise ValueError("balances must be an object")
    if not isinstance(transfers, list):
        raise ValueError("transfers must be a list")
    for name, balance in balances.items():
        if not _is_name(name):
            raise ValueError("account names must be nonempty strings")
        if not _is_nonnegative_integer(balance):
            raise ValueError("balances must be nonnegative integers")

    result = balances.copy()
    for transfer in transfers:
        if not isinstance(transfer, list) or len(transfer) != 3:
            raise ValueError("each transfer must be a three-element list")
        source, destination, amount = transfer
        if not _is_name(source) or not _is_name(destination):
            raise ValueError("account names must be nonempty strings")
        if not _is_nonnegative_integer(amount):
            raise ValueError("transfer amounts must be nonnegative integers")
        if source not in result or destination not in result:
            raise ValueError("both transfer accounts must exist")
        if result[source] < amount:
            raise ValueError("insufficient funds")
        result[source] -= amount
        result[destination] += amount

    return {"balances": result}
