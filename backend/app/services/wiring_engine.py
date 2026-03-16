from __future__ import annotations

import heapq
from collections.abc import Iterable


def _neighbors(point: tuple[int, int], limit: int = 100) -> list[tuple[int, int]]:
    x, y = point
    points = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return [(nx, ny) for nx, ny in points if 0 <= nx <= limit and 0 <= ny <= limit]


def _blocked_points(obstacles: Iterable[dict]) -> set[tuple[int, int]]:
    blocked: set[tuple[int, int]] = set()
    for obstacle in obstacles:
        x1, x2 = sorted([obstacle["x1"], obstacle["x2"]])
        y1, y2 = sorted([obstacle["y1"], obstacle["y2"]])
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                blocked.add((x, y))
    return blocked


def shortest_path(
    start: tuple[int, int], end: tuple[int, int], obstacles: Iterable[dict], limit: int = 100
) -> list[tuple[int, int]]:
    if start == end:
        return [start]

    blocked = _blocked_points(obstacles)
    blocked.discard(start)
    blocked.discard(end)

    heap: list[tuple[int, tuple[int, int]]] = [(0, start)]
    distances: dict[tuple[int, int], int] = {start: 0}
    previous: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

    while heap:
        current_distance, current = heapq.heappop(heap)
        if current == end:
            break
        if current_distance > distances.get(current, float("inf")):
            continue

        for neighbor in _neighbors(current, limit):
            if neighbor in blocked:
                continue
            new_distance = current_distance + 1
            if new_distance < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_distance
                previous[neighbor] = current
                heapq.heappush(heap, (new_distance, neighbor))

    if end not in previous:
        raise ValueError("无法生成路径，请调整设备坐标或障碍物设置")

    path: list[tuple[int, int]] = []
    cursor: tuple[int, int] | None = end
    while cursor is not None:
        path.append(cursor)
        cursor = previous[cursor]
    path.reverse()
    return path
