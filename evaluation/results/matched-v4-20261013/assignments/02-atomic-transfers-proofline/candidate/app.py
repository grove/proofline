def process(payload):
    """Apply ordered transfers to a private copy of validated balances."""
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
        if not isinstance(balance, int) or isinstance(balance, bool) or balance < 0:
            raise ValueError("balances must be nonnegative integers")

    final_balances = balances.copy()
    for transfer in transfers:
        if not isinstance(transfer, list) or len(transfer) != 3:
            raise ValueError("each transfer must be [from, to, amount]")
        source, destination, amount = transfer
        if (not isinstance(source, str) or not source
                or not isinstance(destination, str) or not destination):
            raise ValueError("transfer accounts must be nonempty strings")
        if source not in final_balances or destination not in final_balances:
            raise ValueError("both transfer accounts must exist")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
            raise ValueError("transfer amounts must be nonnegative integers")
        if final_balances[source] < amount:
            raise ValueError("insufficient funds")
        final_balances[source] -= amount
        final_balances[destination] += amount

    return {"balances": final_balances}
