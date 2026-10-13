def process(payload):
    """Allocate units proportionally using the largest-remainder method."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    units = payload.get("units")
    weights = payload.get("weights")
    if type(units) is not int or not 0 <= units <= 1000:
        raise ValueError("units must be an integer between 0 and 1000")
    if not isinstance(weights, list) or not 1 <= len(weights) <= 10:
        raise ValueError("weights must be a list of length 1 to 10")
    if any(type(weight) is not int or weight < 0 for weight in weights):
        raise ValueError("weights must contain nonnegative integers")

    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("weights must contain at least one positive integer")

    quotients = [divmod(units * weight, total_weight) for weight in weights]
    allocations = [quotient for quotient, _ in quotients]
    remaining = units - sum(allocations)
    order = sorted(range(len(weights)), key=lambda index: (-quotients[index][1], index))
    for index in order[:remaining]:
        allocations[index] += 1

    return {"allocations": allocations}
