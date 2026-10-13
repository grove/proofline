import heapq


def process(payload):
    """Order a graph by dependencies, breaking ties by original node position."""
    if not isinstance(payload, dict):
        raise ValueError("Expected an object with nodes and edges")
    nodes = payload.get("nodes")
    edges = payload.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("nodes and edges must be lists")

    positions = {}
    for index, name in enumerate(nodes):
        if not isinstance(name, str) or not name:
            raise ValueError("Node names must be nonempty strings")
        if name in positions:
            raise ValueError("Node names must be unique")
        positions[name] = index

    successors = [set() for _ in nodes]
    indegrees = [0] * len(nodes)
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2:
            raise ValueError("Each edge must be a two-element list")
        before, after = edge
        if (not isinstance(before, str) or not isinstance(after, str)
                or before not in positions or after not in positions):
            raise ValueError("Edges must reference declared nodes")
        if before == after:
            raise ValueError("Self-loops are not allowed")
        source, target = positions[before], positions[after]
        if target not in successors[source]:
            successors[source].add(target)
            indegrees[target] += 1

    # Reconsider original positions after every emission: a FIFO queue would
    # put a newly eligible early node behind already waiting later nodes.
    ready = [index for index, degree in enumerate(indegrees) if degree == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        index = heapq.heappop(ready)
        order.append(nodes[index])
        for target in successors[index]:
            indegrees[target] -= 1
            if indegrees[target] == 0:
                heapq.heappush(ready, target)
    if len(order) != len(nodes):
        raise ValueError("Graph contains a cycle")
    return {"order": order}
