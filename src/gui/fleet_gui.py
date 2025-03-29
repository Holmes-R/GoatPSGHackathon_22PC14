import json
import base64
import dash
import networkx as nx
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output, State
import requests  # To send requests to FastAPI
from src.models.robots import Robot
# Dash App
dash_app = dash.Dash(__name__)

# Graph Data
G = nx.Graph()
pos = {}
robot_positions = {}  # Dictionary to store robot positions and their colors
robot_counter = 1  # Unique identifier for robots

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

def draw_graph():
    """Draws the graph with nodes, edges, and robots."""
    fig = go.Figure()

    # Draw nodes
    for node in G.nodes():
        color = G.nodes[node].get("color", "blue")
        node_label = G.nodes[node].get("label", f"Node {node}")
        fig.add_trace(go.Scatter(
            x=[pos[node][0]], y=[pos[node][1]],
            mode="markers+text",
            marker=dict(size=12, color=color),
            text=node_label,
            textposition="top center",
            name=node_label,
            customdata=[[node]],  # Wrap node index in a list to avoid TypeError
            hoverinfo='text'
        ))

    # Draw edges
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode="lines",
            line=dict(width=2, color="gray"),
            showlegend=False
        ))

    # Draw robots and display their status
    for robot_id, robot in robot_positions.items():
        robot_status = robot.get_status()  # Get robot's current status
        robot_color = robot.node_color
        fig.add_trace(go.Scatter(
            x=[pos[robot.position][0]], y=[pos[robot.position][1]],
            mode="markers+text",
            marker=dict(size=16, color=robot_color, symbol="circle"),
            text=f"R{robot_id}: {robot_status}",
            textposition="bottom center",
            name=f"Robot {robot_id}",
            customdata=[robot.position],
            hoverinfo='text'
        ))

    return fig

# Dash Layout
dash_app.layout = html.Div([
    html.H1("Environment & Robot Visualization"),
    dcc.Upload(id="upload-data", children=html.Button("Upload JSON File"), multiple=False),
    dcc.Graph(id="graph-plot", config={'displayModeBar': False}),
    html.Div(id="robot-status"),
])

@dash_app.callback(
    Output("graph-plot", "figure"),
    Output("robot-status", "children"),
    [Input("upload-data", "contents"), Input("graph-plot", "clickData")],
    prevent_initial_call=True
)
def update_graph(file_contents, clickData):
    global robot_counter, robot_positions
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    message = ""

    # Handle file upload
    if triggered_id == "upload-data" and file_contents:
        content_type, content_string = file_contents.split(",")
        decoded = base64.b64decode(content_string)
        json_data = json.loads(decoded)
        extract_graph_data(json_data)

        # **Reset robot positions and counter**
        robot_positions.clear()
        robot_counter = 1  

    # Handle robot spawning on graph click
    elif triggered_id == "graph-plot" and clickData:
        point_data = clickData['points'][0]
        node_index = point_data.get('customdata', [None])[0] if isinstance(point_data.get('customdata'), list) else point_data.get('customdata')

        if node_index is None:
            message = "Invalid click. Please select a valid node."
        elif node_index in G.nodes:  
            response = requests.post(f"http://127.0.0.1:8000/spawn_robot/{node_index}")
            if response.ok:
                robot_info = response.json()
                message = robot_info["message"]

                node_color = G.nodes[node_index].get("color", "black")  
                robot_positions[robot_counter] = Robot(robot_counter, node_index, node_color)

                message += f" Robot R{robot_counter} spawned at Node {node_index}."
                robot_counter += 1
            else:
                message = response.json().get("message", "Error spawning robot.")
        else:
            message = "Invalid node selected."

    return draw_graph(), message

if __name__ == "__main__":
    dash_app.run(debug=True, port=8051)
