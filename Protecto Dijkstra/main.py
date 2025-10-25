import os
import math
import heapq
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont

try:
    import cv2
    CV2_AVAILABLE = True
except Exception:
    CV2_AVAILABLE = False

# -----------------------------
# RUTAS A ARCHIVOS
# -----------------------------
ASSETS_DIR = "assets"
BACKGROUND_IMG = os.path.join(ASSETS_DIR, "mapa.png")
MENU_VIDEO = os.path.join(ASSETS_DIR, "menu_fondo.mp4")
TRANSITION_VIDEO = os.path.join(ASSETS_DIR, "transition.mp4")
ZELDA_TTF = os.path.join(ASSETS_DIR, "The-Wild-Breath-of-Zelda.ttf")

CHAR_IMG = {
    "pie": os.path.join(ASSETS_DIR, "personaje_pie.png"),
    "paravela": os.path.join(ASSETS_DIR, "personaje_paravela.png"),
    "caballo": os.path.join(ASSETS_DIR, "personaje_caballo.png"),
}

# -----------------------------
# CONSTANTES
# -----------------------------
WIN_W = 1031
WIN_H = 768
NODE_RADIUS = 12
NODE_COLOR = "#4cbef3"
NODE_OUTLINE = "#006899"
NODE_CURRENT = "#40f6e4"
NODE_VISITED = "#d0f0c0"
EDGE_COLOR = "#c1934a"
EDGE_HIGHLIGHT = "#66ff66"
EDGE_PATH = "#1c8ff4"
DIST_OFFSET = (0, -18)
ANIM_DELAY_MS = 700
MOVE_STEP_MS = 25
MOVE_STEP_PX = 8

# fuente "fantasiosa" por defecto si está instalada
FANCY_FONT_FAMILY = "Zelda"

# multiplicadores por modo
MODE_MULT = {
    "pie": 1.5,
    "paravela": 1.1,
    "caballo": 0.8
}

FIXED_NODES = [
    ("Torre 1", 236, 355),  ("Torre 2", 390, 230),  ("Torre 3", 430, 360),
    ("Torre 4", 707, 275),  ("Torre 5", 840, 280), ("Torre 6", 1086, 107),("Torre 7", 650, 435),
    ("Torre 8", 960, 285), ("Torre 9", 850, 430), ("Torre 10", 530, 483),
    ("Torre 11", 230, 625),("Torre 12", 380, 693),("Torre 13", 550, 620),
    ("Torre 14", 610, 750),("Torre 15", 720, 620),("Torre 16", 760, 780),
    ("Torre 17", 900, 676),("Torre 18", 1005, 658)
]

BASE_EDGES = [
    ("Torre 1","Torre 2",10),("Torre 1","Torre 3",12),("Torre 3","Torre 2",8),("Torre 3","Torre 4",18),("Torre 4","Torre 9",12),("Torre 9","Torre 5",8),
    ("Torre 9","Torre 8",7),("Torre 8","Torre 6",9),("Torre 5","Torre 6",15),("Torre 4","Torre 7",9),("Torre 3","Torre 10",8),("Torre 11","Torre 1",25),
    ("Torre 10","Torre 7",5),("Torre 10","Torre 13",6),("Torre 7","Torre 15",7),("Torre 13","Torre 15",8),("Torre 15","Torre 17",9),
    ("Torre 17","Torre 18",5),("Torre 17","Torre 16",7),("Torre 14","Torre 16",6),("Torre 14","Torre 13",10),("Torre 15","Torre 16",7),("Torre 13","Torre 12",9),("Torre 12","Torre 11",15)
]

# -----------------------------
# TRANSFORM (estático: sin pan/zoom)
# -----------------------------
class Transform:
    def __init__(self, scale=1.0, offset_x=0.0, offset_y=0.0):
        self.scale = scale
        self.offset_x = offset_x
        self.offset_y = offset_y
    def img_to_canvas(self, ix, iy):
        return ix * self.scale + self.offset_x, iy * self.scale + self.offset_y

# -----------------------------
# APP
# -----------------------------
class DijkstraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dijkstra — Hyrule App")
        self.root.geometry(f"{WIN_W}x{WIN_H}")
        self.root.minsize(800,600)
        self.fullscreen = False
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", lambda e: self._exit_fullscreen())

        self.transform = Transform(scale=1.0, offset_x=0.0, offset_y=0.0)
        self.nodes = []
        self.edges = []
        self.mode = "idle"
        self.selected_mode = None
        self.dijkstra_sel = []
        self.animating = False
        self.char_img_tk = None
        self.char_canvas_id = None

        self._move_frames = []
        self._move_frame_idx = 0

        self._counter_after_id = None
        self._counter_current = 0.0
        self._counter_target = 0.0
        self._counter_duration_ms = 0
        self._counter_start_time = None
        self._counter_update_interval = 30

        self._menu_btn_imgs = {}
        self._menu_title_imgtk = None

        self._load_resources()
        self._build_menu()

    # -----------------------------
    # Cargar recursos (imagenes, videos, fuentes)
    # -----------------------------
    def _load_resources(self):
        if not os.path.exists(BACKGROUND_IMG):
            messagebox.showerror("Error", f"No se encontró la imagen de fondo: {BACKGROUND_IMG}\nColócala en assets/ y renómbrala 'mapa.png'")
            self.root.destroy()
            return
        self.img_orig = Image.open(BACKGROUND_IMG).convert("RGBA")
        self.img_w, self.img_h = self.img_orig.size

        self.menu_video_cap = None
        self.transition_video_cap = None
        if CV2_AVAILABLE and os.path.exists(MENU_VIDEO):
            self.menu_video_cap = cv2.VideoCapture(MENU_VIDEO)
        if CV2_AVAILABLE and os.path.exists(TRANSITION_VIDEO):
            self.transition_video_cap = cv2.VideoCapture(TRANSITION_VIDEO)

        self.char_imgs = {}
        for key, path in CHAR_IMG.items():
            if os.path.exists(path):
                img = Image.open(path).convert("RGBA")
                img = img.resize((36,36), Image.LANCZOS)
                self.char_imgs[key] = img
            else:
                self.char_imgs[key] = None

        # detectar fuente fanciosa instalada en el sistema
        try:
            import tkinter.font as tkFont
            fams = set(tkFont.families())
            self._fancy_font_available = FANCY_FONT_FAMILY in fams
        except Exception:
            self._fancy_font_available = False

        # intentar registrar la TTF Zelda (best-effort)
        self._registered_font = False
        if os.path.exists(ZELDA_TTF):
            try:
                import sys, ctypes
                if sys.platform.startswith("win"):
                    FR_PRIVATE = 0x10
                    pathw = os.path.abspath(ZELDA_TTF)
                    ctypes.windll.gdi32.AddFontResourceExW(pathw, FR_PRIVATE, 0)
                    self._registered_font = True
                else:
                    self._registered_font = False
            except Exception:
                self._registered_font = False

    # -----------------------------
    # MENU UI (selección de modo) con botones como imágenes de texto
    # -----------------------------
    def _make_text_image(self, text, font_path, size=(300,72), text_color="white", bg_color=NODE_COLOR):
    # crea una imagen RGBA y dibuja el texto centrado usando la TTF si está disponible
        w, h = size
        img = Image.new("RGBA", (w, h), bg_color)
        draw = ImageDraw.Draw(img)

    # intentar cargar TTF Zelda; fallback a FANCY_FONT_FAMILY; finalmente cargar default
        font = None
        try:
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, int(h * 0.36))
            else:
                raise Exception("no ttf")
        except Exception:
            try:
                font = ImageFont.truetype(FANCY_FONT_FAMILY, int(h * 0.36))
            except Exception:
                try:
                    font = ImageFont.truetype("Segoe UI", int(h * 0.28))
                except Exception:
                    font = ImageFont.load_default()

    # medir texto de forma segura: usar textbbox si está disponible, si no usar textsize
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            txt_w = bbox[2] - bbox[0]
            txt_h = bbox[3] - bbox[1]
        except Exception:
            try:
                txt_w, txt_h = draw.textsize(text, font=font)
            except Exception:
            # último recurso: estimación
                txt_w = int(len(text) * (h * 0.18))
                txt_h = int(h * 0.36)

        x = (w - txt_w) // 2
        y = (h - txt_h) // 2
        draw.text((x, y), text, font=font, fill=text_color)

        return img

    def _build_menu(self):
        for w in self.root.winfo_children():
            w.destroy()

        self.menu_frame = tk.Frame(self.root, bg="#001523")
        self.menu_frame.pack(fill="both", expand=True)

        overlay_parent = None
        if self.menu_video_cap:
            lbl = tk.Label(self.menu_frame, bg="#001523")
            lbl.pack(fill="both", expand=True)
            self._play_video_on_label(self.menu_video_cap, lbl, loop=True)
            overlay_parent = self.menu_frame
        else:
            canvas = tk.Canvas(self.menu_frame, width=WIN_W, height=WIN_H, bg="#001523", highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            img = self.img_orig.copy().resize((WIN_W, WIN_H), Image.LANCZOS)
            self.menu_bg_tk = ImageTk.PhotoImage(img)
            canvas.create_image(0,0, anchor="nw", image=self.menu_bg_tk)
            canvas.create_rectangle(0,0,WIN_W,WIN_H, fill="#001523", stipple="gray50")
            overlay_parent = canvas

        # Crear imágenes para título y botones usando la TTF Zelda si está en assets
        try:
            title_img = self._make_text_image("Elige modo de desplazamiento", ZELDA_TTF, size=(560,64), text_color="white", bg_color="#001523")
            self._menu_title_imgtk = ImageTk.PhotoImage(title_img)
            title_widget = tk.Label(overlay_parent, image=self._menu_title_imgtk, bg="#001523")
            title_widget.place(relx=0.5, rely=0.18, anchor="center")
        except Exception:
            font_title = (FANCY_FONT_FAMILY, 20, "bold") if getattr(self, "_fancy_font_available", False) else ("Segoe UI", 20, "bold")
            title = tk.Label(overlay_parent, text="Elige modo de desplazamiento", bg="#001523", fg="white", font=font_title)
            title.place(relx=0.5, rely=0.18, anchor="center")

        # generar botones como imágenes y guardarlas en self para evitar GC
        btn_specs = [("A PIE", 0.32, 'pie'), ("PARAVELA", 0.50, 'paravela'), ("CABALLO", 0.68, 'caballo')]
        for label_text, relx, mode_key in btn_specs:
            pil_img = self._make_text_image(label_text, ZELDA_TTF, size=(220,54), text_color="white", bg_color=NODE_COLOR)
            tk_img = ImageTk.PhotoImage(pil_img)
            self._menu_btn_imgs[label_text] = tk_img
            tk.Button(overlay_parent, image=tk_img, command=lambda m=mode_key: self._start_transition_and_open(m),
                      bd=0, highlightthickness=0, activebackground=NODE_COLOR).place(relx=relx, rely=0.4, anchor="center", width=220, height=54)

        hint_font = (FANCY_FONT_FAMILY, 10) if getattr(self, "_fancy_font_available", False) else ("Segoe UI", 10)
        hint = tk.Label(overlay_parent, text="(Selecciona modo — luego elige nodo inicio y destino en el mapa)", bg="#001523", fg="white", font=hint_font)
        hint.place(relx=0.5, rely=0.52, anchor="center")

    def _play_video_on_label(self, cap, label_widget, loop=False):
        def update():
            ret, frame = cap.read()
            if not ret:
                if loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()
                    if not ret:
                        return
                else:
                    return
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            try:
                w = max(1, label_widget.winfo_width())
                h = max(1, label_widget.winfo_height())
            except Exception:
                w, h = WIN_W, WIN_H
            frame = cv2.resize(frame, (w, h))
            img = ImageTk.PhotoImage(Image.fromarray(frame))
            label_widget.imgtk = img
            label_widget.configure(image=img)
            label_widget.after(30, update)
        update()

    def _start_transition_and_open(self, mode_key):
        self.selected_mode = mode_key
        for w in self.root.winfo_children():
            w.destroy()
        if self.transition_video_cap:
            lbl = tk.Label(self.root, bg="black")
            lbl.pack(fill="both", expand=True)
            def update_tr():
                ret, frame = self.transition_video_cap.read()
                if not ret:
                    self.transition_video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    lbl.destroy()
                    self._build_main()
                    return
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                try:
                    w = max(1, lbl.winfo_width())
                    h = max(1, lbl.winfo_height())
                except Exception:
                    w, h = WIN_W, WIN_H
                frame = cv2.resize(frame, (w, h))
                img = ImageTk.PhotoImage(Image.fromarray(frame))
                lbl.imgtk = img
                lbl.configure(image=img)
                lbl.after(30, update_tr)
            update_tr()
        else:
            lbl = tk.Label(self.root)
            lbl.pack(fill="both", expand=True)
            img = self.img_orig.copy().resize((WIN_W, WIN_H), Image.LANCZOS)
            tkimg = ImageTk.PhotoImage(img)
            lbl.configure(image=tkimg)
            lbl.image = tkimg
            self.root.after(800, lambda: (lbl.destroy(), self._build_main()))

    # -----------------------------
    # MAIN UI: mapa, nodos, aristas visibles y controles
    # -----------------------------
    def _build_main(self):
        for w in self.root.winfo_children():
            w.destroy()

        left = tk.Frame(self.root, width=260, bg="#012428")
        left.pack(side="left", fill="y")
        right = tk.Frame(self.root, bg="black")
        right.pack(side="right", fill="both", expand=True)

        # fonts
        if getattr(self, "_fancy_font_available", False):
            font_title = (FANCY_FONT_FAMILY, 18, "bold")
            font_small = (FANCY_FONT_FAMILY, 12)
            font_btn = (FANCY_FONT_FAMILY, 11, "bold")
            font_result = (FANCY_FONT_FAMILY, 16, "bold")
        else:
            font_title = ("The-Wild-Breath-of-Zelda", 18, "bold") if self._registered_font else ("Segoe UI", 18, "bold")
            font_small = ("The-Wild-Breath-of-Zelda", 12) if self._registered_font else ("Segoe UI", 12)
            font_btn = ("The-Wild-Breath-of-Zelda", 11, "bold") if self._registered_font else ("Segoe UI", 11, "bold")
            font_result = ("The-Wild-Breath-of-Zelda", 16, "bold") if self._registered_font else ("Segoe UI", 16, "bold")

        tk.Label(left, text="Controles", bg="#012428", fg="white", font=font_title).pack(pady=12)

        btnk = {"bg": NODE_COLOR, "fg": "white", "font": font_btn, "bd": 0}
        tk.Button(left, text="Reiniciar aristas", command=self._reset_edges, **btnk).pack(fill="x", padx=12, pady=6)
        tk.Button(left, text="Seleccionar inicio/destino", command=self._set_select_start_end, **btnk).pack(fill="x", padx=12, pady=6)
        tk.Button(left, text="Ejecutar Dijkstra", command=self._on_execute_dijkstra, **btnk).pack(fill="x", padx=12, pady=6)
        tk.Button(left, text="Volver al menú", command=self._back_to_menu, **btnk).pack(fill="x", padx=12, pady=6)

        self.left_cost_var = tk.StringVar(value="Costo del viaje: --")
        tk.Label(left, textvariable=self.left_cost_var, bg="#012428", fg="white", font=font_result).pack(padx=8, pady=10)

        self.info_var = tk.StringVar(value=f"Modo elegido: {self.selected_mode}  — selecciona inicio y destino")
        tk.Label(left, textvariable=self.info_var, bg="#012428", fg="white", wraplength=220, font=font_small).pack(padx=8, pady=14)

        self.canvas = tk.Canvas(right, width=WIN_W, height=WIN_H, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # forzar layout y obtener tamaños reales antes de calcular escala
        self.root.update_idletasks()
        canvas_w = max(1, self.canvas.winfo_width())
        canvas_h = max(1, self.canvas.winfo_height())

        # usar "contain" (min) para que la imagen entre en el canvas sin recorte ni zoom
        scale_x = canvas_w / self.img_w
        scale_y = canvas_h / self.img_h
        scale = min(scale_x, scale_y)
        self.transform.scale = scale
        self.transform.offset_x = (canvas_w - self.img_w * scale) / 2
        self.transform.offset_y = (canvas_h - self.img_h * scale) / 2

        # dibujar estatico
        self._draw_background()
        self._create_nodes_and_edges()
        self._create_hud_title()

        # redibujar cuando cambie tamaño real del canvas (maneja inicio y fullscreen)
        def _on_canvas_config(event):
            try:
                canvas_w = max(1, event.width)
                canvas_h = max(1, event.height)
                scale_x = canvas_w / self.img_w
                scale_y = canvas_h / self.img_h
                scale = min(scale_x, scale_y)
                self.transform.scale = scale
                self.transform.offset_x = (canvas_w - self.img_w * scale) / 2
                self.transform.offset_y = (canvas_h - self.img_h * scale) / 2
                self._draw_background()
                self._create_nodes_and_edges()
                self._create_hud_title()
            except Exception:
                pass

        self.canvas.bind("<Configure>", _on_canvas_config)
        self.canvas.bind("<Button-1>", self._on_left_click)

        self.char_canvas_id = None

    # -----------------------------
    # Dibujar fondo (usar transform, evitar bordes negros)
    # -----------------------------
    def _draw_background(self):
        w = max(1, int(self.img_w * self.transform.scale))
        h = max(1, int(self.img_h * self.transform.scale))
        img = self.img_orig.copy().resize((w, h), Image.LANCZOS)
        self.tk_bg = ImageTk.PhotoImage(img)
        try:
            if hasattr(self, "bg_id") and self.bg_id:
                self.canvas.delete(self.bg_id)
        except:
            pass
        ox = int(round(self.transform.offset_x))
        oy = int(round(self.transform.offset_y))
        self.bg_id = self.canvas.create_image(ox, oy, anchor="nw", image=self.tk_bg)
        self.canvas.tag_lower(self.bg_id)

    # -----------------------------
    # Crear nodos y aristas alineados con la imagen
    # -----------------------------
    def _create_nodes_and_edges(self):
        for e in list(self.edges):
            try:
                self.canvas.delete(e["line"])
                self.canvas.delete(e["text_id"])
            except:
                pass
        for n in list(self.nodes):
            try:
                self.canvas.delete(n["oval"])
                self.canvas.delete(n["text"])
                self.canvas.delete(n["dist"])
            except:
                pass
        self.nodes = []
        self.edges = []

        if getattr(self, "_fancy_font_available", False):
            node_font = (FANCY_FONT_FAMILY, 9, "bold")
            dist_font = (FANCY_FONT_FAMILY, 8, "bold")
            edge_font = (FANCY_FONT_FAMILY, 10, "bold")
        else:
            node_font = ("The-Wild-Breath-of-Zelda", 9, "bold") if self._registered_font else ("Segoe UI", 9, "bold")
            dist_font = ("The-Wild-Breath-of-Zelda", 8, "bold") if self._registered_font else ("Segoe UI", 8, "bold")
            edge_font = ("The-Wild-Breath-of-Zelda", 10, "bold") if self._registered_font else ("Segoe UI", 10, "bold")

        for label, ix, iy in FIXED_NODES:
            cx, cy = self.transform.img_to_canvas(ix, iy)
            oval = self.canvas.create_oval(cx - NODE_RADIUS, cy - NODE_RADIUS, cx + NODE_RADIUS, cy + NODE_RADIUS,
                                           fill=NODE_COLOR, outline=NODE_OUTLINE, width=2, tags=("node",))
            txt = self.canvas.create_text(cx, cy, text=label, fill="black", font=node_font)
            dist_id = self.canvas.create_text(cx + DIST_OFFSET[0], cy + DIST_OFFSET[1], text="∞", fill="white", font=dist_font)
            node = {"label": label, "ix": ix, "iy": iy, "oval": oval, "text": txt, "dist": dist_id}
            self.nodes.append(node)
            self.canvas.tag_raise(oval)
            self.canvas.tag_raise(txt)
            self.canvas.tag_raise(dist_id)

        for u,v,w in BASE_EDGES:
            a = self._find_node_by_label(u)
            b = self._find_node_by_label(v)
            if a and b:
                ax, ay = self.transform.img_to_canvas(a["ix"], a["iy"])
                bx, by = self.transform.img_to_canvas(b["ix"], b["iy"])
                line = self.canvas.create_line(ax, ay, bx, by, fill=EDGE_COLOR, width=2)
                mx, my = (ax+bx)/2, (ay+by)/2
                text_id = self.canvas.create_text(mx, my, text=str(w), fill="yellow", font=edge_font)
                edge = {"u": u, "v": v, "line": line, "weight": w, "text_id": text_id, "base_weight": w}
                self.edges.append(edge)
                self.canvas.tag_raise(text_id)

    def _find_node_by_label(self, label):
        for n in self.nodes:
            if n["label"] == label:
                return n
        return None

    # -----------------------------
    # Interacción: seleccionar inicio/destino con clic izquierdo
    # -----------------------------
    def _on_left_click(self, event):
        node = self._node_at_canvas(event.x, event.y)
        if node:
            if self.mode == "select_start_end":
                self.dijkstra_sel.append(node)
                if len(self.dijkstra_sel) == 1:
                    self.info_var.set(f"Inicio seleccionado: {node['label']} — ahora selecciona destino")
                elif len(self.dijkstra_sel) == 2:
                    if self.dijkstra_sel[0]["label"] == self.dijkstra_sel[1]["label"]:
                        messagebox.showerror("Error", "Inicio y destino no pueden ser iguales")
                        self.dijkstra_sel = []
                        self.mode = "idle"
                        self.info_var.set("Modo idle")
                    else:
                        self.info_var.set(f"Inicio: {self.dijkstra_sel[0]['label']}  —  Destino: {self.dijkstra_sel[1]['label']}")
                        self.mode = "idle"
                        self._place_character_on_node(self.dijkstra_sel[0])
            else:
                self.info_var.set(f"Clic en nodo {node['label']}")

    def _node_at_canvas(self, cx, cy):
        for n in self.nodes:
            nx_c, ny_c = self.transform.img_to_canvas(n["ix"], n["iy"])
            r = NODE_RADIUS
            if (cx - nx_c) ** 2 + (cy - ny_c) ** 2 <= r * r:
                return n
        return None

    def _set_select_start_end(self):
        self.mode = "select_start_end"
        self.dijkstra_sel = []
        self.info_var.set("Selecciona primero el nodo de inicio, luego el nodo destino (clic izquierdo)")

    def _place_character_on_node(self, node):
        if self.char_canvas_id:
            try:
                self.canvas.delete(self.char_canvas_id)
            except:
                pass
            self.char_canvas_id = None
        key = self.selected_mode
        img = self.char_imgs.get(key)
        cx, cy = self.transform.img_to_canvas(node["ix"], node["iy"])
        if img is None:
            self.char_canvas_id = self.canvas.create_oval(cx-8, cy-8, cx+8, cy+8, fill="#ffcc66", outline="")
            self.char_img_tk = None
        else:
            self.char_img_tk = ImageTk.PhotoImage(img)
            self.char_canvas_id = self.canvas.create_image(cx, cy - NODE_RADIUS - 10, image=self.char_img_tk)

    # -----------------------------
    # Ejecutar Dijkstra con pasos guardados y animación
    # -----------------------------
    def _on_execute_dijkstra(self):
        if len(self.dijkstra_sel) != 2:
            messagebox.showwarning("Falta selección", "Selecciona primero nodo inicio y destino (Seleccionar inicio/destino).")
            return
        if not self.selected_mode:
            messagebox.showwarning("Falta modo", "Selecciona un modo desde el menú inicial.")
            return

        start_label = self.dijkstra_sel[0]["label"]
        end_label = self.dijkstra_sel[1]["label"]

        mult = MODE_MULT.get(self.selected_mode, 1.0)
        graph = {}
        labels = [n["label"] for n in self.nodes]
        for l in labels:
            graph[l] = {}
        for e in self.edges:
            u = e["u"]; v = e["v"]
            w = e["base_weight"] * mult
            graph[u][v] = w
            graph[v][u] = w

        dist = {l: float("inf") for l in labels}
        prev = {l: None for l in labels}
        dist[start_label] = 0
        pq = [(0, start_label)]
        visited = set()
        steps = []
        while pq:
            d,u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            steps.append(("explore", u, dict(dist), set(visited)))
            for v,w in graph[u].items():
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    prev[v] = u
                    heapq.heappush(pq, (dist[v], v))
                    steps.append(("relax", u, v, dict(dist), set(visited)))

        if dist[end_label] == float("inf"):
            messagebox.showinfo("Resultado", f"No hay camino desde {start_label} hasta {end_label}")
            return

        tiempo = dist[end_label]

        path = []
        cur = end_label
        while cur is not None:
            path.insert(0, cur)
            cur = prev[cur]
        steps.append(("final", path, dict(dist), set(visited)))

        # mostrar coste solo en panel izquierdo
        self.left_cost_var.set(f"Costo del viaje: {tiempo:.1f} minutos")

        total_frames = self._estimate_total_frames_for_path(path)
        total_move_time_ms = max(1, total_frames * MOVE_STEP_MS)

        self._start_counter_animation(target=tiempo, duration_ms=total_move_time_ms)

        self.animating = True
        self._animate_steps(steps, 0, path)

    def _estimate_total_frames_for_path(self, path_labels):
        frames = 0
        for i in range(len(path_labels)-1):
            a_label = path_labels[i]; b_label = path_labels[i+1]
            a = self._find_node_by_label(a_label); b = self._find_node_by_label(b_label)
            ax, ay = self.transform.img_to_canvas(a["ix"], a["iy"])
            bx, by = self.transform.img_to_canvas(b["ix"], b["iy"])
            dist_px = math.hypot(bx-ax, by-ay)
            steps = max(1, int(dist_px / MOVE_STEP_PX))
            frames += steps
        return frames

    def _animate_steps(self, steps, idx, final_path):
        if idx >= len(steps):
            self.animating = False
            self._prepare_move_frames(final_path)
            self._move_frame_idx = 0
            self._animate_move_frame()
            return
        step = steps[idx]
        typ = step[0]
        if typ == "explore":
            _, u, dists, visited = step
            self.info_var.set(f"Explorando: {u}")
            self._update_visual_state(current=u, distances=dists, visited=visited, highlight_edge=None, path=None)
        elif typ == "relax":
            _, u, v, dists, visited = step
            self.info_var.set(f"Relajando: {u} → {v}")
            line_id = None
            for e in self.edges:
                if (e["u"] == u and e["v"] == v) or (e["u"] == v and e["v"] == u):
                    line_id = e["line"]
                    break
            self._update_visual_state(current=u, distances=dists, visited=visited, highlight_edge=line_id, path=None)
        elif typ == "final":
            _, path, dists, visited = step
            self.info_var.set(f"Camino final: {' → '.join(path)}")
            self._update_visual_state(current=None, distances=dists, visited=visited, highlight_edge=None, path=path)
        self.root.after(ANIM_DELAY_MS, lambda: self._animate_steps(steps, idx+1, final_path))

    def _update_visual_state(self, current=None, distances=None, visited=None, highlight_edge=None, path=None):
        distances = distances or {}
        visited = visited or set()
        for n in self.nodes:
            label = n["label"]
            cx, cy = self.transform.img_to_canvas(n["ix"], n["iy"])
            self.canvas.coords(n["oval"], cx - NODE_RADIUS, cy - NODE_RADIUS, cx + NODE_RADIUS, cy + NODE_RADIUS)
            self.canvas.coords(n["text"], cx, cy)
            self.canvas.coords(n["dist"], cx + DIST_OFFSET[0], cy + DIST_OFFSET[1])
            fill = NODE_COLOR
            if path and label in path:
                fill = NODE_CURRENT
            elif label == current:
                fill = NODE_CURRENT
            elif label in visited:
                fill = NODE_VISITED
            self.canvas.itemconfig(n["oval"], fill=fill)
            txt = "∞"
            if label in distances:
                v = distances[label]
                txt = "∞" if v == float('inf') else f"{v:.1f}"
            self.canvas.itemconfig(n["dist"], text=txt)
        for e in self.edges:
            a = self._find_node_by_label(e["u"]); b = self._find_node_by_label(e["v"])
            ax, ay = self.transform.img_to_canvas(a["ix"], a["iy"])
            bx, by = self.transform.img_to_canvas(b["ix"], b["iy"])
            self.canvas.coords(e["line"], ax, ay, bx, by)
            mx, my = (ax+bx)/2, (ay+by)/2
            self.canvas.coords(e["text_id"], mx, my)
            col = EDGE_COLOR; width = 2
            if highlight_edge and e["line"] == highlight_edge:
                col = EDGE_HIGHLIGHT; width = 4
            if path:
                pairs = list(zip(path[:-1], path[1:]))
                if (e["u"], e["v"]) in pairs or (e["v"], e["u"]) in pairs:
                    col = EDGE_PATH; width = 4
            self.canvas.itemconfig(e["line"], fill=col, width=width)
        self.canvas.update()

    def _prepare_move_frames(self, path_labels):
        frames = []
        for i in range(len(path_labels)-1):
            a_label = path_labels[i]; b_label = path_labels[i+1]
            a = self._find_node_by_label(a_label); b = self._find_node_by_label(b_label)
            ax, ay = self.transform.img_to_canvas(a["ix"], a["iy"])
            bx, by = self.transform.img_to_canvas(b["ix"], b["iy"])
            dist_px = math.hypot(bx-ax, by-ay)
            steps = max(1, int(dist_px / MOVE_STEP_PX))
            for s in range(1, steps+1):
                t = s / steps
                nx = ax + (bx-ax) * t
                ny = ay + (by-ay) * t
                frames.append((nx, ny))
            frames.append((bx, by))
        self._move_frames = frames

    def _animate_move_frame(self):
        if not self._move_frames or self._move_frame_idx >= len(self._move_frames):
            self.info_var.set("Movimiento completado — camino mostrado")
            return
        nx, ny = self._move_frames[self._move_frame_idx]
        if self.char_img_tk:
            self.canvas.coords(self.char_canvas_id, nx, ny - NODE_RADIUS - 10)
        else:
            self.canvas.coords(self.char_canvas_id, nx-8, ny-8, nx+8, ny+8)
        self._move_frame_idx += 1
        self.canvas.update()
        self.root.after(MOVE_STEP_MS, self._animate_move_frame)

    # -----------------------------
    # Contador progresivo interno
    # -----------------------------
    def _start_counter_animation(self, target, duration_ms):
        if self._counter_after_id:
            try:
                self.root.after_cancel(self._counter_after_id)
            except:
                pass
            self._counter_after_id = None
        self._counter_current = 0.0
        self._counter_target = float(target)
        self._counter_duration_ms = max(1, int(duration_ms))
        self._counter_start_time = None
        self._counter_update_interval = 30
        self._counter_tick()

    def _counter_tick(self):
        import time
        now = int(round(time.time() * 1000))
        if self._counter_start_time is None:
            self._counter_start_time = now
            elapsed = 0
        else:
            elapsed = now - self._counter_start_time
        t = min(1.0, elapsed / max(1, self._counter_duration_ms))
        eased = 1 - (1 - t) * (1 - t)
        value = eased * self._counter_target
        self._counter_current = value
        self.info_var.set(f"Contador: {self._counter_current:.1f} minutos")
        if t >= 1.0:
            self._counter_after_id = None
            self.info_var.set(f"Contador: {self._counter_target:.1f} minutos")
            return
        self._counter_after_id = self.root.after(self._counter_update_interval, self._counter_tick)

    # -----------------------------
    # Utilities
    # -----------------------------
    def _reset_edges(self):
        for e in list(self.edges):
            try:
                self.canvas.delete(e["line"])
                self.canvas.delete(e["text_id"])
            except:
                pass
        self.edges = []
        edge_font = (FANCY_FONT_FAMILY, 10, "bold") if getattr(self, "_fancy_font_available", False) else (("The-Wild-Breath-of-Zelda", 10, "bold") if self._registered_font else ("Segoe UI", 10, "bold"))
        for u,v,w in BASE_EDGES:
            a = self._find_node_by_label(u)
            b = self._find_node_by_label(v)
            if a and b:
                ax, ay = self.transform.img_to_canvas(a["ix"], a["iy"])
                bx, by = self.transform.img_to_canvas(b["ix"], b["iy"])
                line = self.canvas.create_line(ax, ay, bx, by, fill=EDGE_COLOR, width=2)
                mx, my = (ax+bx)/2, (ay+by)/2
                text_id = self.canvas.create_text(mx, my, text=str(w), fill="yellow", font=edge_font)
                edge = {"u": u, "v": v, "line": line, "weight": w, "text_id": text_id, "base_weight": w}
                self.edges.append(edge)
        self._draw_background()
        for e in self.edges:
            a = self._find_node_by_label(e["u"]); b = self._find_node_by_label(e["v"])
            ax, ay = self.transform.img_to_canvas(a["ix"], a["iy"])
            bx, by = self.transform.img_to_canvas(b["ix"], b["iy"])
            self.canvas.coords(e["line"], ax, ay, bx, by)
        self.info_var.set("Aristas reiniciadas")

    def _back_to_menu(self):
        if messagebox.askyesno("Volver", "¿Volver al menú y elegir otro modo?"):
            for w in self.root.winfo_children():
                w.destroy()
            self.selected_mode = None
            self._build_menu()

    # -----------------------------
    # Fullscreen handlers
    # -----------------------------
    def _toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)
        try:
            canvas_w = max(1, self.canvas.winfo_width())
            canvas_h = max(1, self.canvas.winfo_height())
            scale_x = canvas_w / self.img_w
            scale_y = canvas_h / self.img_h
            scale = min(scale_x, scale_y)
            self.transform.scale = scale
            self.transform.offset_x = (canvas_w - self.img_w * scale) / 2
            self.transform.offset_y = (canvas_h - self.img_h * scale) / 2
            self._draw_background()
            self._create_nodes_and_edges()
            self._create_hud_title()
        except Exception:
            pass

    def _exit_fullscreen(self):
        self.fullscreen = False
        self.root.attributes("-fullscreen", False)
        try:
            canvas_w = max(1, self.canvas.winfo_width())
            canvas_h = max(1, self.canvas.winfo_height())
            scale_x = canvas_w / self.img_w
            scale_y = canvas_h / self.img_h
            scale = min(scale_x, scale_y)
            self.transform.scale = scale
            self.transform.offset_x = (canvas_w - self.img_w * scale) / 2
            self.transform.offset_y = (canvas_h - self.img_h * scale) / 2
            self._draw_background()
            self._create_nodes_and_edges()
            self._create_hud_title()
        except Exception:
            pass

    # -----------------------------
    # HUD título fijo
    # -----------------------------
    def _create_hud_title(self):
        title_text = "Viaje por Hyrule"
        try:
            if hasattr(self, "hud_title_id") and self.hud_title_id:
                self.canvas.delete(self.hud_title_id)
        except:
            pass
        if getattr(self, "_fancy_font_available", False):
            hud_font = (FANCY_FONT_FAMILY, 18, "bold")
        else:
            hud_font = ("The-Wild-Breath-of-Zelda", 18, "bold") if self._registered_font else ("Segoe UI", 18, "bold")
        self.hud_title_id = self.canvas.create_text(120, 24, text=title_text, anchor="center", font=hud_font, fill="white")
        self.canvas.tag_raise(self.hud_title_id)

# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = DijkstraApp(root)
    root.mainloop()