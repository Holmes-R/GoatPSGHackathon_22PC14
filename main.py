from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import json
from io import BytesIO
from typing import List, Dict

app = FastAPI()

# Example of robot data model
class Robot(BaseModel):
    robot_id: int
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
