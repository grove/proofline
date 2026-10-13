import heapq


def process(payload):
    """Return dependency order, preferring original positions at every step."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    nodes = payload.get("nodes")
    edges = payload.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("nodes and edges must be lists")

    positions = {}
    for index, name in enumerate(nodes):
        if not isinstance(name, str) or not name:
            raise ValueError("node names must be nonempty strings")
        if name in positions:
            raise ValueError("node names must be unique")
        positions[name] = index

    successors = [[] for _ in nodes]
    dependencies = [0 for _ in nodes]
    seen_edges = set()
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2:
            raise ValueError("each edge must be a two-element list")
        before, after = edge
        if (not isinstance(before, str) or not isinstance(after, str)
                or before not in positions or after not in positions):
            raise ValueError("edges must reference declared nodes")
        if before == after:
            raise ValueError("self-loops are not allowed")
        pair = (positions[before], positions[after])
        if pair not in seen_edges:
            seen_edges.add(pair)
            successors[pair[0]].append(pair[1])
            dependencies[pair[1]] += 1

    ready = [index for index, count in enumerate(dependencies) if count == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        index = heapq.heappop(ready)
        order.append(nodes[index])
        for successor in successors[index]:
            dependencies[successor] -= 1
            if dependencies[successor] == 0:
                heapq.heappush(ready, successor)

    if len(order) != len(nodes):
        raise ValueError("dependencies contain a cycle")
    return {"order": order}
