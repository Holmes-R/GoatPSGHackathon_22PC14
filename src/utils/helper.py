import heapq
from typing import Dict, List, Tuple, Optional
from functools import lru_cache

class PathFinder:
    _CACHE_SIZE = 1000  
    
    @classmethod
    @lru_cache(maxsize=_CACHE_SIZE)
    def find_path(
        cls,
        nav_graph_tuple: tuple,  
        start_idx: int,
        end_idx: int,
        congestion_tuple: Optional[tuple] = None  
    ) -> List[int]:
       
        nav_graph = {
            "vertices": nav_graph_tuple[0],
            "lanes": nav_graph_tuple[1]
        }
        congestion_data = dict(congestion_tuple) if congestion_tuple else None
        
        if start_idx == end_idx:
            return []

        if len(nav_graph["vertices"]) > 100:
            return cls._bidirectional_search(nav_graph, start_idx, end_idx, congestion_data)
            
        return cls._a_star_search(nav_graph, start_idx, end_idx, congestion_data)

    @staticmethod
    def _a_star_search(
        nav_graph: Dict,
        start_idx: int,
        end_idx: int,
        congestion_data: Optional[Dict[Tuple[int, int], float]] = None
    ) -> List[int]:
        """Optimized A* implementation with micro-optimizations"""
        vertices = nav_graph["vertices"]
        lanes = nav_graph["lanes"]
        
        end_pos = vertices[end_idx]
        heuristic_cache = [0] * len(vertices)
        for i, pos in enumerate(vertices):
            dx = pos[0] - end_pos[0]
            dy = pos[1] - end_pos[1]
            heuristic_cache[i] = (dx*dx + dy*dy)**0.5

        open_set = []
        heapq.heappush(open_set, (0, start_idx))
        came_from = {}
        g_score = {start_idx: 0}
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
            for lane in lanes:
                if lane[0] == current:
                    neighbors.add(lane[1])
                elif lane[1] == current:
                    neighbors.add(lane[0])

            current_pos = vertices[current]
            current_g = g_score[current]
            
            for neighbor in neighbors:
                neighbor_pos = vertices[neighbor]
                dx = current_pos[0] - neighbor_pos[0]
                dy = current_pos[1] - neighbor_pos[1]
                base_cost = (dx*dx + dy*dy)**0.5
                
                if congestion_data:
                    congestion = congestion_data.get((current, neighbor), 0)
                    congestion += congestion_data.get((neighbor, current), 0)
                    base_cost *= (1 + congestion)
                
                tentative_g = current_g + base_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + heuristic_cache[neighbor]
                    if neighbor not in open_set_hash:
                        heapq.heappush(open_set, (f_score, neighbor))
                        open_set_hash.add(neighbor)

        return []

    @staticmethod
    def _bidirectional_search(
        nav_graph: Dict,
        start_idx: int,
        end_idx: int,
        congestion_data: Optional[Dict[Tuple[int, int], float]] = None
    ) -> List[int]:
        """Bidirectional A* for large graphs"""

        pass

    @staticmethod
    def prepare_for_caching(nav_graph: Dict, congestion_data: Optional[Dict] = None) -> tuple:
        """Convert nav_graph and congestion_data to hashable types for caching"""
        nav_graph_tuple = (
            tuple(tuple(v) for v in nav_graph["vertices"]),
            tuple(tuple(l) for l in nav_graph["lanes"])
        )
        congestion_tuple = tuple(congestion_data.items()) if congestion_data else None
        return nav_graph_tuple, congestion_tuple