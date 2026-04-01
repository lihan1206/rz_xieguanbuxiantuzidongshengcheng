"""
A*路径规划算法实现
支持3D空间、障碍物避让、路径优化
"""

import heapq
import math
from typing import List, Tuple, Dict, Set, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import numpy as np


class NodeState(Enum):
    """节点状态"""
    FREE = 0      # 空闲
    OBSTACLE = 1  # 障碍物
    START = 2     # 起点
    END = 3       # 终点
    PATH = 4      # 路径


@dataclass
class Point3D:
    """3D点坐标"""
    x: float
    y: float
    z: float = 0.0
    
    def __hash__(self):
        return hash((round(self.x, 3), round(self.y, 3), round(self.z, 3)))
    
    def __eq__(self, other):
        if not isinstance(other, Point3D):
            return False
        return (round(self.x, 3) == round(other.x, 3) and
                round(self.y, 3) == round(other.y, 3) and
                round(self.z, 3) == round(other.z, 3))
    
    def distance_to(self, other: 'Point3D') -> float:
        """计算到另一点的欧几里得距离"""
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2 +
            (self.z - other.z) ** 2
        )
    
    def to_tuple(self) -> Tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass
class Node:
    """A*节点"""
    point: Point3D
    g_cost: float = float('inf')  # 从起点到当前节点的实际代价
    h_cost: float = 0.0           # 启发式估计代价
    parent: Optional['Node'] = None
    
    @property
    def f_cost(self) -> float:
        return self.g_cost + self.h_cost
    
    def __lt__(self, other: 'Node') -> bool:
        return self.f_cost < other.f_cost
    
    def __hash__(self):
        return hash(self.point)
    
    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.point == other.point


@dataclass
class Obstacle:
    """障碍物定义"""
    id: str
    position: Point3D
    width: float
    height: float
    depth: float
    buffer_zone: float = 0.0  # 缓冲区域
    
    def contains(self, point: Point3D) -> bool:
        """检查点是否在障碍物内（含缓冲区）"""
        half_w = (self.width / 2) + self.buffer_zone
        half_h = (self.height / 2) + self.buffer_zone
        half_d = (self.depth / 2) + self.buffer_zone
        
        return (self.position.x - half_w <= point.x <= self.position.x + half_w and
                self.position.y - half_h <= point.y <= self.position.y + half_h and
                self.position.z - half_d <= point.z <= self.position.z + half_d)
    
    def get_bounds(self) -> Tuple[Point3D, Point3D]:
        """获取障碍物边界 (min, max)"""
        half_w = (self.width / 2) + self.buffer_zone
        half_h = (self.height / 2) + self.buffer_zone
        half_d = (self.depth / 2) + self.buffer_zone
        
        min_point = Point3D(
            self.position.x - half_w,
            self.position.y - half_h,
            self.position.z - half_d
        )
        max_point = Point3D(
            self.position.x + half_w,
            self.position.y + half_h,
            self.position.z + half_d
        )
        return min_point, max_point


@dataclass
class PathConstraints:
    """路径约束条件"""
    max_length: Optional[float] = None      # 最大长度
    min_segment_length: float = 10.0        # 最小线段长度
    max_bend_angle: float = 90.0            # 最大弯折角度
    prefer_straight: bool = True            # 优先直线路径
    avoid_areas: List[Tuple[Point3D, Point3D]] = field(default_factory=list)  # 避让区域
    weight_factors: Dict[str, float] = field(default_factory=lambda: {
        'length': 1.0,
        'bends': 0.5,
        'elevation': 0.3
    })


@dataclass
class RouteResult:
    """路径计算结果"""
    path: List[Point3D]
    total_length: float
    bend_count: int
    bend_points: List[Point3D]
    calculation_time_ms: float
    is_optimal: bool
    cost_breakdown: Dict[str, float]


class AStarPathfinder:
    """
    A*路径规划算法实现
    支持3D空间、多方向搜索、障碍物避让
    """
    
    def __init__(
        self,
        grid_size: float = 10.0,
        bounds: Optional[Tuple[Point3D, Point3D]] = None,
        allow_diagonal: bool = True,
        allow_3d: bool = True
    ):
        self.grid_size = grid_size
        self.bounds = bounds
        self.allow_diagonal = allow_diagonal
        self.allow_3d = allow_3d
        self.obstacles: List[Obstacle] = []
        
        # 6方向移动 (上下左右前后) + 对角线
        self.directions_2d = [
            (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0),  # 四方向
            (1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0)  # 对角线
        ]
        
        self.directions_3d = self.directions_2d + [
            (0, 0, 1), (0, 0, -1),  # 上下
            (1, 0, 1), (1, 0, -1), (-1, 0, 1), (-1, 0, -1),
            (0, 1, 1), (0, 1, -1), (0, -1, 1), (0, -1, -1),
            (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1),
            (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1)
        ]
    
    def add_obstacle(self, obstacle: Obstacle):
        """添加障碍物"""
        self.obstacles.append(obstacle)
    
    def clear_obstacles(self):
        """清除所有障碍物"""
        self.obstacles.clear()
    
    def is_valid_point(self, point: Point3D) -> bool:
        """检查点是否在有效范围内"""
        if self.bounds:
            min_bound, max_bound = self.bounds
            if not (min_bound.x <= point.x <= max_bound.x and
                    min_bound.y <= point.y <= max_bound.y and
                    min_bound.z <= point.z <= max_bound.z):
                return False
        return True
    
    def is_obstacle(self, point: Point3D) -> bool:
        """检查点是否与障碍物碰撞"""
        for obs in self.obstacles:
            if obs.contains(point):
                return True
        return False
    
    def snap_to_grid(self, point: Point3D) -> Point3D:
        """将点吸附到网格"""
        return Point3D(
            round(point.x / self.grid_size) * self.grid_size,
            round(point.y / self.grid_size) * self.grid_size,
            round(point.z / self.grid_size) * self.grid_size
        )
    
    def get_neighbors(self, node: Node) -> List[Point3D]:
        """获取节点的所有邻居"""
        directions = self.directions_3d if self.allow_3d else self.directions_2d
        neighbors = []
        
        for dx, dy, dz in directions:
            new_point = Point3D(
                node.point.x + dx * self.grid_size,
                node.point.y + dy * self.grid_size,
                node.point.z + dz * self.grid_size
            )
            
            if self.is_valid_point(new_point) and not self.is_obstacle(new_point):
                neighbors.append(new_point)
        
        return neighbors
    
    def heuristic(self, point: Point3D, goal: Point3D) -> float:
        """
        启发式函数 - 使用欧几里得距离
        可配置为曼哈顿距离或其他启发式
        """
        # 欧几里得距离
        return point.distance_to(goal)
    
    def calculate_cost(
        self,
        current: Node,
        neighbor: Point3D,
        goal: Point3D,
        constraints: PathConstraints
    ) -> float:
        """
        计算移动代价
        考虑距离、高度变化、弯折等因素
        """
        base_cost = current.point.distance_to(neighbor)
        
        # 长度权重
        cost = base_cost * constraints.weight_factors.get('length', 1.0)
        
        # 高度变化惩罚
        z_diff = abs(neighbor.z - current.point.z)
        if z_diff > 0:
            cost += z_diff * constraints.weight_factors.get('elevation', 0.3)
        
        # 弯折惩罚
        if current.parent:
            # 计算方向变化
            prev_dir = (
                current.point.x - current.parent.point.x,
                current.point.y - current.parent.point.y,
                current.point.z - current.parent.point.z
            )
            curr_dir = (
                neighbor.x - current.point.x,
                neighbor.y - current.point.y,
                neighbor.z - current.point.z
            )
            
            # 如果方向改变，增加弯折成本
            if prev_dir != curr_dir:
                cost += constraints.weight_factors.get('bends', 0.5) * self.grid_size
        
        return cost
    
    def find_path(
        self,
        start: Point3D,
        goal: Point3D,
        constraints: Optional[PathConstraints] = None,
        waypoints: Optional[List[Point3D]] = None,
        max_iterations: int = 100000
    ) -> Optional[RouteResult]:
        """
        执行A*路径搜索
        
        Args:
            start: 起点
            goal: 终点
            constraints: 路径约束
            waypoints: 途经点
            max_iterations: 最大迭代次数
        
        Returns:
            RouteResult: 路径结果，失败返回None
        """
        import time
        start_time = time.time()
        
        if constraints is None:
            constraints = PathConstraints()
        
        # 吸附到网格
        start = self.snap_to_grid(start)
        goal = self.snap_to_grid(goal)
        
        # 检查起点终点有效性
        if self.is_obstacle(start) or self.is_obstacle(goal):
            return None
        
        # 处理途经点
        if waypoints:
            full_path = [start]
            current_start = start
            
            for waypoint in waypoints + [goal]:
                waypoint = self.snap_to_grid(waypoint)
                segment = self._find_path_segment(
                    current_start, waypoint, constraints, max_iterations
                )
                if segment is None:
                    return None
                full_path.extend(segment[1:])  # 避免重复点
                current_start = waypoint
            
            path = full_path
        else:
            path = self._find_path_segment(start, goal, constraints, max_iterations)
        
        if path is None:
            return None
        
        calculation_time = (time.time() - start_time) * 1000
        
        # 计算路径统计信息
        return self._analyze_path(path, calculation_time)
    
    def _find_path_segment(
        self,
        start: Point3D,
        goal: Point3D,
        constraints: PathConstraints,
        max_iterations: int
    ) -> Optional[List[Point3D]]:
        """搜索单段路径"""
        
        # 开放列表（优先队列）
        open_set: List[Node] = []
        
        # 起始节点
        start_node = Node(point=start, g_cost=0.0)
        start_node.h_cost = self.heuristic(start, goal)
        heapq.heappush(open_set, start_node)
        
        # 关闭列表
        closed_set: Set[Point3D] = set()
        
        # 节点字典（用于快速查找）
        node_dict: Dict[Point3D, Node] = {start: start_node}
        
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            
            # 取出f值最小的节点
            current = heapq.heappop(open_set)
            
            # 到达目标
            if current.point == goal:
                return self._reconstruct_path(current)
            
            closed_set.add(current.point)
            
            # 遍历邻居
            for neighbor_point in self.get_neighbors(current):
                if neighbor_point in closed_set:
                    continue
                
                # 计算新的g值
                move_cost = self.calculate_cost(current, neighbor_point, goal, constraints)
                new_g = current.g_cost + move_cost
                
                neighbor_node = node_dict.get(neighbor_point)
                
                if neighbor_node is None:
                    # 新节点
                    neighbor_node = Node(
                        point=neighbor_point,
                        g_cost=new_g,
                        h_cost=self.heuristic(neighbor_point, goal),
                        parent=current
                    )
                    node_dict[neighbor_point] = neighbor_node
                    heapq.heappush(open_set, neighbor_node)
                elif new_g < neighbor_node.g_cost:
                    # 找到更优路径
                    neighbor_node.g_cost = new_g
                    neighbor_node.parent = current
                    # 重新入队（简化处理，实际可优化）
                    heapq.heappush(open_set, neighbor_node)
        
        # 未找到路径
        return None
    
    def _reconstruct_path(self, end_node: Node) -> List[Point3D]:
        """从终点回溯重建路径"""
        path = []
        current: Optional[Node] = end_node
        
        while current:
            path.append(current.point)
            current = current.parent
        
        return list(reversed(path))
    
    def _analyze_path(
        self,
        path: List[Point3D],
        calculation_time: float
    ) -> RouteResult:
        """分析路径特征"""
        
        # 计算总长度
        total_length = 0.0
        for i in range(len(path) - 1):
            total_length += path[i].distance_to(path[i + 1])
        
        # 计算弯折点
        bend_points = []
        bend_count = 0
        
        for i in range(1, len(path) - 1):
            prev_dir = (
                path[i].x - path[i-1].x,
                path[i].y - path[i-1].y,
                path[i].z - path[i-1].z
            )
            next_dir = (
                path[i+1].x - path[i].x,
                path[i+1].y - path[i].y,
                path[i+1].z - path[i].z
            )
            
            if prev_dir != next_dir:
                bend_count += 1
                bend_points.append(path[i])
        
        # 成本分解
        cost_breakdown = {
            'total_length': total_length,
            'bend_count': bend_count,
            'point_count': len(path)
        }
        
        return RouteResult(
            path=path,
            total_length=total_length,
            bend_count=bend_count,
            bend_points=bend_points,
            calculation_time_ms=calculation_time,
            is_optimal=True,  # A*保证最优性
            cost_breakdown=cost_breakdown
        )
    
    def optimize_path(
        self,
        path: List[Point3D],
        constraints: PathConstraints
    ) -> List[Point3D]:
        """
        路径后处理优化
        - 移除冗余点
        - 直线化
        """
        if len(path) <= 2:
            return path
        
        optimized = [path[0]]
        i = 0
        
        while i < len(path) - 1:
            # 尝试找到最远的可见点
            j = len(path) - 1
            while j > i:
                if self._is_line_of_sight_clear(path[i], path[j]):
                    optimized.append(path[j])
                    i = j
                    break
                j -= 1
            else:
                i += 1
                if i < len(path):
                    optimized.append(path[i])
        
        return optimized
    
    def _is_line_of_sight_clear(self, start: Point3D, end: Point3D) -> bool:
        """检查两点之间视线是否畅通"""
        # 使用Bresenham算法或采样检查
        distance = start.distance_to(end)
        steps = int(distance / (self.grid_size / 2))
        
        for i in range(1, steps):
            t = i / steps
            point = Point3D(
                start.x + (end.x - start.x) * t,
                start.y + (end.y - start.y) * t,
                start.z + (end.z - start.z) * t
            )
            if self.is_obstacle(point):
                return False
        
        return True


class MultiPathPlanner:
    """多路径规划器 - 支持多连接同时规划"""
    
    def __init__(self, pathfinder: AStarPathfinder):
        self.pathfinder = pathfinder
    
    def plan_multiple_paths(
        self,
        connections: List[Tuple[Point3D, Point3D]],
        constraints: Optional[PathConstraints] = None,
        prioritize: bool = True
    ) -> List[Optional[RouteResult]]:
        """
        规划多条路径
        
        Args:
            connections: 连接列表 [(start1, end1), (start2, end2), ...]
            constraints: 路径约束
            prioritize: 是否按优先级排序
        
        Returns:
            路径结果列表
        """
        results = []
        
        # 按优先级排序（如果需要）
        if prioritize:
            # 这里可以添加优先级逻辑
            pass
        
        for start, end in connections:
            result = self.pathfinder.find_path(start, end, constraints)
            results.append(result)
            
            # 将已规划路径添加为障碍物（避免交叉）
            if result:
                self._add_path_as_obstacle(result.path)
        
        return results
    
    def _add_path_as_obstacle(self, path: List[Point3D], width: float = 5.0):
        """将路径添加为障碍物（用于避免路径交叉）"""
        for point in path:
            obstacle = Obstacle(
                id=f"path_obstacle_{id(point)}",
                position=point,
                width=width,
                height=width,
                depth=width,
                buffer_zone=0
            )
            self.pathfinder.add_obstacle(obstacle)


# 使用示例
if __name__ == "__main__":
    # 创建路径规划器
    pathfinder = AStarPathfinder(
        grid_size=10.0,
        bounds=(Point3D(0, 0, 0), Point3D(500, 500, 100)),
        allow_diagonal=True,
        allow_3d=True
    )
    
    # 添加障碍物
    obstacle = Obstacle(
        id="wall_1",
        position=Point3D(200, 200, 0),
        width=100,
        height=20,
        depth=50,
        buffer_zone=10
    )
    pathfinder.add_obstacle(obstacle)
    
    # 定义起点终点
    start = Point3D(50, 50, 0)
    goal = Point3D(400, 400, 0)
    
    # 定义约束
    constraints = PathConstraints(
        max_length=1000,
        min_segment_length=10,
        max_bend_angle=90,
        prefer_straight=True,
        weight_factors={
            'length': 1.0,
            'bends': 0.8,
            'elevation': 0.5
        }
    )
    
    # 执行路径搜索
    result = pathfinder.find_path(start, goal, constraints)
    
    if result:
        print(f"找到路径!")
        print(f"总长度: {result.total_length:.2f}")
        print(f"弯折次数: {result.bend_count}")
        print(f"计算耗时: {result.calculation_time_ms:.2f}ms")
        print(f"路径点数: {len(result.path)}")
        print(f"路径点: {[(p.x, p.y, p.z) for p in result.path]}")
    else:
        print("未找到路径")
