import json
import networkx as nx
import matplotlib.pyplot as plt

# Load JSON file
file_path = r"data/nav_graph_3.json"
json_file = file_path

# Read JSON data
with open(json_file, "r") as file:
    data = json.load(file)

# Extract vertices and lanes
vertices = data["levels"]["l1"]["vertices"]
lanes = data["levels"]["l1"]["lanes"]

# Create a graph
G = nx.Graph()

# Position dictionary for visualization
pos = {}
labels = {}
charger_nodes = []

# Add vertices to the graph
for i, (lat, lon, metadata) in enumerate(vertices):  # Swap lat/lon for proper visualization
    G.add_node(i)
    pos[i] = (lon, lat)  # Use (x=longitude, y=latitude)
    labels[i] = metadata.get("name", f"V{i}")

    if metadata.get("is_charger", False):  # Check if it's a charging station
        charger_nodes.append(i)

# Add lanes (edges) to the graph
for start, end, _ in lanes:  # Lanes are stored as [start, end, {metadata}]
    G.add_edge(start, end)

# Draw the graph
plt.figure(figsize=(10, 6))

# Draw edges
nx.draw_networkx_edges(G, pos, edge_color="black", width=1.5)

# Draw normal nodes
normal_nodes = [node for node in G.nodes if node not in charger_nodes]
nx.draw_networkx_nodes(G, pos, nodelist=normal_nodes, node_color="skyblue", node_size=500, edgecolors="black")

# Highlight charger nodes
nx.draw_networkx_nodes(G, pos, nodelist=charger_nodes, node_color="red", node_size=700, edgecolors="black", label="Chargers")

# Draw labels
nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight="bold", verticalalignment="bottom")

# Finalize plot
plt.title("Navigation Graph Visualization")
plt.legend()
plt.grid(True)
plt.show()

