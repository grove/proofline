def process(payload):
    """Apply an ordered set of transfers without changing the input."""
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
        if not _is_nonnegative_integer(balance):
            raise ValueError("balances must be nonnegative integers")

    final_balances = balances.copy()
    for transfer in transfers:
        if not isinstance(transfer, list) or len(transfer) != 3:
            raise ValueError("each transfer must be [from, to, amount]")
        source, destination, amount = transfer
        if (not isinstance(source, str) or not source
                or not isinstance(destination, str) or not destination):
            raise ValueError("account names must be nonempty strings")
        if source not in final_balances or destination not in final_balances:
            raise ValueError("both transfer accounts must exist")
        if not _is_nonnegative_integer(amount):
            raise ValueError("transfer amounts must be nonnegative integers")
        if final_balances[source] < amount:
            raise ValueError("insufficient funds")
        final_balances[source] -= amount
        final_balances[destination] += amount

    return {"balances": final_balances}


def _is_nonnegative_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
