import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

# =========================
# Config colores / estilos
# =========================
BG_MAIN = "#1e1e1e"
BG_PANEL = "#242830"
BG_CANVAS = "#2e3241"
ACCENT_A = "#61afef"
ACCENT_B = "#9ecf83"
ERROR = "#e06c75"
TEXT = "#e6eef6"

# =========================
# Animación slide-in para frames
# =========================
def slide_in_frame(container, new_frame, direction="right", step=30, delay=8):
    container.update_idletasks()
    w = container.winfo_width() or 900
    start_x = w if direction == "right" else -w
    new_frame.place(x=start_x, y=0, relwidth=1, relheight=1)
    new_frame.lift()
    def anim(x):
        if (direction == "right" and x <= 0) or (direction == "left" and x >= 0):
            new_frame.place(x=0, y=0)
            return
        x += -step if direction == "right" else step
        new_frame.place(x=x, y=0)
        container.update()
        new_frame.after(delay, lambda: anim(x))
    anim(start_x)

# =========================
# App base
# =========================
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Método de Euclides — Automático y Manual")
        self.geometry("980x640")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)

        # Contenedor principal
        self.container = tk.Frame(self, bg=BG_MAIN)
        self.container.pack(fill="both", expand=True)

        # Crear frames y colocarlos, listos para slide
        self.frames = {}
        for F in (MainMenu, SubMenuEuclides, EuclidesAutomaticFrame, EuclidesManualFrame):
            frame = F(parent=self.container, controller=self)
            self.frames[F] = frame
            frame.place(relwidth=1, relheight=1)

        self.current = None
        self.show_frame(MainMenu, animate=False)

    def show_frame(self, cls, animate=True, direction="right"):
        frame = self.frames[cls]
        if animate and self.current is not None:
            slide_in_frame(self.container, frame, direction=direction)
        else:
            frame.place(x=0, y=0, relwidth=1, relheight=1)
            frame.lift()
        self.current = frame

# =========================
# MainMenu
# =========================
class MainMenu(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_MAIN)
        self.controller = controller

        tk.Label(self, text="🧮 Calculadora del Método de Euclides",
                 font=("Segoe UI", 24, "bold"), fg=ACCENT_A, bg=BG_MAIN).pack(pady=44)

        tk.Label(self, text="Selecciona modo", font=("Segoe UI", 14), fg=TEXT, bg=BG_MAIN).pack(pady=(0,6))

        btn_style = {"font": ("Segoe UI", 14, "bold"), "width": 30, "height": 2, "bd": 0, "cursor": "hand2"}

        tk.Button(self, text="⚙️ Método de Euclides", bg="#282c34", fg=ACCENT_A,
                  command=lambda: controller.show_frame(SubMenuEuclides), **btn_style).pack(pady=12)
        tk.Button(self, text="🚪 Salir", bg=ERROR, fg="white",
                  command=controller.destroy, **btn_style).pack(pady=12)

# =========================
# Submenu: elegir Automático / Manual
# =========================
class SubMenuEuclides(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_PANEL)
        self.controller = controller

        top = tk.Frame(self, bg=BG_PANEL)
        top.pack(fill="x", pady=8, padx=8)
        tk.Button(top, text="⬅ Volver", bg="#3a3f46", fg=TEXT, bd=0, cursor="hand2",
                  command=lambda: controller.show_frame(MainMenu, direction="left")).pack(side="left")
        tk.Label(top, text="Método de Euclides — Selecciona Modo",
                 font=("Segoe UI", 20, "bold"), fg=ACCENT_A, bg=BG_PANEL).pack(side="left", padx=12)

        body = tk.Frame(self, bg=BG_PANEL)
        body.pack(expand=True)

        btn_style = {"font": ("Segoe UI", 16, "bold"), "width": 30, "height": 2, "bd": 0, "cursor": "hand2"}
        tk.Button(body, text="🔁 Modo Automático", bg=ACCENT_B, fg="#242830",
                  command=lambda: controller.show_frame(EuclidesAutomaticFrame, direction="right"), **btn_style).pack(pady=18)
        tk.Button(body, text="✋ Modo Manual", bg=ACCENT_A, fg="#242830",
                  command=lambda: controller.show_frame(EuclidesManualFrame, direction="left"), **btn_style).pack(pady=18)

# =========================
# Euclides Automático (mantener diseño)
# =========================
class EuclidesAutomaticFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_PANEL)
        self.controller = controller

        header = tk.Frame(self, bg=BG_PANEL)
        header.pack(fill="x", pady=10)
        tk.Button(header, text="⬅ Volver", bg="#3a3f46", fg=TEXT, bd=0, cursor="hand2",
                  command=lambda: controller.show_frame(SubMenuEuclides, direction="left")).pack(side="left", padx=8)
        tk.Label(header, text="Algoritmo de Euclides — Modo Automático",
                 font=("Segoe UI", 20, "bold"), fg="#55c1de", bg=BG_PANEL).pack(padx=12, pady=6)

        # Scroll vertical
        self.canvas = tk.Canvas(self, bg=BG_PANEL, highlightthickness=0)
        self.scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable = tk.Frame(self.canvas, bg=BG_PANEL)
        self.canvas.create_window((0,0), window=self.scrollable, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll_y.pack(side="right", fill="y")
        self.scrollable.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # entradas
        self.entries = []
        entry_frame = tk.Frame(self.scrollable, bg=BG_PANEL)
        entry_frame.pack(pady=10)
        for i, txt in enumerate(["Número A:", "Número B:", "Número C (opcional):"]):
            tk.Label(entry_frame, text=txt, font=("Segoe UI", 12), fg="#b3b8cc", bg=BG_PANEL).grid(row=i, column=0, padx=6, pady=6)
            e = tk.Entry(entry_frame, width=16, font=("Segoe UI", 12), justify="center", bg=BG_CANVAS, fg=TEXT, bd=0)
            e.grid(row=i, column=1, padx=6, pady=6)
            self.entries.append(e)

        tk.Label(self.scrollable, text="(Puedes poner los 3 valores separados por comas o espacios)",
                 font=("Segoe UI", 9), fg="#9aa8b6", bg=BG_PANEL).pack()

        # area donde aparecerán los botones de opción para 3 valores
        self.opts_frame = tk.Frame(self.scrollable, bg=BG_PANEL)
        self.opts_frame.pack()

        tk.Button(self.scrollable, text="🧮 Calcular", bg=ACCENT_B, fg="#242830", bd=0,
                  font=("Segoe UI", 12, "bold"), command=self.calcular).pack(pady=8)
        tk.Button(self.scrollable, text="🗑 Limpiar", bg=ERROR, fg="white", bd=0,
                  font=("Segoe UI", 12, "bold"), command=self.limpiar).pack(pady=4)

        self.info_lbl = tk.Label(self.scrollable, text="", fg=ERROR, bg=BG_PANEL, font=("Segoe UI", 12))
        self.info_lbl.pack(pady=6)

        self.tables = []

    def limpiar(self):
        for e in self.entries:
            e.delete(0, tk.END)
        for t in self.tables:
            t.destroy()
        self.tables.clear()
        self.info_lbl.config(text="")
        for w in self.opts_frame.winfo_children():
            w.destroy()

    def calcular(self):
        # limpiar botones previos de opciones si hay
        for w in self.opts_frame.winfo_children():
            w.destroy()

        # parse inputs up to 3 numbers
        try:
            parts = []
            for e in self.entries:
                v = e.get().strip()
                if v:
                    parts.extend(v.replace(",", " ").split())
            nums = [int(p) for p in parts][:3]
        except Exception:
            self.info_lbl.config(text="⚠ Solo se permiten números enteros.")
            return
        if len(nums) < 2:
            self.info_lbl.config(text="⚠ Ingresa al menos dos números.")
            return

        if len(nums) == 2:
            # comportamiento directo con 2 valores
            threading.Thread(target=self._run_direct, args=(nums[0], nums[1])).start()
        else:
            # si hay 3 valores, mostrar tres botones justo debajo del Calcular con los valores numericos
            a, b, c = nums
            tk.Label(self.opts_frame, text="Elige los dos valores para operar primero:", fg=ACCENT_B, bg=BG_PANEL,
                     font=("Segoe UI", 11, "bold")).pack(pady=(6,2))
            # opciones con los valores (no letras)
            opts = [ (f"{a} y {b}", (a,b,c)), (f"{a} y {c}", (a,c,b)), (f"{b} y {c}", (b,c,a)) ]
            for txt, data in opts:
                btn = tk.Button(self.opts_frame, text=txt, bg="#4e5663", fg="white", bd=0, width=18, cursor="hand2",
                                command=lambda d=data: threading.Thread(target=self._start_three, args=(d,)).start())
                btn.pack(pady=4)
            self.info_lbl.config(text="Selecciona una opción para que el modo automático opere automáticamente.", fg=TEXT)

    def _run_direct(self, a, b):
        self.info_lbl.config(text=f"Calculando MCD({a}, {b})...")
        m = self._draw_table(a, b)
        self.info_lbl.config(text=f"🏁 MCD = {m}", fg=ACCENT_B)

    def _start_three(self, data):
        # data is (a,b,c) where a and b are to be used first, c remaining
        a, b, c = data
        self.info_lbl.config(text=f"Calculando MCD({a}, {b})...", fg=ACCENT_A)
        m1 = self._draw_table(a, b)
        time.sleep(0.6)
        self.info_lbl.config(text=f"Calculando MCD({m1}, {c})...", fg=ACCENT_A)
        m2 = self._draw_table(m1, c)
        self.info_lbl.config(text=f"🏁 MCD Final = {m2}", fg=ACCENT_B)

    def _draw_table(self, a, b):
        """
        Dibuja tabla exactamente como se requiere para el modo Automático.
        Esta función está diseñada para ser llamada desde otras partes del programa.
        """
        frame = tk.Frame(self.scrollable, bg=BG_PANEL)
        frame.pack(pady=14, fill="x")
        self.tables.append(frame)
        tk.Label(frame, text=f"Operación: MCD({a}, {b})", fg=ACCENT_A, bg=BG_PANEL, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=10)
        canvas = tk.Canvas(frame, bg=BG_CANVAS, height=220, width=860, highlightthickness=0)
        canvas.pack(fill="x", padx=12, pady=6)
        paso = 0; x = 60; colw = 140
        # Dibujar mientras b != 0; cada iteración dibuja la columna correspondiente (incluye el paso que produce residuo 0)
        while b != 0:
            paso += 1
            q = a // b
            r = a % b
            # three-cell column
            for i in range(3):
                canvas.create_rectangle(x, 50 + i*45, x + colw, 95 + i*45, outline="#555", width=1)
            canvas.create_text(x + colw/2, 30, text=f"Paso {paso}", font=("Segoe UI", 10, "italic"), fill=ACCENT_A)
            canvas.create_text(x - 30, 50 + 45 + 22, text=str(a), font=("Segoe UI", 11, "bold"), fill=ACCENT_A)
            canvas.create_text(x + colw/2, 50 + 22, text=f"Cociente: {q}", font=("Segoe UI", 11, "bold"), fill=ACCENT_B)
            canvas.create_text(x + colw/2, 50 + 45 + 22, text=f"Divisor: {b}", font=("Segoe UI", 11, "bold"), fill="#e5c07b")
            canvas.create_text(x + colw/2, 50 + 90 + 22, text=f"Residuo: {r}", font=("Segoe UI", 11, "bold"), fill="#d19a66")
            a, b = b, r
            canvas.update()
            time.sleep(0.35)
            x += colw + 40
        return a

# =========================
# Euclides Manual Frame
# =========================
class EuclidesManualFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_PANEL)
        self.controller = controller

        # header con volver (vuelve al SubMenu)
        top = tk.Frame(self, bg=BG_PANEL)
        top.pack(fill="x", pady=8)
        tk.Button(top, text="⬅ Volver", bg="#3a3f46", fg=TEXT, bd=0, cursor="hand2",
                  command=lambda: controller.show_frame(SubMenuEuclides, direction="right")).pack(side="left", padx=8)
        tk.Label(top, text="Algoritmo de Euclides — Modo Manual", font=("Segoe UI", 18, "bold"),
                 fg=ACCENT_A, bg=BG_PANEL).pack(side="left", padx=12)

        # scrollable area (vertical + horizontal)
        self.canvas = tk.Canvas(self, bg=BG_PANEL, highlightthickness=0)
        self.scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        self.inner = tk.Frame(self.canvas, bg=BG_PANEL)
        self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x.pack(side="bottom", fill="x")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # controls (entradas y botones)
        controls = tk.Frame(self.inner, bg=BG_PANEL)
        controls.pack(pady=10, fill="x")

        left = tk.Frame(controls, bg=BG_PANEL)
        left.pack(side="left", padx=12)
        tk.Label(left, text="Número A:", bg=BG_PANEL, fg=TEXT).pack(anchor="w")
        self.e_a = tk.Entry(left, width=14, font=("Segoe UI",12), justify="center", bg=BG_CANVAS, fg=TEXT, bd=0)
        self.e_a.pack(pady=6)
        tk.Label(left, text="Número B:", bg=BG_PANEL, fg=TEXT).pack(anchor="w")
        self.e_b = tk.Entry(left, width=14, font=("Segoe UI",12), justify="center", bg=BG_CANVAS, fg=TEXT, bd=0)
        self.e_b.pack(pady=6)
        tk.Label(left, text="Número C (opcional):", bg=BG_PANEL, fg=TEXT).pack(anchor="w")
        self.e_c = tk.Entry(left, width=14, font=("Segoe UI",12), justify="center", bg=BG_CANVAS, fg=TEXT, bd=0)
        self.e_c.pack(pady=6)

        # right controls: nueva disposición (reemplazamos 'Iniciar con A,B,C' por 'Comprobar en modo automático')
        right = tk.Frame(controls, bg=BG_PANEL)
        right.pack(side="right", padx=12)
        tk.Button(right, text="🧮 Abrir Calculadora Universal", bg=ACCENT_B, fg="#242830", bd=0,
                  font=("Segoe UI",12,"bold"), width=24, cursor="hand2", command=self.open_calculator_universal).pack(pady=6)

        # REEMPLAZADO: botón que antes iniciaba con A,B,C -> ahora comprueba y manda al modo automático (prefill)
        tk.Button(right, text="🔁 Comprobar en modo automático", bg=ACCENT_A, fg="#242830", bd=0,
                  font=("Segoe UI",12,"bold"), width=24, cursor="hand2", command=self.check_and_go_automatic).pack(pady=6)

        tk.Button(right, text="🗑 Limpiar todo", bg=ERROR, fg="white", bd=0,
                  font=("Segoe UI",12,"bold"), width=24, cursor="hand2", command=self.clear_all).pack(pady=6)

        # tabla manual (usar mismo diseño visual que automatico)
        self.manual_container = tk.Frame(self.inner, bg=BG_CANVAS)
        self.manual_container.pack(padx=12, pady=12, fill="x")
        tk.Label(self.manual_container, text="Tabla Manual (pasos añadidos desde la calculadora)", bg=BG_CANVAS,
                 fg=ACCENT_A, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=6, pady=(6,4))

        self.steps_container = tk.Frame(self.manual_container, bg=BG_CANVAS)
        self.steps_container.pack(fill="x", padx=6, pady=6)

        # mensajes
        self.msg_label = tk.Label(self.inner, text="", bg=BG_PANEL, fg=ERROR, font=("Segoe UI", 12))
        self.msg_label.pack(pady=(6,12))

        # internal state
        self.steps = []  # lista de (D,S,q,r)

    def check_and_go_automatic(self):
        """
        Valida entradas A/B/(C opcional). Si A y B (al menos) están bien,
        rellena las entradas del frame Automático y navega a él.
        """
        parts = []
        for e in (self.e_a, self.e_b, self.e_c):
            v = e.get().strip()
            if v:
                parts.extend(v.replace(",", " ").split())
        try:
            nums = [int(p) for p in parts]
        except Exception:
            messagebox.showwarning("Entrada inválida", "Solo se permiten enteros en A,B,C.")
            return

        if len(nums) < 2:
            messagebox.showwarning("Datos insuficientes", "Debes ingresar al menos A y B para comprobar en modo automático.")
            return

        # prefill Automatic frame entries (0..2)
        auto_frame = self.controller.frames[EuclidesAutomaticFrame]
        # clear previous
        for e in auto_frame.entries:
            e.delete(0, tk.END)
        # insert values (up to 3)
        for i, val in enumerate(nums[:3]):
            if i < len(auto_frame.entries):
                auto_frame.entries[i].insert(0, str(val))

        # ensure any previous option buttons in automatic are removed
        try:
            auto_frame.limpiar()
        except Exception:
            pass

        # show automatic frame
        self.controller.show_frame(EuclidesAutomaticFrame, animate=True, direction="right")

    # --------------------------
    # Abrir Calculadora Universal: requiere que A y B existan y sean enteros
    # --------------------------
    def open_calculator_universal(self):
        a = self.e_a.get().strip()
        b = self.e_b.get().strip()
        if not a or not b:
            messagebox.showwarning("Datos insuficientes", "Debes ingresar al menos los valores A y B antes de abrir la calculadora.")
            return
        try:
            int(a); int(b)
        except ValueError:
            messagebox.showwarning("Entrada inválida", "A y B deben ser números enteros válidos.")
            return
        popup = CalculadoraUniversal(self, int(a), int(b))
        popup.slide_in()

    # --------------------------
    # (métodos auxiliares)
    # --------------------------
    def _add_step(self, D, S, q, r):
        self.steps.append((D, S, q, r))
        row = tk.Frame(self.steps_container, bg=BG_CANVAS)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=f"Dividendo: {D}", bg=BG_CANVAS, fg=ACCENT_A, font=("Segoe UI", 11)).pack(side="left", padx=8)
        tk.Label(row, text=f"Divisor: {S}", bg=BG_CANVAS, fg="#e5c07b", font=("Segoe UI", 11)).pack(side="left", padx=8)
        tk.Label(row, text=f"Cociente: {q}", bg=BG_CANVAS, fg=ACCENT_B, font=("Segoe UI", 11)).pack(side="left", padx=8)
        tk.Label(row, text=f"Residuo: {r}", bg=BG_CANVAS, fg="#d19a66", font=("Segoe UI", 11, "bold")).pack(side="left", padx=8)
        if r == 0:
            tk.Label(row, text=f" ✨ MCD local = {S}", bg=BG_CANVAS, fg=ACCENT_B, font=("Segoe UI", 11, "bold")).pack(side="left", padx=8)
        self.msg_label.config(text=f"Paso agregado: {D} = {S}*{q} + {r}", fg=ACCENT_A)
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except:
            pass

    def _create_table_visual(self, a, b, add_import_button=False, import_target=None):
        frame = tk.Frame(self.steps_container, bg=BG_CANVAS)
        frame.pack(pady=10, fill="x")
        tk.Label(frame, text=f"Operación: MCD({a}, {b})", fg=ACCENT_A, bg=BG_CANVAS, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=6)
        canvas = tk.Canvas(frame, bg=BG_CANVAS, height=200, width=860, highlightthickness=0)
        canvas.pack(fill="x", padx=6, pady=6)
        paso = 0; x = 60; colw = 140
        while b != 0:
            paso += 1
            q = a // b
            r = a % b
            for i in range(3):
                canvas.create_rectangle(x, 50 + i*45, x + colw, 95 + i*45, outline="#555", width=1)
            canvas.create_text(x + colw/2, 30, text=f"Paso {paso}", font=("Segoe UI", 10, "italic"), fill=ACCENT_A)
            canvas.create_text(x - 30, 50 + 45 + 22, text=str(a), font=("Segoe UI", 11, "bold"), fill=ACCENT_A)
            canvas.create_text(x + colw/2, 50 + 22, text=f"Cociente: {q}", font=("Segoe UI", 11, "bold"), fill=ACCENT_B)
            canvas.create_text(x + colw/2, 50 + 45 + 22, text=f"Divisor: {b}", font=("Segoe UI", 11, "bold"), fill="#e5c07b")
            canvas.create_text(x + colw/2, 50 + 90 + 22, text=f"Residuo: {r}", font=("Segoe UI", 11, "bold"), fill="#d19a66")
            a, b = b, r
            canvas.update()
            time.sleep(0.25)
            x += colw + 40
        m = a
        # add import button if requested (bottom-right of the table frame)
        if add_import_button and import_target is not None:
            m_val, next_c = import_target
            def do_import():
                try:
                    app = self.controller
                    auto_frame = app.frames[EuclidesAutomaticFrame]
                    threading.Thread(target=lambda: auto_frame._draw_table(m_val, next_c)).start()
                except Exception as e:
                    print("Error importando desde manual:", e)
            btn = tk.Button(frame, text="Importar esta", bg=ACCENT_B, fg="#242830", bd=0, cursor="hand2",
                            font=("Segoe UI", 10, "bold"), command=do_import)
            btn.pack(side="right", padx=10, pady=6)
        return m

    def go_to_automatic(self):
        self.controller.show_frame(EuclidesAutomaticFrame, animate=True, direction="right")

    def verify_result(self):
        if not self.steps:
            self.msg_label.config(text="⚠ No hay pasos para verificar.", fg=ERROR)
            return
        ok = True
        for (D,S,q,r) in self.steps:
            if D != S * q + r or r < 0:
                ok = False
                break
        if ok:
            self.msg_label.config(text="✅ Los pasos son consistentes.", fg=ACCENT_B)
        else:
            self.msg_label.config(text="❌ Hay errores en los pasos.", fg=ERROR)

    def clear_all(self):
        self.e_a.delete(0, tk.END)
        self.e_b.delete(0, tk.END)
        self.e_c.delete(0, tk.END)
        for child in self.steps_container.winfo_children():
            child.destroy()
        self.steps.clear()
        self.msg_label.config(text="")
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        except:
            pass

# =========================
# Calculadora Universal (con scrolls)
# =========================
class CalculadoraUniversal(tk.Toplevel):
    def __init__(self, parent, a, b):
        super().__init__(parent)
        self.parent = parent  # EuclidesManualFrame instance
        self.configure(bg=BG_PANEL)
        self.title("Calculadora Universal")
        self.resizable(False, False)

        # tamaño y centrado
        self.w = 420
        self.h = 520
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        x = (sw - self.w) // 2
        y = (sh - self.h) // 2
        self.geometry(f"{self.w}x{self.h}+{x}+{y}")

        # container con canvas + scrollbars (vertical + horizontal)
        outer = tk.Frame(self, bg=BG_PANEL)
        outer.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(outer, bg=BG_PANEL, highlightthickness=0)
        self.scroll_y = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.scroll_x = ttk.Scrollbar(outer, orient="horizontal", command=self.canvas.xview)
        self.inner = tk.Frame(self.canvas, bg=BG_PANEL)
        self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x.pack(side="bottom", fill="x")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # display
        self.display = tk.Entry(self.inner, font=("Segoe UI", 16), justify="right", bd=0, relief="flat",
                                bg=BG_CANVAS, fg=ACCENT_A, insertbackground=TEXT)
        self.display.pack(fill="x", pady=(8,8), padx=12)

        # keypad (simple)
        keys_frame = tk.Frame(self.inner, bg=BG_PANEL)
        keys_frame.pack(pady=(0,8))
        keys = [
            ("7","8","9","/"),
            ("4","5","6","*"),
            ("1","2","3","-"),
            ("0","C","=","+")
        ]
        for row in keys:
            rf = tk.Frame(keys_frame, bg=BG_PANEL)
            rf.pack()
            for k in row:
                tk.Button(rf, text=k, width=6, height=2, bd=0, bg="#3b4048", fg=TEXT,
                          font=("Segoe UI", 11, "bold"), cursor="hand2",
                          command=lambda t=k: self._on_key(t)).pack(side="left", padx=6, pady=6)

        # Botón para abrir la Casita (prefill A,B) -> ahora la Casita usa nuevo diseño
        tk.Button(self.inner, text="∞ Casita (división)", bg="#4e5663", fg="white", bd=0,
                  font=("Segoe UI", 11, "bold"), width=26, cursor="hand2",
                  command=lambda: SpecialCasitaPopup(self.parent, prefill=(a,b)).slide_in()).pack(pady=(6,6))

        tk.Label(self.inner, text="Abre la casita para división manual (interactiva).", bg=BG_PANEL, fg="#bfc9d8",
                 font=("Segoe UI", 9)).pack(pady=(0,8))

        tk.Button(self.inner, text="Cerrar", bg="#6b6f76", fg=TEXT, bd=0,
                  font=("Segoe UI", 12), width=10, command=self._on_close).pack(pady=8)

    def _on_key(self, key):
        if key == "C":
            self.display.delete(0, tk.END)
            return
        if key == "=":
            expr = self.display.get()
            try:
                val = eval(expr)
                self.display.delete(0, tk.END)
                self.display.insert(0, str(val))
            except:
                self.display.delete(0, tk.END)
                self.display.insert(0, "Err")
            return
        self.display.insert(tk.END, key)

    def slide_in(self):
        self.deiconify()
        self.update()

    def _on_close(self):
        try:
            self.grab_release()
        except:
            pass
        self.destroy()

# =========================
# Special Casita Popup (DISEÑO PERSONALIZADO)
# =========================
class SpecialCasitaPopup(tk.Toplevel):
    def __init__(self, parent, prefill=None):
        super().__init__(parent)
        self.parent = parent
        self.prefill = prefill or (None, None)
        self.configure(bg=BG_PANEL)
        self.title("Casita — División Interactiva")
        self.resizable(False, False)

        # tamaño y posición inicial (fuera de pantalla para slide)
        self.w = 560
        self.h_collapsed = 380
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        x = (sw - self.w) // 2
        y = sh + 60
        self.geometry(f"{self.w}x{self.h_collapsed}+{x}+{y}")

        # variables
        self.var_dividendo = tk.StringVar()
        self.var_divisor = tk.StringVar()
        self.var_cociente = tk.StringVar()
        self.var_residuo = tk.StringVar(value="—")

        # --- Make popup scrollable in case content grows ---
        outer = tk.Frame(self, bg=BG_PANEL)
        outer.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(outer, bg=BG_PANEL, highlightthickness=0)
        self.scroll_y = ttk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        self.scroll_x = ttk.Scrollbar(outer, orient="horizontal", command=self.canvas.xview)
        self.inner = tk.Frame(self.canvas, bg=BG_PANEL)
        self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x.pack(side="bottom", fill="x")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        container = tk.Frame(self.inner, bg=BG_PANEL)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        left = tk.Frame(container, bg=BG_PANEL)
        left.pack(side="left", fill="both", expand=False, padx=(0,12))
        tk.Label(left, text="Diseño: Cociente arriba — Divisor / Dividendo", bg=BG_PANEL, fg=ACCENT_A,
                 font=("Segoe UI", 10, "bold")).pack(pady=(0,6))
        self.visual = tk.Canvas(left, width=300, height=220, bg=BG_CANVAS, highlightthickness=0)
        self.visual.pack(padx=6, pady=6)
        self._draw_new_layout_visual()

        right = tk.Frame(container, bg=BG_PANEL)
        right.pack(side="right", fill="both", expand=True)
        tk.Label(right, text="Cociente (arriba) — opcional:", bg=BG_PANEL, fg=TEXT).pack(anchor="w")
        self._entry_coc = tk.Entry(right, textvariable=self.var_cociente, width=24, justify="center",
                                   bg=BG_CANVAS, fg=TEXT, bd=0)
        self._entry_coc.pack(pady=6)

        separator = tk.Frame(right, height=2, bg="#3b4048")
        separator.pack(fill="x", pady=(4,8))

        row = tk.Frame(right, bg=BG_PANEL)
        row.pack(fill="x", pady=6)
        col1 = tk.Frame(row, bg=BG_PANEL)
        col1.pack(side="left", padx=(0,6), expand=True, fill="x")
        tk.Label(col1, text="Divisor:", bg=BG_PANEL, fg=TEXT).pack(anchor="w")
        self._entry_divisor = tk.Entry(col1, textvariable=self.var_divisor, width=14, justify="center",
                                       bg=BG_CANVAS, fg=TEXT, bd=0)
        self._entry_divisor.pack(pady=4, anchor="w")
        tk.Label(row, text="/", bg=BG_PANEL, fg=ACCENT_A, font=("Segoe UI", 16, "bold")).pack(side="left", padx=6)
        col2 = tk.Frame(row, bg=BG_PANEL)
        col2.pack(side="left", padx=(6,0), expand=True, fill="x")
        tk.Label(col2, text="Dividendo:", bg=BG_PANEL, fg=TEXT).pack(anchor="w")
        self._entry_div_top = tk.Entry(col2, textvariable=self.var_dividendo, width=14, justify="center",
                                       bg=BG_CANVAS, fg=TEXT, bd=0)
        self._entry_div_top.pack(pady=4, anchor="w")

        tk.Label(right, text="Residuo:", bg=BG_PANEL, fg=TEXT).pack(anchor="w", pady=(8,0))
        self._lbl_res = tk.Label(right, textvariable=self.var_residuo, bg=BG_PANEL, fg=ACCENT_B, font=("Segoe UI", 12, "bold"))
        self._lbl_res.pack(anchor="w", pady=(0,6))

        tk.Label(right, text="Llena Dividendo y Divisor. Cociente opcional. Pulsa Validar.", bg=BG_PANEL, fg="#bfc9d8",
                 font=("Segoe UI", 9)).pack(anchor="w", pady=(6,6))

        self.btns = tk.Frame(right, bg=BG_PANEL)
        self.btns.pack(pady=6, fill="x")
        tk.Button(self.btns, text="✅ Validar", bg=ACCENT_B, fg="#242830", bd=0, font=("Segoe UI", 11, "bold"),
                  command=self._validate_show).pack(side="left", padx=6)
        tk.Button(self.btns, text="🧹 Borrar", bg=ERROR, fg="white", bd=0, font=("Segoe UI", 11, "bold"),
                  command=self._clear_casita).pack(side="left", padx=6)
        tk.Button(self.btns, text="Cerrar", bg="#6b6f76", fg=TEXT, bd=0, font=("Segoe UI", 11),
                  command=self._on_close).pack(side="left", padx=6)

        self.result_frame = tk.Frame(right, bg=BG_PANEL)
        self.result_frame.pack(fill="x", pady=(8,0))

        # prefill if provided (A,B from manual)
        if self.prefill[0] is not None:
            self.var_dividendo.set(str(self.prefill[0]))
        if self.prefill[1] is not None:
            self.var_divisor.set(str(self.prefill[1]))

    def _draw_new_layout_visual(self):
        c = self.visual
        c.delete("all")
        c.create_text(150, 22, text="Cociente", fill=ACCENT_A, font=("Segoe UI", 10, "bold"))
        c.create_rectangle(40,36,260,66, outline="#777", width=1)
        c.create_line(20,90,280,90, fill="#555", width=2)
        c.create_rectangle(40,100,140,160, outline="#777", width=1)
        c.create_text(90,120, text="Divisor", fill="#e5c07b", font=("Segoe UI", 9))
        c.create_text(170,130, text="/", fill=ACCENT_A, font=("Segoe UI", 20, "bold"))
        c.create_rectangle(200,100,300,160, outline="#777", width=1)
        c.create_text(250,120, text="Dividendo", fill=ACCENT_A, font=("Segoe UI", 9))
        c.create_text(150,185, text="(Diseño sustituto — reemplaza la casita anterior)", fill="#9aa8b6", font=("Segoe UI", 8))

    def _validate_show(self):
        try:
            D_str = self._entry_div_top.get().strip()
            S_str = self._entry_divisor.get().strip()
            if D_str == "" or S_str == "":
                messagebox.showwarning("Entrada insuficiente", "Debes ingresar Dividendo y Divisor.")
                return
            D = int(D_str)
            S = int(S_str)
        except Exception:
            messagebox.showwarning("Entrada inválida", "Dividendo y Divisor deben ser enteros.")
            return
        if S == 0:
            messagebox.showwarning("Divisor 0", "El divisor no puede ser 0.")
            return
        q_user = self._entry_coc.get().strip()
        if q_user == "":
            q = D // S
        else:
            try:
                q = int(q_user)
            except:
                messagebox.showwarning("Entrada inválida", "Cociente debe ser entero si se ingresa.")
                return
        r = D - S * q
        if r < 0:
            messagebox.showwarning("Residuo inválido", f"Residuo negativo ({r}). Revisa los valores.")
            return

        # set residuo visible
        self.var_residuo.set(str(r))

        # update visual boxes with values
        self._draw_vals_on_visual(D, S, q, r)

        # limpiar resultados anteriores y crear botón importar (si no existe)
        for w in self.result_frame.winfo_children():
            w.destroy()

        tk.Label(self.result_frame, text=f"Cociente: {q}", bg=BG_PANEL, fg=ACCENT_A, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(self.result_frame, text=f"Residuo: {r}", bg=BG_PANEL, fg="#d19a66", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        def import_action(D=D, S=S, q=q, r=r):
            if r == 0:
                ctxt = None
                try:
                    ctxt = int(self.parent.e_c.get().strip())
                except:
                    ctxt = None
                if ctxt is not None:
                    threading.Thread(target=lambda: self._import_mcd_final(S, ctxt)).start()
                    return
            threading.Thread(target=lambda: self._import_to_automatic(D, S, q, r)).start()

        btn = tk.Button(self.result_frame, text="📥 Importar", bg=ACCENT_B, fg="#242830", bd=0,
                        font=("Segoe UI", 10, "bold"), cursor="hand2", command=import_action)
        btn.pack(pady=6)
        self.lift()

    def _draw_vals_on_visual(self, D, S, q, r):
        c = self.visual
        self._draw_new_layout_visual()
        c.create_text(150, 50, text=str(q), fill=ACCENT_A, font=("Segoe UI", 11, "bold"))
        c.create_text(90, 130, text=str(S), fill="#e5c07b", font=("Segoe UI", 11, "bold"))
        c.create_text(250, 130, text=str(D), fill=ACCENT_A, font=("Segoe UI", 11, "bold"))
        c.create_text(150, 165, text=f"Residuo: {r}", fill="#d19a66", font=("Segoe UI", 10, "bold"))

    def _import_to_automatic(self, D, S, q, r):
        try:
            app = self.parent.controller
            auto_frame = app.frames[EuclidesAutomaticFrame]
            auto_frame._draw_table(D, S)
            try:
                self.parent._add_step(D, S, q, r)
            except Exception:
                pass
        except Exception as e:
            print("Error importando a automático:", e)

    def _import_mcd_final(self, S, ctxt):
        try:
            app = self.parent.controller
            auto_frame = app.frames[EuclidesAutomaticFrame]
            auto_frame._draw_table(S, ctxt)
            try:
                self.parent._add_step(S, ctxt, ctxt // S if S != 0 else 0, ctxt % S if S != 0 else ctxt)
            except Exception:
                pass
        except Exception as e:
            print("Error importando MCD final:", e)

    def _clear_casita(self):
        self.var_dividendo.set("")
        self.var_divisor.set("")
        self.var_cociente.set("")
        self.var_residuo.set("—")
        for w in self.result_frame.winfo_children():
            w.destroy()
        self._draw_new_layout_visual()

    def slide_in(self):
        self.update()
        sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        target_x = (sw - self.w) // 2
        target_y = (sh - self.h_collapsed) // 2
        y = sh + 60
        step = 28
        self.geometry(f"{self.w}x{self.h_collapsed}+{target_x}+{y}")
        self.update()
        while y > target_y:
            y -= step
            if y < target_y: y = target_y
            self.geometry(f"{self.w}x{self.h_collapsed}+{target_x}+{y}")
            self.update()
            time.sleep(0.01)

    def _on_close(self):
        try:
            self.grab_release()
        except:
            pass
        self.destroy()

# =========================
# Ejecutar app
# =========================
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
