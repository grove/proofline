def _nonnegative_integer(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def process(payload):
    """Apply ordered transfers to a private copy, or reject with ValueError."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if "balances" not in payload or "transfers" not in payload:
        raise ValueError("payload requires balances and transfers")

    balances = payload["balances"]
    transfers = payload["transfers"]
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
        if (
            not isinstance(sender, str) or not sender
            or not isinstance(recipient, str) or not recipient
        ):
            raise ValueError("transfer accounts must be nonempty strings")
        if sender not in final_balances or recipient not in final_balances:
            raise ValueError("both transfer accounts must exist")
        if not _nonnegative_integer(amount):
            raise ValueError("transfer amounts must be nonnegative integers")
        # Check before debit/credit, even when sender and recipient are equal.
        if final_balances[sender] < amount:
            raise ValueError("insufficient funds")
        final_balances[sender] -= amount
        final_balances[recipient] += amount

    return {"balances": final_balances}
