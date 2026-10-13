def process(payload):
    """Return the union and covered length of half-open integer intervals."""
    if not isinstance(payload, dict) or not isinstance(payload.get("intervals"), list):
        raise ValueError("payload must contain an intervals list")

    intervals = []
    for interval in payload["intervals"]:
        if not isinstance(interval, list) or len(interval) != 2:
            raise ValueError("each interval must be a two-element list")
        start, end = interval
        if type(start) is not int or type(end) is not int:
            raise ValueError("interval coordinates must be integers")
        if not 0 <= start <= end <= 200:
            raise ValueError("intervals must satisfy 0 <= start <= end <= 200")
        if start < end:
            intervals.append((start, end))

    segments = []
    for start, end in sorted(intervals):
        if segments and start <= segments[-1][1]:
            segments[-1][1] = max(segments[-1][1], end)
        else:
            segments.append([start, end])

    return {
        "segments": segments,
        "covered": sum(end - start for start, end in segments),
    }
