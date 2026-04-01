from __future__ import annotations

import heapq
import random
import math
from collections.abc import Iterable
from enum import Enum


class Path3DAlgorithm(Enum):
    """3D路径算法类型"""
    ASTAR_3D = "astar_3d"
    DIJKSTRA_3D = "dijkstra_3d"


def _neighbors_3d(point: tuple[int, int, int], limit: int = 100) -> list[tuple[int, int, int]]:
    """
    获取3D空间中的相邻点（6个方向）
    """
    x, y, z = point
    points = [
        (x + 1, y, z), (x - 1, y, z),
        (x, y + 1, z), (x, y - 1, z),
        (x, y, z + 1), (x, y, z - 1)
    ]
    return [(nx, ny, nz) for nx, ny, nz in points 
            if 0 <= nx <= limit and 0 <= ny <= limit and 0 <= nz <= limit]


def _blocked_points_3d(obstacles: Iterable[dict]) -> set[tuple[int, int, int]]:
    """
    解析3D障碍物区域
    障碍物格式: {"x1": int, "y1": int, "z1": int, "x2": int, "y2": int, "z2": int}
    """
    blocked: set[tuple[int, int, int]] = set()
    for obstacle in obstacles:
        x1, x2 = sorted([obstacle.get("x1", 0), obstacle.get("x2", 0)])
        y1, y2 = sorted([obstacle.get("y1", 0), obstacle.get("y2", 0)])
        z1, z2 = sorted([obstacle.get("z1", 0), obstacle.get("z2", 0)])
        
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                for z in range(z1, z2 + 1):
                    blocked.add((x, y, z))
    return blocked


def _manhattan_distance_3d(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    """3D曼哈顿距离"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])


def _euclidean_distance_3d(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """3D欧几里得距离"""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _reconstruct_path_3d(previous: dict, end: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    """重建3D路径"""
    path: list[tuple[int, int, int]] = []
    cursor: tuple[int, int, int] | None = end
    while cursor is not None:
        path.append(cursor)
        cursor = previous.get(cursor)
    path.reverse()
    return path


def astar_path_3d(
    start: tuple[int, int, int], 
    end: tuple[int, int, int], 
    obstacles: Iterable[dict], 
    limit: int = 100
) -> list[tuple[int, int, int]]:
    """
    3D A*算法寻路
    """
    if start == end:
        return [start]

    blocked = _blocked_points_3d(obstacles)
    blocked.discard(start)
    blocked.discard(end)

    heap: list[tuple[int, int, tuple[int, int, int]]] = [(0, 0, start)]
    g_scores: dict[tuple[int, int, int], int] = {start: 0}
    f_scores: dict[tuple[int, int, int], int] = {start: _manhattan_distance_3d(start, end)}
    previous: dict[tuple[int, int, int], tuple[int, int, int] | None] = {start: None}

    while heap:
        current_f, current_g, current = heapq.heappop(heap)
        
        if current == end:
            break
            
        if current_f > f_scores.get(current, float("inf")):
            continue

        for neighbor in _neighbors_3d(current, limit):
            if neighbor in blocked:
                continue
                
            tentative_g = current_g + 1
            
            if tentative_g < g_scores.get(neighbor, float("inf")):
                previous[neighbor] = current
                g_scores[neighbor] = tentative_g
                f_scores[neighbor] = tentative_g + _manhattan_distance_3d(neighbor, end)
                heapq.heappush(heap, (f_scores[neighbor], g_scores[neighbor], neighbor))

    if end not in previous:
        raise ValueError("无法生成3D路径，请调整设备坐标或障碍物设置")

    return _reconstruct_path_3d(previous, end)


def dijkstra_path_3d(
    start: tuple[int, int, int], 
    end: tuple[int, int, int], 
    obstacles: Iterable[dict], 
    limit: int = 100
) -> list[tuple[int, int, int]]:
    """
    3D Dijkstra算法寻路
    """
    if start == end:
        return [start]

    blocked = _blocked_points_3d(obstacles)
    blocked.discard(start)
    blocked.discard(end)

    heap: list[tuple[int, tuple[int, int, int]]] = [(0, start)]
    distances: dict[tuple[int, int, int], int] = {start: 0}
    previous: dict[tuple[int, int, int], tuple[int, int, int] | None] = {start: None}

    while heap:
        current_distance, current = heapq.heappop(heap)
        
        if current == end:
            break
            
        if current_distance > distances.get(current, float("inf")):
            continue

        for neighbor in _neighbors_3d(current, limit):
            if neighbor in blocked:
                continue
                
            new_distance = current_distance + 1
            
            if new_distance < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_distance
                previous[neighbor] = current
                heapq.heappush(heap, (new_distance, neighbor))

    if end not in previous:
        raise ValueError("无法生成3D路径，请调整设备坐标或障碍物设置")

    return _reconstruct_path_3d(previous, end)


def shortest_path_3d(
    start: tuple[int, int, int], 
    end: tuple[int, int, int], 
    obstacles: Iterable[dict], 
    algorithm: Path3DAlgorithm = Path3DAlgorithm.ASTAR_3D,
    limit: int = 100
) -> list[tuple[int, int, int]]:
    """
    3D最短路径计算入口函数
    """
    if algorithm == Path3DAlgorithm.DIJKSTRA_3D:
        return dijkstra_path_3d(start, end, obstacles, limit)
    else:
        return astar_path_3d(start, end, obstacles, limit)