import json
import base64
import dash
import networkx as nx
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL

# Dash App
dash_app = dash.Dash(__name__)

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

def draw_graph():
    """Draws the graph with nodes, edges, and robots."""
    fig = go.Figure()

    # Draw nodes
    for node in G.nodes():
        color = G.nodes[node].get("color", "blue")
        fig.add_trace(go.Scatter(
            x=[pos[node][0]], y=[pos[node][1]],
            mode="markers+text",
            marker=dict(size=12, color=color),
            text=G.nodes[node]["label"],
            textposition="top center",
            name=G.nodes[node]["label"]
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

    # Draw robots
    for robot_id, node in robot_positions.items():
        fig.add_trace(go.Scatter(
            x=[pos[node][0]], y=[pos[node][1]],
            mode="markers+text",
            marker=dict(size=16, color="black", symbol="circle"),
            text=f"R{robot_id}",
            textposition="bottom center",
            name=f"Robot {robot_id}"
        ))
    return fig

def generate_spawn_buttons():
    """Dynamically create a button for each node."""
    return [html.Button(f"Spawn at {G.nodes[n]['label']}", id={"type": "spawn-btn", "index": n}) for n in G.nodes if n not in robot_positions.values()]

dash_app.layout = html.Div([
    html.H1("Environment & Robot Visualization"),
    dcc.Upload(id="upload-data", children=html.Button("Upload JSON File"), multiple=False),
    dcc.Graph(id="graph-plot"),
    html.Div(id="spawn-buttons"),  # Buttons will be updated dynamically
    html.Div(id="robot-status"),
])

# **Callback 1: Handle File Upload and Generate Graph**
@dash_app.callback(
    Output("graph-plot", "figure"),
    Output("spawn-buttons", "children"),
    Input("upload-data", "contents")
)
def update_graph_from_upload(file_contents):
    if not file_contents:
        return go.Figure(), ""

    content_type, content_string = file_contents.split(",")
    decoded = base64.b64decode(content_string)
    json_data = json.loads(decoded)
    extract_graph_data(json_data)

    return draw_graph(), generate_spawn_buttons()

@dash_app.callback(
    Output("graph-plot", "figure", allow_duplicate=True),
    Output("robot-status", "children"),
    Output("spawn-buttons", "children", allow_duplicate=True),
    Input({"type": "spawn-btn", "index": ALL}, "n_clicks"),
    State({"type": "spawn-btn", "index": ALL}, "id"),
    prevent_initial_call=True
)
def spawn_robot(n_clicks, button_ids):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, "", dash.no_update

    for i, clicks in enumerate(n_clicks):
        if clicks and button_ids[i]:
            node_index = button_ids[i]["index"]
            
            # Ensure the robot spawns only if the vertex is unoccupied
            if node_index not in robot_positions.values():
                robot_positions[len(robot_positions) + 1] = node_index
                return draw_graph(), f"Robot spawned at {G.nodes[node_index]['label']}!", generate_spawn_buttons()
            else:
                return dash.no_update, f"Robot already exists at {G.nodes[node_index]['label']}!", dash.no_update
    
    return dash.no_update, "", dash.no_update

if __name__ == "__main__":
    dash_app.run(debug=True, port=8051)
