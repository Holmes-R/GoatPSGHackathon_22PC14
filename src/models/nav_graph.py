import json
import networkx as nx
import matplotlib.pyplot as plt

file_path = r"data/nav_graph_3.json"
json_file = file_path

with open(json_file, "r") as file:
    data = json.load(file)

vertices = data["levels"]["l1"]["vertices"]
lanes = data["levels"]["l1"]["lanes"]

G = nx.Graph()

pos = {}
labels = {}
charger_nodes = []

for i, (lat, lon, metadata) in enumerate(vertices): 
    G.add_node(i)
    pos[i] = (lon, lat)  
    labels[i] = metadata.get("name", f"V{i}")

    if metadata.get("is_charger", False):  
        charger_nodes.append(i)

for start, end, _ in lanes: 
    G.add_edge(start, end)

plt.figure(figsize=(10, 6))

nx.draw_networkx_edges(G, pos, edge_color="black", width=1.5)

normal_nodes = [node for node in G.nodes if node not in charger_nodes]
nx.draw_networkx_nodes(G, pos, nodelist=normal_nodes, node_color="skyblue", node_size=500, edgecolors="black")

nx.draw_networkx_nodes(G, pos, nodelist=charger_nodes, node_color="red", node_size=700, edgecolors="black", label="Chargers")

nx.draw_networkx_labels(G, pos, labels, font_size=10, font_weight="bold", verticalalignment="bottom")

plt.title("Navigation Graph Visualization")
plt.legend()
plt.grid(True)
plt.show()

