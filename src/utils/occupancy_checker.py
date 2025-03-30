from collections import deque
from typing import Optional, List

class OccupancyChecker:
    @staticmethod
    def get_vertex_occupancy(fleet_manager, vertex_idx: int) -> Optional[str]:
        """
        Check if a vertex is occupied by any robot.
        
        Args:
            fleet_manager: The FleetManager instance
            vertex_idx: Index of the vertex to check
            
        Returns:
            Robot ID if occupied, None if available
        """
        if not fleet_manager.nav_graph or vertex_idx >= len(fleet_manager.nav_graph["vertices"]):
            return None
            
        for robot in fleet_manager.robots:
            if fleet_manager.get_vertex_index(robot.position) == vertex_idx:
                return robot.robot_id
        return None
    
    @staticmethod
    def find_nearest_available_vertex(fleet_manager, start_vertex_idx: int) -> int:
        """
        Find the nearest unoccupied vertex using BFS.
        
        Args:
            fleet_manager: The FleetManager instance
            start_vertex_idx: Index of the starting vertex
            
        Returns:
            Index of the nearest available vertex, or -1 if none found
        """
        if not fleet_manager.nav_graph:
            return -1
            
        vertices = fleet_manager.nav_graph["vertices"]
        lanes = fleet_manager.nav_graph["lanes"]
        num_vertices = len(vertices)
        
        if start_vertex_idx < 0 or start_vertex_idx >= num_vertices:
            return -1
            
        # Check if starting vertex is actually available
        if not OccupancyChecker.get_vertex_occupancy(fleet_manager, start_vertex_idx):
            return start_vertex_idx
            
        # Build adjacency list
        adj = [[] for _ in range(num_vertices)]
        for lane in lanes:
            from_idx, to_idx = lane[0], lane[1]
            adj[from_idx].append(to_idx)
            adj[to_idx].append(from_idx)  # Assuming undirected graph
            
        # BFS setup
        visited = [False] * num_vertices
        queue = deque()
        queue.append(start_vertex_idx)
        visited[start_vertex_idx] = True
        
        while queue:
            current_idx = queue.popleft()
            
            # Check neighbors
            for neighbor_idx in adj[current_idx]:
                if not visited[neighbor_idx]:
                    # Check if this vertex is available
                    if not OccupancyChecker.get_vertex_occupancy(fleet_manager, neighbor_idx):
                        return neighbor_idx
                        
                    visited[neighbor_idx] = True
                    queue.append(neighbor_idx)
        
        return -1  # No available vertex found
    
    @staticmethod
    def get_available_vertices_in_range(fleet_manager, center_vertex_idx: int, max_distance: float) -> List[int]:
        """
        Get all available vertices within a certain distance of a center vertex.
        
        Args:
            fleet_manager: The FleetManager instance
            center_vertex_idx: Index of the center vertex
            max_distance: Maximum allowed distance
            
        Returns:
            List of vertex indices sorted by distance (closest first)
        """
        if not fleet_manager.nav_graph:
            return []
            
        vertices = fleet_manager.nav_graph["vertices"]
        center_pos = vertices[center_vertex_idx]
        available_vertices = []
        
        for idx, vertex in enumerate(vertices):
            if idx == center_vertex_idx:
                continue
                
            if not OccupancyChecker.get_vertex_occupancy(fleet_manager, idx):
                distance = ((vertex[0] - center_pos[0])**2 + (vertex[1] - center_pos[1])**2)**0.5
                if distance <= max_distance:
                    available_vertices.append((idx, distance))
        
        # Sort by distance
        available_vertices.sort(key=lambda x: x[1])
        return [x[0] for x in available_vertices]