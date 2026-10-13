def process(payload):
    """Apply ordered transfers to a copy of the supplied balances."""
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

    final_balances = balances.copy()
    for transfer in transfers:
        if not isinstance(transfer, list) or len(transfer) != 3:
            raise ValueError("each transfer must be [from, to, amount]")
        sender, recipient, amount = transfer
        for name in (sender, recipient):
            if not isinstance(name, str) or not name:
                raise ValueError("account names must be nonempty strings")
            if name not in final_balances:
                raise ValueError("both transfer accounts must exist")
        if not _nonnegative_integer(amount):
            raise ValueError("transfer amounts must be nonnegative integers")
        if final_balances[sender] < amount:
            raise ValueError("insufficient funds")
        final_balances[sender] -= amount
        final_balances[recipient] += amount

    return {"balances": final_balances}


def _nonnegative_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
