from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import json
from io import BytesIO
from typing import List, Dict
from src.controllers.traffic_manager import TrafficManager
traffic_manager = TrafficManager()
app = FastAPI()

# Example of robot data model
class Robot(BaseModel):
    robot_id: str
    position: tuple
    status: str = "waiting"

# Store environment graph and robots data
env_graph = None
robots = []

@app.post("/upload_json/")
async def upload_json(file: UploadFile = File(...)):
    try:
        content = await file.read()
        env_graph_data = json.loads(content.decode())
        global env_graph
        env_graph = env_graph_data
        return {"message": "JSON loaded successfully", "data": env_graph_data}
    except Exception as e:
        return {"error": str(e)}

@app.get("/get_env_graph/")
async def get_env_graph():
    if env_graph:
        return {"data": env_graph}
    else:
        return {"error": "No environment graph available"}

@app.post("/spawn_robot/")
async def spawn_robot(robot: Robot):
    robots.append(robot)
    return {"message": f"Robot {robot.robot_id} spawned", "robot": robot.dict()}

@app.get("/get_robots/")
async def get_robots():
    return {"robots": [robot.dict() for robot in robots]}


@app.get("/get_collisions/")
async def get_collisions(threshold: float = 2.0):
    robot_positions = {robot.robot_id: robot.position for robot in robots}
    collisions = traffic_manager.detect_collision(robot_positions, threshold)
    return {"collisions": collisions}

@app.get("/get_lane_status/{lane_from}/{lane_to}")
async def get_lane_status(lane_from: int, lane_to: int):
    status = traffic_manager.get_lane_status((lane_from, lane_to))
    return {"status": status}

@app.post("/set_robot_priority/{robot_id}")
async def set_robot_priority(robot_id: str, priority: float):
    traffic_manager.set_robot_priority(robot_id, priority)
    return {"message": f"Priority for robot {robot_id} set to {priority}"}