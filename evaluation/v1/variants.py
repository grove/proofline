"""Trusted local control candidates, NEVER copied to coding-agent workspaces.

These are finite, independently graded examples, not a source of expected answers.
Generated candidates contain only the selected implementation and public wrappers.
"""
import inspect
import re
from urllib.parse import unquote_plus


def ref_slugs(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("titles"), list):
        raise ValueError("titles list required")
    used, output = set(), []
    for title in payload["titles"]:
        if not isinstance(title, str):
            raise ValueError("title is not text")
        base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        if not base:
            raise ValueError("empty normalized title")
        name, suffix = base, 2
        while name in used:
            name = f"{base}-{suffix}"
            suffix += 1
        used.add(name)
        output.append(name)
    return {"slugs": output}


def alt_slugs(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("titles"), list):
        raise ValueError("titles list required")
    seen, result = set(), []
    for title in payload["titles"]:
        if not isinstance(title, str):
            raise ValueError("title must be text")
        pieces, fragment = [], ""
        for char in title.lower():
            if char in "abcdefghijklmnopqrstuvwxyz0123456789":
                fragment += char
            elif fragment:
                pieces.append(fragment)
                fragment = ""
        if fragment:
            pieces.append(fragment)
        base = "-".join(pieces)
        if not base:
            raise ValueError("slug cannot be empty")
        proposed = base
        i = 2
        while proposed in seen:
            proposed = base + "-" + str(i)
            i += 1
        seen.add(proposed)
        result.append(proposed)
    return {"slugs": result}


def bad_slugs(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("titles"), list):
        raise ValueError("titles list required")
    counts, output = {}, []
    for title in payload["titles"]:
        if not isinstance(title, str):
            raise ValueError("title is not text")
        base = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
        if not base:
            raise ValueError("empty title")
        counts[base] = counts.get(base, 0) + 1
        output.append(base if counts[base] == 1 else base + "-" + str(counts[base]))
    return {"slugs": output}


def ref_inventory(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("starting"), dict) or not isinstance(payload.get("events"), list):
        raise ValueError("starting and events required")
    stock = {}
    for sku, quantity in payload["starting"].items():
        if not isinstance(sku, str) or not sku or type(quantity) is not int or quantity < 0:
            raise ValueError("invalid initial quantity")
        stock[sku] = quantity
    for event in payload["events"]:
        if not isinstance(event, dict):
            raise ValueError("invalid event")
        sku, delta = event.get("sku"), event.get("delta")
        if not isinstance(sku, str) or not sku or type(delta) is not int:
            raise ValueError("invalid event contents")
        stock[sku] = stock.get(sku, 0) + delta
        if stock[sku] < 0:
            raise ValueError("negative intermediate stock")
    return {"stock": dict(sorted(stock.items()))}


def alt_inventory(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("starting"), dict) or not isinstance(payload.get("events"), list):
        raise ValueError("starting and events required")
    base = dict(payload["starting"])
    for sku, number in base.items():
        if not isinstance(sku, str) or not sku or type(number) is not int or number < 0:
            raise ValueError("invalid initial stock")
    events = []
    for row in payload["events"]:
        if not isinstance(row, dict) or not isinstance(row.get("sku"), str) or not row["sku"] or type(row.get("delta")) is not int:
            raise ValueError("invalid event")
        events.append((row["sku"], row["delta"]))
        sku = row["sku"]
        intermediate = base.get(sku, 0) + sum(delta for name, delta in events if name == sku)
        if intermediate < 0:
            raise ValueError("transient stock below zero")
    result = dict(base)
    for sku, delta in events:
        result[sku] = result.get(sku, 0) + delta
    return {"stock": dict(sorted(result.items()))}


def bad_inventory(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("starting"), dict) or not isinstance(payload.get("events"), list):
        raise ValueError("starting and events required")
    stock = {}
    for sku, quantity in payload["starting"].items():
        if not isinstance(sku, str) or not sku or type(quantity) is not int or quantity < 0:
            raise ValueError("invalid initial stock")
        stock[sku] = quantity
    for event in payload["events"]:
        if not isinstance(event, dict) or not isinstance(event.get("sku"), str) or not event["sku"] or type(event.get("delta")) is not int:
            raise ValueError("invalid event")
        stock[event["sku"]] = stock.get(event["sku"], 0) + event["delta"]
    if any(v < 0 for v in stock.values()):
        raise ValueError("negative final stock")
    return {"stock": dict(sorted(stock.items()))}


def ref_intervals(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("intervals"), list):
        raise ValueError("intervals required")
    intervals = []
    for pair in payload["intervals"]:
        if not isinstance(pair, list) or len(pair) != 2 or any(type(v) is not int for v in pair):
            raise ValueError("invalid interval")
        a, b = pair
        if not 0 <= a <= b <= 200:
            raise ValueError("out-of-range interval")
        if a < b:
            intervals.append((a, b))
    merged = []
    for a, b in sorted(intervals):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(b, merged[-1][1])
        else:
            merged.append([a, b])
    return {"segments": merged, "covered": sum(b - a for a, b in merged)}


def alt_intervals(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("intervals"), list):
        raise ValueError("intervals required")
    occupied = set()
    for pair in payload["intervals"]:
        if not isinstance(pair, list) or len(pair) != 2 or any(type(v) is not int for v in pair):
            raise ValueError("invalid interval")
        a, b = pair
        if not 0 <= a <= b <= 200:
            raise ValueError("out-of-range interval")
        occupied.update(range(a, b))
    ordered = sorted(occupied)
    if not ordered:
        return {"segments": [], "covered": 0}
    start, previous = ordered[0], ordered[0]
    segments = []
    for position in ordered[1:]:
        if position > previous + 1:
            segments.append([start, previous + 1])
            start = position
        previous = position
    segments.append([start, previous + 1])
    return {"segments": segments, "covered": len(ordered)}


def bad_intervals(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("intervals"), list):
        raise ValueError("intervals required")
    pairs = []
    for pair in payload["intervals"]:
        if not isinstance(pair, list) or len(pair) != 2 or any(type(v) is not int for v in pair):
            raise ValueError("invalid interval")
        a, b = pair
        if not 0 <= a <= b <= 200:
            raise ValueError("out-of-range interval")
        if a < b:
            pairs.append((a, b))
    merged = []
    for a, b in sorted(pairs):
        if merged and a < merged[-1][1]:  # Incorrectly separates touching intervals.
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return {"segments": merged, "covered": sum(b - a for a, b in merged)}


def ref_forms(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("query"), str):
        raise ValueError("query required")
    fields = {}
    for part in payload["query"].split("&"):
        if not part:
            continue
        name, separator, value = part.partition("=")
        def decode(s):
            if re.search(r"%(?![a-fA-F0-9]{2})", s):
                raise ValueError("invalid percent escape")
            return unquote_plus(s, encoding="utf-8", errors="strict")
        name = decode(name)
        value = decode(value if separator else "")
        if not name:
            raise ValueError("empty field name")
        fields.setdefault(name, []).append(value)
    return {"fields": fields}


def alt_forms(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("query"), str):
        raise ValueError("query required")
    def decode(text):
        text = text.replace("+", " ")
        data = bytearray()
        at = 0
        while at < len(text):
            if text[at] == "%":
                if at + 2 >= len(text) or any(c not in "0123456789abcdefABCDEF" for c in text[at + 1:at + 3]):
                    raise ValueError("invalid percent escape")
                data.append(int(text[at + 1:at + 3], 16))
                at += 3
            else:
                data.extend(text[at].encode("utf-8"))
                at += 1
        return data.decode("utf-8", errors="strict")
    result = {}
    for item in payload["query"].split("&"):
        if not item:
            continue
        components = item.split("=", 1)
        name = decode(components[0])
        value = decode(components[1] if len(components) == 2 else "")
        if not name:
            raise ValueError("empty key")
        result.setdefault(name, []).append(value)
    return {"fields": result}


def bad_forms(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("query"), str):
        raise ValueError("query required")
    result = {}
    for item in payload["query"].split("&"):
        if not item:
            continue
        name, _, value = item.partition("=")
        if re.search(r"%(?![a-fA-F0-9]{2})", name + "&" + value):
            raise ValueError("invalid escape")
        name = unquote_plus(name, encoding="utf-8", errors="strict")
        value = unquote_plus(value, encoding="utf-8", errors="strict")
        if not name:
            raise ValueError("empty name")
        result[name] = [value]  # Incorrectly discards earlier values.
    return {"fields": result}


def ref_allocations(payload):
    if not isinstance(payload, dict):
        raise ValueError("object required")
    units, weights = payload.get("units"), payload.get("weights")
    if type(units) is not int or not 0 <= units <= 1000 or not isinstance(weights, list) or not 1 <= len(weights) <= 10 or any(type(x) is not int or x < 0 for x in weights) or sum(weights) == 0:
        raise ValueError("invalid allocation request")
    total = sum(weights)
    shares = [units * weight // total for weight in weights]
    rem = [units * weight % total for weight in weights]
    missing = units - sum(shares)
    for index in sorted(range(len(weights)), key=lambda i: (-rem[i], i))[:missing]:
        shares[index] += 1
    return {"allocations": shares}


def alt_allocations(payload):
    if not isinstance(payload, dict):
        raise ValueError("object required")
    units, weights = payload.get("units"), payload.get("weights")
    if type(units) is not int or not 0 <= units <= 1000 or not isinstance(weights, list) or not 1 <= len(weights) <= 10 or any(type(x) is not int or x < 0 for x in weights) or not any(weights):
        raise ValueError("invalid allocation request")
    denominator = sum(weights)
    result = [divmod(units * number, denominator)[0] for number in weights]
    pending = set(range(len(weights)))
    for _ in range(units - sum(result)):
        best = max(pending, key=lambda i: (units * weights[i] % denominator, -i))
        result[best] += 1
        pending.remove(best)
    return {"allocations": result}


def bad_allocations(payload):
    if not isinstance(payload, dict):
        raise ValueError("object required")
    units, weights = payload.get("units"), payload.get("weights")
    if type(units) is not int or not 0 <= units <= 1000 or not isinstance(weights, list) or not 1 <= len(weights) <= 10 or any(type(x) is not int or x < 0 for x in weights) or sum(weights) == 0:
        raise ValueError("invalid allocation request")
    total = sum(weights)
    result = [units * w // total for w in weights]
    rem = [units * w % total for w in weights]
    for i in sorted(range(len(weights)), key=lambda j: (-rem[j], -j))[:units - sum(result)]:
        result[i] += 1  # Incorrectly breaks ties by later index.
    return {"allocations": result}


def ref_islands(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("grid"), list):
        raise ValueError("grid required")
    grid = payload["grid"]
    if not grid or any(not isinstance(row, str) for row in grid) or not grid[0] or any(len(row) != len(grid[0]) or set(row) - {".", "#"} for row in grid):
        raise ValueError("invalid grid")
    height, width = len(grid), len(grid[0])
    visited, sizes = set(), []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != "#" or (row, col) in visited:
                continue
            visited.add((row, col))
            queue = [(row, col)]
            size = 0
            while queue:
                r, c = queue.pop()
                size += 1
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] == "#" and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            sizes.append(size)
    sizes.sort(reverse=True)
    return {"count": len(sizes), "sizes": sizes}


def alt_islands(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("grid"), list):
        raise ValueError("grid required")
    grid = payload["grid"]
    if not grid or any(not isinstance(row, str) for row in grid) or not grid[0] or any(len(row) != len(grid[0]) or set(row) - {".", "#"} for row in grid):
        raise ValueError("invalid grid")
    height, width = len(grid), len(grid[0])
    parent = {}
    def root(p):
        while parent[p] != p:
            parent[p] = parent[parent[p]]
            p = parent[p]
        return p
    for r in range(height):
        for c in range(width):
            if grid[r][c] == "#":
                key = (r, c)
                parent[key] = key
                for adjacent in ((r - 1, c), (r, c - 1)):
                    if adjacent in parent:
                        parent[root(key)] = root(adjacent)
    sizes = {}
    for node in parent:
        representative = root(node)
        sizes[representative] = sizes.get(representative, 0) + 1
    ordered = sorted(sizes.values(), reverse=True)
    return {"count": len(ordered), "sizes": ordered}


def bad_islands(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("grid"), list):
        raise ValueError("grid required")
    grid = payload["grid"]
    if not grid or any(not isinstance(row, str) for row in grid) or not grid[0] or any(len(row) != len(grid[0]) or set(row) - {".", "#"} for row in grid):
        raise ValueError("invalid grid")
    visited, sizes = set(), []
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] != "#" or (r, c) in visited:
                continue
            todo, size = [(r, c)], 0
            visited.add((r, c))
            while todo:
                y, x = todo.pop()
                size += 1
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):  # Incorrectly allows diagonal contact.
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < len(grid) and 0 <= nx < len(grid[0]) and grid[ny][nx] == "#" and (ny, nx) not in visited:
                            visited.add((ny, nx))
                            todo.append((ny, nx))
            sizes.append(size)
    sizes.sort(reverse=True)
    return {"count": len(sizes), "sizes": sizes}


FUNCTIONS = {
    "collision-slugs": (ref_slugs, alt_slugs, bad_slugs),
    "ordered-inventory": (ref_inventory, alt_inventory, bad_inventory),
    "half-open-union": (ref_intervals, alt_intervals, bad_intervals),
    "form-multimap": (ref_forms, alt_forms, bad_forms),
    "largest-remainder": (ref_allocations, alt_allocations, bad_allocations),
    "four-way-islands": (ref_islands, alt_islands, bad_islands),
}


def candidate_code(task_id, variant):
    if variant not in {"reference", "alternative", "defective"}:
        raise ValueError("Unknown control variant")
    method = FUNCTIONS[task_id][("reference", "alternative", "defective").index(variant)]
    return ("import re\nfrom urllib.parse import unquote_plus\n\n"
            + inspect.getsource(method)
            + "\nprocess = " + method.__name__ + "\n")
