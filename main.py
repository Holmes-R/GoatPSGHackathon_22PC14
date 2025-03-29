import json
import networkx as nx
import random
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

# FastAPI App
app = FastAPI()

# Enable CORS for communication with Dash frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Graph Data
G = nx.Graph()
pos = {}
robot_positions = {}

# Predefined colors for nodes
node_colors = ["red", "blue", "green", "purple", "orange", "brown", "pink", "gray", "cyan", "magenta"]

def extract_graph_data(json_data):
    """Extracts graph data from JSON and assigns unique indices."""
    global G, pos
    G.clear()
    pos.clear()
    
    levels = json_data.get("levels", {})
    level_key = list(levels.keys())[0]  # Assuming first level
    level_data = levels[level_key]

    vertices = level_data.get("vertices", [])
    lanes = level_data.get("lanes", [])

    for index, vertex in enumerate(vertices):
        x, y, properties = vertex
        node_name = properties.get("name", f"Node {index}")
        G.add_node(index, label=node_name, color=node_colors[index % len(node_colors)])
        pos[index] = (x, y)

    for lane in lanes:
        source_index, target_index, *_ = lane
        if source_index < len(vertices) and target_index < len(vertices):
            G.add_edge(source_index, target_index)

print("Graph Nodes:", list(G.nodes(data=True)))
print("Node Positions:", pos)

@app.get("/graph")
async def get_graph():
    """Returns graph data to frontend"""
    return {
        "nodes": [{ "id": n, "label": G.nodes[n]["label"], "color": G.nodes[n]["color"], "position": pos[n]} for n in G.nodes()],
        "edges": list(G.edges())
    }

@app.post("/spawn_robot/{node_id}")
async def spawn_robot(node_id: int):
    """Spawns a robot at a given node"""
    if node_id in G.nodes and node_id not in robot_positions.values():
        robot_positions[len(robot_positions) + 1] = node_id
        return {"message": f"Robot spawned at {G.nodes[node_id]['label']}", "robots": robot_positions}
    return {"message": "Invalid node or already occupied", "robots": robot_positions}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    while True:
        await asyncio.sleep(2)  # Simulating movement
        for robot_id in robot_positions.keys():
            robot_positions[robot_id] = random.choice(list(G.nodes))
        await websocket.send_json({"robots": robot_positions})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
