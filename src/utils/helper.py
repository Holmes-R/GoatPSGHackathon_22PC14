# helpers.py
import heapq
from typing import Dict, List, Tuple, Optional

class PathFinder:
    @staticmethod
    def find_path(
        nav_graph: Dict,
        start_idx: int,
        end_idx: int,
        congestion_data: Optional[Dict[Tuple[int, int], float]] = None
    ) -> List[int]:
        """
        A* pathfinding with optional congestion awareness
        Args:
            nav_graph: Navigation graph with vertices and lanes
            start_idx: Starting vertex index
            end_idx: Target vertex index
            congestion_data: {(from_idx, to_idx): congestion_level}
        Returns:
            List of vertex indices in path (empty if no path)
        """
        def heuristic(u: int, v: int) -> float:
            p1, p2 = nav_graph["vertices"][u], nav_graph["vertices"][v]
            return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5

        def edge_cost(u: int, v: int) -> float:
            p1, p2 = nav_graph["vertices"][u], nav_graph["vertices"][v]
            base_cost = ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5
            if congestion_data:
                congestion = congestion_data.get((u, v), 0) + congestion_data.get((v, u), 0)
                return base_cost * (1 + congestion)
            return base_cost

        open_set = []
        heapq.heappush(open_set, (0, start_idx))
        came_from = {}
        g_score = {start_idx: 0}
        f_score = {start_idx: heuristic(start_idx, end_idx)}
        open_set_hash = {start_idx}

        while open_set:
            current = heapq.heappop(open_set)[1]
            open_set_hash.remove(current)

            if current == end_idx:
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return path[::-1]

            neighbors = set()
            for lane in nav_graph["lanes"]:
                if lane[0] == current:
                    neighbors.add(lane[1])
                elif lane[1] == current:
                    neighbors.add(lane[0])

            for neighbor in neighbors:
                tentative_g_score = g_score[current] + edge_cost(current, neighbor)
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + heuristic(neighbor, end_idx)
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
                        open_set_hash.add(neighbor)

        return []