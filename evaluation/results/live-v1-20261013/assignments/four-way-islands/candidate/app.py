def process(payload):
    """Count four-way connected land components in a rectangular grid."""
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object containing a grid")
    grid = payload.get("grid")
    if not isinstance(grid, list) or not grid:
        raise ValueError("grid must be a nonempty list of strings")
    if not all(isinstance(row, str) for row in grid):
        raise ValueError("grid rows must be strings")

    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    if any(cell not in ".#" for row in grid for cell in row):
        raise ValueError("grid may contain only '.' and '#'")

    height = len(grid)
    visited = [bytearray(width) for _ in grid]
    sizes = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != "#" or visited[row][col]:
                continue
            visited[row][col] = 1
            pending = [(row, col)]
            size = 0
            while pending:
                current_row, current_col = pending.pop()
                size += 1
                for next_row, next_col in (
                    (current_row - 1, current_col),
                    (current_row + 1, current_col),
                    (current_row, current_col - 1),
                    (current_row, current_col + 1),
                ):
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and grid[next_row][next_col] == "#"
                        and not visited[next_row][next_col]
                    ):
                        visited[next_row][next_col] = 1
                        pending.append((next_row, next_col))
            sizes.append(size)

    sizes.sort(reverse=True)
    return {"count": len(sizes), "sizes": sizes}
