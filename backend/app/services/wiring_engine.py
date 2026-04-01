from __future__ import annotations

import heapq
import random
import math
from collections.abc import Iterable
from enum import Enum


class PathAlgorithm(Enum):
    """路径算法类型"""
    ASTAR = "astar"
    DIJKSTRA = "dijkstra"
    GENETIC = "genetic"


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


def _manhattan_distance(a: tuple[int, int], b: tuple[int, int]) -> int:
    """曼哈顿距离"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _euclidean_distance(a: tuple[int, int], b: tuple[int, int]) -> float:
    """欧几里得距离"""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _reconstruct_path(previous: dict, end: tuple[int, int]) -> list[tuple[int, int]]:
    """重建路径"""
    path: list[tuple[int, int]] = []
    cursor: tuple[int, int] | None = end
    while cursor is not None:
        path.append(cursor)
        cursor = previous.get(cursor)
    path.reverse()
    return path


def astar_path(
    start: tuple[int, int], end: tuple[int, int], obstacles: Iterable[dict], limit: int = 100
) -> list[tuple[int, int]]:
    """
    A*算法寻路
    """
    if start == end:
        return [start]

    blocked = _blocked_points(obstacles)
    blocked.discard(start)
    blocked.discard(end)

    heap: list[tuple[int, int, tuple[int, int]]] = [(0, 0, start)]
    g_scores: dict[tuple[int, int], int] = {start: 0}
    f_scores: dict[tuple[int, int], int] = {start: _manhattan_distance(start, end)}
    previous: dict[tuple[int, int], tuple[int, int] | None] = {start: None}

    while heap:
        current_f, current_g, current = heapq.heappop(heap)
        
        if current == end:
            break
            
        if current_f > f_scores.get(current, float("inf")):
            continue

        for neighbor in _neighbors(current, limit):
            if neighbor in blocked:
                continue
                
            tentative_g = current_g + 1
            
            if tentative_g < g_scores.get(neighbor, float("inf")):
                previous[neighbor] = current
                g_scores[neighbor] = tentative_g
                f_scores[neighbor] = tentative_g + _manhattan_distance(neighbor, end)
                heapq.heappush(heap, (f_scores[neighbor], g_scores[neighbor], neighbor))

    if end not in previous:
        raise ValueError("无法生成路径，请调整设备坐标或障碍物设置")

    return _reconstruct_path(previous, end)


def dijkstra_path(
    start: tuple[int, int], end: tuple[int, int], obstacles: Iterable[dict], limit: int = 100
) -> list[tuple[int, int]]:
    """
    Dijkstra算法寻路
    """
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

    return _reconstruct_path(previous, end)


class GeneticPathFinder:
    """
    遗传算法路径寻路器
    """
    
    def __init__(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        obstacles: Iterable[dict],
        limit: int = 100,
        population_size: int = 100,
        max_generations: int = 200,
        mutation_rate: float = 0.2
    ):
        self.start = start
        self.end = end
        self.blocked = _blocked_points(obstacles)
        self.limit = limit
        self.population_size = population_size
        self.max_generations = max_generations
        self.mutation_rate = mutation_rate
        self.max_path_length = _manhattan_distance(start, end) * 3
        
    def _create_random_path(self) -> list[tuple[int, int]]:
        """创建随机路径"""
        path = [self.start]
        current = self.start
        
        for _ in range(self.max_path_length):
            if current == self.end:
                break
                
            neighbors = [n for n in _neighbors(current, self.limit) if n not in self.blocked]
            if not neighbors:
                break
                
            current = random.choice(neighbors)
            path.append(current)
            
        return path
    
    def _fitness(self, path: list[tuple[int, int]]) -> float:
        """计算适应度"""
        if not path:
            return 0
            
        # 路径到达终点的奖励
        if path[-1] == self.end:
            base_score = 1000
        else:
            distance_to_end = _manhattan_distance(path[-1], self.end)
            base_score = max(0, 100 - distance_to_end)
        
        # 路径长度的惩罚（越短越好）
        length_penalty = len(path) * 0.5
        
        # 检测碰撞
        collision_count = sum(1 for p in path if p in self.blocked)
        collision_penalty = collision_count * 50
        
        return max(1, base_score - length_penalty - collision_penalty)
    
    def _crossover(self, parent1: list[tuple[int, int]], parent2: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """交叉操作"""
        # 寻找公共点进行交叉
        common_points = [p for p in parent1 if p in parent2 and p != self.start]
        
        if not common_points:
            return parent1.copy() if random.random() < 0.5 else parent2.copy()
            
        crossover_point = random.choice(common_points)
        idx1 = parent1.index(crossover_point)
        idx2 = parent2.index(crossover_point)
        
        # 合并路径
        child = parent1[:idx1] + parent2[idx2:]
        
        # 移除循环
        seen = set()
        unique_path = []
        for p in child:
            if p not in seen:
                seen.add(p)
                unique_path.append(p)
            else:
                # 遇到重复点，结束路径
                break
                
        return unique_path
    
    def _mutate(self, path: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """变异操作"""
        if len(path) < 3 or random.random() > self.mutation_rate:
            return path
            
        # 随机选择一个位置进行变异
        mutate_idx = random.randint(1, len(path) - 2)
        
        # 尝试重新路由该点附近的路径
        current = path[mutate_idx - 1]
        target = path[mutate_idx + 1] if mutate_idx + 1 < len(path) else self.end
        
        # 生成一个随机的中间点
        neighbors = [n for n in _neighbors(current, self.limit) if n not in self.blocked]
        if neighbors:
            new_point = random.choice(neighbors)
            new_path = path[:mutate_idx] + [new_point] + path[mutate_idx + 1:]
            return new_path
            
        return path
    
    def find_path(self) -> list[tuple[int, int]]:
        """执行遗传算法寻路"""
        # 初始化种群
        population = [self._create_random_path() for _ in range(self.population_size)]
        
        best_path = None
        best_fitness = 0
        
        for generation in range(self.max_generations):
            # 计算适应度
            fitness_scores = [(self._fitness(path), path) for path in population]
            fitness_scores.sort(reverse=True, key=lambda x: x[0])
            
            # 更新最佳路径
            if fitness_scores[0][0] > best_fitness:
                best_fitness = fitness_scores[0][0]
                best_path = fitness_scores[0][1]
                
                # 如果找到完美解，提前结束
                if best_path and best_path[-1] == self.end and len(best_path) < self.max_path_length:
                    break
            
            # 选择精英个体
            elite_count = max(5, self.population_size // 5)
            elite = [path for _, path in fitness_scores[:elite_count]]
            
            # 创建新一代
            new_population = elite.copy()
            
            while len(new_population) < self.population_size:
                # 轮盘赌选择
                total_fitness = sum(score for score, _ in fitness_scores)
                if total_fitness > 0:
                    r1 = random.random() * total_fitness
                    r2 = random.random() * total_fitness
                    
                    parent1 = None
                    parent2 = None
                    cum_sum = 0
                    
                    for score, path in fitness_scores:
                        cum_sum += score
                        if parent1 is None and cum_sum >= r1:
                            parent1 = path
                        if parent2 is None and cum_sum >= r2:
                            parent2 = path
                        if parent1 and parent2:
                            break
                else:
                    parent1, parent2 = random.sample(elite, 2)
                
                if parent1 and parent2:
                    child = self._crossover(parent1, parent2)
                    child = self._mutate(child)
                    new_population.append(child)
            
            population = new_population
        
        if not best_path or best_path[-1] != self.end:
            raise ValueError("无法生成路径，请调整设备坐标或障碍物设置")
            
        return best_path


def genetic_path(
    start: tuple[int, int], end: tuple[int, int], obstacles: Iterable[dict], limit: int = 100
) -> list[tuple[int, int]]:
    """
    遗传算法寻路入口函数
    """
    finder = GeneticPathFinder(start, end, obstacles, limit)
    return finder.find_path()


# 兼容原接口
shortest_path = astar_path
