def process(payload):
    """Apply ordered transfers without changing the caller's data.

    Invalid requests, including an intermediate overdraft, raise ValueError.
    All changes are kept in a fresh balance dictionary until success.
    """
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    balances = payload.get("balances")
    transfers = payload.get("transfers")
    if not isinstance(balances, dict):
        raise ValueError("balances must be an object")
    if not isinstance(transfers, list):
        raise ValueError("transfers must be a list")

    for name, balance in balances.items():
        if not isinstance(name, str) or not name:
            raise ValueError("account names must be nonempty strings")
        if not _nonnegative_integer(balance):
            raise ValueError("balances must be nonnegative integers")

    result = balances.copy()
    for transfer in transfers:
        if not isinstance(transfer, list) or len(transfer) != 3:
            raise ValueError("each transfer must be a three-element list")
        source, destination, amount = transfer
        if (not isinstance(source, str) or not source
                or not isinstance(destination, str) or not destination):
            raise ValueError("account names must be nonempty strings")
        if source not in result or destination not in result:
            raise ValueError("both transfer accounts must exist")
        if not _nonnegative_integer(amount):
            raise ValueError("transfer amounts must be nonnegative integers")
        if amount > result[source]:
            raise ValueError("insufficient funds")
        result[source] -= amount
        result[destination] += amount

    return {"balances": result}


def _nonnegative_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
