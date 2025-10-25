import networkx as nx
import matplotlib.pyplot as plt
import heapq
import tkinter as tk
from tkinter import simpledialog

# ==============================
# CONFIGURACIÓN GLOBAL
# ==============================
G = nx.Graph()
pos = {}
node_count = 0
selected_nodes = []
mode = "nodos"  # "nodos", "aristas", "inicio_fin"

# ==============================
# DIBUJAR ESCENA
# ==============================
def draw_scene(highlight_path=None, title=""):
    plt.clf()
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.title(title, fontsize=14, fontweight="bold")

    if highlight_path:
        path_edges = list(zip(highlight_path[:-1], highlight_path[1:]))
        nx.draw(G, pos, with_labels=True, node_color="lightgreen", node_size=900, font_weight="bold")
        nx.draw_networkx_edges(G, pos, edgelist=path_edges, width=3, edge_color="red")
    else:
        nx.draw(G, pos, with_labels=True, node_color="skyblue", node_size=900, font_weight="bold")

    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="blue")

    # Ajustar vista automáticamente
    if pos:
        all_x = [x for x, _ in pos.values()]
        all_y = [y for _, y in pos.values()]
        plt.xlim(min(all_x) - 1, max(all_x) + 1)
        plt.ylim(min(all_y) - 1, max(all_y) + 1)

    plt.draw()

# ==============================
# EVENTOS DE CLIC
# ==============================
def on_click(event):
    global node_count, mode, selected_nodes

    if event.inaxes is None:
        return

    # === MODO: CREAR NODOS ===
    if mode == "nodos":
        node_name = chr(65 + node_count)
        G.add_node(node_name)
        pos[node_name] = (round(event.xdata, 2), round(event.ydata, 2))
        node_count += 1
        draw_scene(title="Modo: Añadiendo Nodos (clic para agregar)")

    # === MODO: CREAR ARISTAS ===
    elif mode == "aristas":
        for node, (x, y) in pos.items():
            # Detectar clic cerca de un nodo
            if abs(event.xdata - x) < 0.2 and abs(event.ydata - y) < 0.2:
                if selected_nodes and node == selected_nodes[-1]:
                    return  # evita doble clic en el mismo nodo
                selected_nodes.append(node)
                if len(selected_nodes) == 2:
                    n1, n2 = selected_nodes
                    if n1 == n2:
                        print("❌ No se puede conectar un nodo consigo mismo.")
                        selected_nodes.clear()
                        return
                    # Ventana emergente para ingresar peso
                    root = tk.Tk()
                    root.withdraw()
                    peso = simpledialog.askfloat(
                        "Peso de la Arista",
                        f"Ingrese el peso entre {n1} y {n2}:",
                        minvalue=0.1
                    )
                    root.destroy()
                    if peso is not None:
                        G.add_edge(n1, n2, weight=peso)
                        draw_scene(title=f"Arista añadida: {n1}-{n2} (peso {peso})")
                    selected_nodes.clear()
                break

    # === MODO: SELECCIONAR INICIO/FIN ===
    elif mode == "inicio_fin":
        for node, (x, y) in pos.items():
            if abs(event.xdata - x) < 0.2 and abs(event.ydata - y) < 0.2:
                selected_nodes.append(node)
                draw_scene(title=f"Seleccionados: {selected_nodes}")
                if len(selected_nodes) == 2:
                    plt.close()
                break

# ==============================
# ALGORITMO DE DIJKSTRA VISUAL
# ==============================
def dijkstra_visual(G, start, target):
    plt.ion()
    distances = {node: float('inf') for node in G.nodes()}
    distances[start] = 0
    prev = {node: None for node in G.nodes()}
    pq = [(0, start)]
    visited = set()

    while pq:
        dist, current = heapq.heappop(pq)
        if current in visited:
            continue
        visited.add(current)

        draw_scene(title=f"Explorando {current}")
        plt.pause(1.0)

        for neighbor in G.neighbors(current):
            w = G[current][neighbor]['weight']
            new_dist = dist + w
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                prev[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))

    # Reconstruir camino
    path = []
    node = target
    while node is not None:
        path.insert(0, node)
        node = prev[node]

    draw_scene(highlight_path=path, title=f"Camino más corto: {' → '.join(path)} (Distancia: {distances[target]})")
    plt.pause(0.5)
    plt.ioff()
    plt.show()

    print(f"\nCamino más corto de {start} a {target}: {' → '.join(path)}")
    print(f"Distancia total: {distances[target]}")

# ==============================
# EJECUCIÓN PRINCIPAL
# ==============================
print("=== CONSTRUCCIÓN DEL GRAFO ===")
print("1️⃣ Fase NODOS: Clic para crear nodos (A, B, C...). Luego cierra la ventana.")
plt.ion()
fig = plt.figure()
cid = fig.canvas.mpl_connect('button_press_event', on_click)
draw_scene(title="Modo: Añadiendo Nodos (clic para agregar)")
plt.show(block=True)

# Cambiar a modo aristas
mode = "aristas"
print("\n2️⃣ Fase ARISTAS: Clic en dos nodos para unirlos. Aparecerá una ventana para ingresar el peso.")
print("Cierra la ventana cuando termines de agregar todas las aristas.")
fig = plt.figure()
cid = fig.canvas.mpl_connect('button_press_event', on_click)
draw_scene(title="Modo: Dibujando Aristas (clic en dos nodos para unir)")
plt.show(block=True)

# Seleccionar inicio y fin
mode = "inicio_fin"
print("\n3️⃣ Fase INICIO-FIN: Clic primero en el nodo de inicio y luego en el de destino.")
fig = plt.figure()
cid = fig.canvas.mpl_connect('button_press_event', on_click)
draw_scene(title="Selecciona el nodo de inicio y el de destino")
plt.show(block=True)

# Ejecutar Dijkstra
if len(selected_nodes) == 2:
    start, target = selected_nodes
    print(f"\nEjecutando Dijkstra desde {start} hasta {target}...")
    dijkstra_visual(G, start, target)
else:
    print("No se seleccionaron correctamente los nodos de inicio y destino.")
