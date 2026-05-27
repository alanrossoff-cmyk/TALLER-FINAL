"""
gui.py — Interfaz Gráfica (Tkinter) de Dolar-Track
Cumple:
  • 4 botones CRUD (Registrar, Ver, Actualizar, Eliminar)
  • 1 botón para abrir Power BI
  • try-except + messagebox en cada operación
  • Diseño profesional con colores corporativos
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import sys
import os
import platform
from datetime import datetime

# Importar lógica desde el paquete Backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from Backend.logic import DolarTrackLogic


# ══════════════════════════════════════════════════════════════
# Paleta de colores
# ══════════════════════════════════════════════════════════════
COLORS = {
    "bg_primary":   "#0D1B2A",   # Azul marino profundo
    "bg_secondary": "#1B2A3B",   # Azul oscuro secundario
    "bg_card":      "#1E3A5F",   # Azul tarjeta
    "accent":       "#00D4AA",   # Verde-turquesa (éxito/registrar)
    "accent_blue":  "#2196F3",   # Azul brillante (ver)
    "accent_warn":  "#FF9800",   # Naranja (actualizar)
    "accent_red":   "#F44336",   # Rojo (eliminar)
    "accent_pbi":   "#F2C811",   # Amarillo Power BI
    "text_white":   "#FFFFFF",
    "text_gray":    "#B0BEC5",
    "header_bg":    "#162032",
    "row_even":     "#1B2A3B",
    "row_odd":      "#162032",
    "select_bg":    "#00D4AA22",
}

FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_SUB    = ("Segoe UI", 11)
FONT_BTN    = ("Segoe UI", 11, "bold")
FONT_LABEL  = ("Segoe UI", 10)
FONT_MONO   = ("Consolas", 10)

PBIX_PATH = os.path.join(os.path.dirname(__file__), "..", "DolarTrack.pbix")


# ══════════════════════════════════════════════════════════════
# Ventana Principal
# ══════════════════════════════════════════════════════════════
class DolarTrackApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("📊 Dolar-Track — Análisis de TRM")
        self.geometry("1150x750")
        self.minsize(900, 600)
        self.configure(bg=COLORS["bg_primary"])
        self.resizable(True, True)

        self.logic = DolarTrackLogic()
        self._construir_ui()
        self._cargar_tabla()

    # ── UI principal ──────────────────────────────────────────
    def _construir_ui(self):
        # ── Header ──
        header = tk.Frame(self, bg=COLORS["bg_secondary"], pady=14)
        header.pack(fill="x")

        tk.Label(header, text="📊  DOLAR-TRACK", font=FONT_TITLE,
                 bg=COLORS["bg_secondary"], fg=COLORS["accent"]).pack(side="left", padx=24)
        tk.Label(header, text="Sistema de Análisis de Tasa de Cambio (TRM)",
                 font=FONT_SUB, bg=COLORS["bg_secondary"],
                 fg=COLORS["text_gray"]).pack(side="left", padx=4)

        # Fecha en tiempo real
        self.lbl_fecha = tk.Label(header, font=FONT_LABEL,
                                  bg=COLORS["bg_secondary"], fg=COLORS["text_gray"])
        self.lbl_fecha.pack(side="right", padx=24)
        self._actualizar_reloj()

        # ── Barra de botones CRUD + Power BI ──
        btn_frame = tk.Frame(self, bg=COLORS["bg_primary"], pady=14, padx=20)
        btn_frame.pack(fill="x")

        self._crear_boton(btn_frame, "➕  Registrar",  COLORS["accent"],      self.registrar_trm)
        self._crear_boton(btn_frame, "📋  Ver Tabla",   COLORS["accent_blue"], self._cargar_tabla)
        self._crear_boton(btn_frame, "✏️  Actualizar",  COLORS["accent_warn"], self.actualizar_trm)
        self._crear_boton(btn_frame, "🗑️  Eliminar",    COLORS["accent_red"],  self.eliminar_trm)

        # Separador visual
        sep = tk.Frame(btn_frame, width=2, bg=COLORS["text_gray"])
        sep.pack(side="left", fill="y", padx=14, pady=4)

        self._crear_boton(btn_frame, "📊  Abrir Power BI",
                          COLORS["accent_pbi"], self.abrir_power_bi,
                          fg=COLORS["bg_primary"])

        # ── Área central: tabla + panel de alerta ──
        main_frame = tk.Frame(self, bg=COLORS["bg_primary"])
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Tabla
        tabla_frame = tk.Frame(main_frame, bg=COLORS["bg_primary"])
        tabla_frame.pack(fill="both", expand=True, side="left")

        self._construir_tabla(tabla_frame)

        # Panel lateral de análisis
        self._construir_panel_lateral(main_frame)

        # ── Barra de estado ──
        self.status_var = tk.StringVar(value="✅ Sistema listo.")
        status_bar = tk.Label(self, textvariable=self.status_var,
                              bg=COLORS["bg_secondary"], fg=COLORS["text_gray"],
                              font=FONT_LABEL, anchor="w", padx=12, pady=4)
        status_bar.pack(fill="x", side="bottom")

    def _crear_boton(self, parent, texto, color, comando, fg="#FFFFFF"):
        btn = tk.Button(
            parent, text=texto, command=comando,
            bg=color, fg=fg, font=FONT_BTN,
            relief="flat", padx=16, pady=8,
            cursor="hand2", activebackground=color,
            activeforeground=fg, bd=0
        )
        btn.pack(side="left", padx=6)

        # Efecto hover sutil
        def on_enter(e):  btn.configure(bg=self._lighten(color))
        def on_leave(e):  btn.configure(bg=color)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    @staticmethod
    def _lighten(hex_color: str) -> str:
        """Aclara un color hex en ~20%."""
        try:
            h = hex_color.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            r = min(255, r + 30); g = min(255, g + 30); b = min(255, b + 30)
            return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:
            return hex_color

    def _construir_tabla(self, parent):
        cols = ("ID", "Divisa", "Fecha", "TRM ($)", "Promedio ($)",
                "Volatilidad", "Diferencia", "Alerta")
        self.tree = ttk.Treeview(parent, columns=cols, show="headings",
                                 selectmode="browse")

        # Estilo
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview",
                        background=COLORS["row_even"],
                        foreground=COLORS["text_white"],
                        fieldbackground=COLORS["row_even"],
                        rowheight=28, font=FONT_MONO)
        style.configure("Treeview.Heading",
                        background=COLORS["header_bg"],
                        foreground=COLORS["accent"],
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", COLORS["bg_card"])])

        anchos = [50, 70, 90, 100, 100, 90, 90, 110]
        for col, w in zip(cols, anchos):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center", minwidth=50)

        # Scrollbars
        vsb = ttk.Scrollbar(parent, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # Tags de color según alerta
        self.tree.tag_configure("COMPRA",      foreground="#00D4AA")
        self.tree.tag_configure("VENTA",       foreground="#FF9800")
        self.tree.tag_configure("ALERTA_ALTA", foreground="#F44336", font=(*FONT_MONO[:2], "bold"))
        self.tree.tag_configure("ALERTA_BAJA", foreground="#F44336", font=(*FONT_MONO[:2], "bold"))
        self.tree.tag_configure("NEUTRAL",     foreground="#B0BEC5")

    def _construir_panel_lateral(self, parent):
        panel = tk.Frame(parent, bg=COLORS["bg_card"], width=260,
                         padx=14, pady=14)
        panel.pack(side="right", fill="y", padx=(12, 0))
        panel.pack_propagate(False)

        tk.Label(panel, text="📈 Análisis Rápido", font=("Segoe UI", 13, "bold"),
                 bg=COLORS["bg_card"], fg=COLORS["accent"]).pack(anchor="w", pady=(0, 12))

        # Selector de divisa
        tk.Label(panel, text="Divisa:", font=FONT_LABEL,
                 bg=COLORS["bg_card"], fg=COLORS["text_gray"]).pack(anchor="w")
        self.combo_divisa = ttk.Combobox(panel, state="readonly", width=14)
        self.combo_divisa.pack(anchor="w", pady=(2, 10))
        self._poblar_combo_divisas()
        self.combo_divisa.bind("<<ComboboxSelected>>", lambda e: self._actualizar_panel())

        # Labels de métricas
        self.metricas_vars = {}
        metricas = [
            ("n_registros", "Registros"),
            ("promedio",    "Promedio TRM"),
            ("volatilidad", "Volatilidad σ"),
            ("minimo",      "Mínimo"),
            ("maximo",      "Máximo"),
            ("rango",       "Rango"),
            ("tendencia",   "Tendencia"),
        ]
        for key, label in metricas:
            tk.Label(panel, text=label + ":", font=FONT_LABEL,
                     bg=COLORS["bg_card"], fg=COLORS["text_gray"]).pack(anchor="w", pady=(6, 0))
            var = tk.StringVar(value="—")
            self.metricas_vars[key] = var
            tk.Label(panel, textvariable=var, font=("Consolas", 11, "bold"),
                     bg=COLORS["bg_card"], fg=COLORS["text_white"]).pack(anchor="w")

        tk.Button(panel, text="🔄 Refrescar",
                  command=self._actualizar_panel,
                  bg=COLORS["bg_secondary"], fg=COLORS["accent"],
                  font=FONT_LABEL, relief="flat", cursor="hand2").pack(pady=14)

    # ── Poblar combo ──────────────────────────────────────────
    def _poblar_combo_divisas(self):
        try:
            divisas = self.logic.obtener_divisas()
            valores = [d["simbolo"] for d in divisas]
            self.combo_divisa["values"] = valores
            if valores:
                self.combo_divisa.set(valores[0])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron cargar las divisas:\n{e}")

    # ── Panel lateral: actualizar métricas ───────────────────
    def _actualizar_panel(self):
        try:
            simbolo = self.combo_divisa.get()
            if not simbolo:
                return
            resumen = self.logic.resumen_por_divisa(simbolo)
            if resumen is None:
                for v in self.metricas_vars.values():
                    v.set("Sin datos")
                return
            fmt = lambda x: f"${x:,.2f}"
            self.metricas_vars["n_registros"].set(str(resumen.n_registros))
            self.metricas_vars["promedio"].set(fmt(resumen.promedio))
            self.metricas_vars["volatilidad"].set(f"{resumen.volatilidad:,.4f}")
            self.metricas_vars["minimo"].set(fmt(resumen.minimo))
            self.metricas_vars["maximo"].set(fmt(resumen.maximo))
            self.metricas_vars["rango"].set(fmt(resumen.rango))
            self.metricas_vars["tendencia"].set(resumen.tendencia)
        except Exception as e:
            messagebox.showerror("Error en análisis", str(e))

    # ── Cargar / refrescar tabla ──────────────────────────────
    def _cargar_tabla(self):
        try:
            self.tree.delete(*self.tree.get_children())
            registros = self.logic.obtener_registros()
            for r in registros:
                alerta = r.get("alerta", "NEUTRAL") or "NEUTRAL"
                valores = (
                    r["id_hecho"],
                    r["divisa"],
                    r["fecha"],
                    f"${r['valor_trm']:,.2f}",
                    f"${r['promedio_historico']:,.2f}" if r["promedio_historico"] else "—",
                    f"{r['volatilidad']:,.4f}" if r["volatilidad"] else "—",
                    f"${r['diferencia_promedio']:,.2f}" if r["diferencia_promedio"] else "—",
                    alerta,
                )
                self.tree.insert("", "end", values=valores, tags=(alerta,))

            self.status_var.set(f"✅ {len(registros)} registros cargados.")
            self._actualizar_panel()
        except Exception as e:
            messagebox.showerror("Error al cargar datos", f"No se pudo cargar la tabla:\n{e}")

    # ══════════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════════

    # ── Registrar TRM ─────────────────────────────────────────
    def registrar_trm(self):
        try:
            ventana = VentanaRegistrar(self, self.logic.obtener_divisas())
            self.wait_window(ventana)
            if ventana.resultado:
                datos = ventana.resultado
                resultado = self.logic.registrar_trm(
                    datos["divisa"], datos["fecha"], datos["valor"]
                )
                messagebox.showinfo(
                    "✅ TRM Registrada",
                    f"{resultado.mensaje_alerta}\n\n"
                    f"Promedio histórico : ${resultado.promedio_historico:,.2f}\n"
                    f"Volatilidad σ      : {resultado.volatilidad:,.4f}"
                )
                self._cargar_tabla()
        except ValueError as e:
            messagebox.showerror("⚠️ Dato inválido", str(e))
        except Exception as e:
            messagebox.showerror("❌ Error", f"Ocurrió un error inesperado:\n{e}")

    # ── Ver (ya implementado en _cargar_tabla) ────────────────

    # ── Actualizar TRM ────────────────────────────────────────
    def actualizar_trm(self):
        try:
            seleccion = self.tree.selection()
            if not seleccion:
                messagebox.showwarning("⚠️ Selección vacía",
                                       "Por favor seleccione un registro de la tabla.")
                return
            valores = self.tree.item(seleccion[0])["values"]
            id_hecho = int(valores[0])
            trm_actual = valores[3]  # Ej: "$4,185.50"

            nuevo_str = simpledialog.askstring(
                "Actualizar TRM",
                f"Registro ID: {id_hecho}\nTRM actual: {trm_actual}\n\nIngrese el nuevo valor TRM:",
                parent=self
            )
            if nuevo_str is None:
                return
            nuevo_valor = float(nuevo_str.replace(",", ".").replace("$", ""))

            if self.logic.actualizar_trm(id_hecho, nuevo_valor):
                messagebox.showinfo("✅ Actualizado",
                                    f"Registro {id_hecho} actualizado a ${nuevo_valor:,.2f}")
                self._cargar_tabla()
            else:
                messagebox.showerror("Error", "No se encontró el registro.")
        except ValueError as e:
            messagebox.showerror("⚠️ Dato inválido", str(e))
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al actualizar:\n{e}")

    # ── Eliminar TRM ──────────────────────────────────────────
    def eliminar_trm(self):
        try:
            seleccion = self.tree.selection()
            if not seleccion:
                messagebox.showwarning("⚠️ Selección vacía",
                                       "Por favor seleccione un registro de la tabla.")
                return
            valores = self.tree.item(seleccion[0])["values"]
            id_hecho = int(valores[0])
            fecha    = valores[2]
            trm      = valores[3]

            confirmar = messagebox.askyesno(
                "Confirmar eliminación",
                f"¿Está seguro de eliminar el registro?\n\n"
                f"ID: {id_hecho} | Fecha: {fecha} | TRM: {trm}"
            )
            if not confirmar:
                return

            if self.logic.eliminar_trm(id_hecho):
                messagebox.showinfo("✅ Eliminado",
                                    f"Registro {id_hecho} eliminado correctamente.")
                self._cargar_tabla()
            else:
                messagebox.showerror("Error", "No se encontró el registro.")
        except Exception as e:
            messagebox.showerror("❌ Error", f"Error al eliminar:\n{e}")

    # ── Abrir Power BI ────────────────────────────────────────
    def abrir_power_bi(self):
        try:
            ruta = os.path.abspath(PBIX_PATH)
            if not os.path.exists(ruta):
                messagebox.showwarning(
                    "Archivo no encontrado",
                    f"No se encontró el archivo Power BI en:\n{ruta}\n\n"
                    "Asegúrese de que 'DolarTrack.pbix' esté en la raíz del proyecto."
                )
                return

            sistema = platform.system()
            if sistema == "Windows":
                os.startfile(ruta)
            elif sistema == "Darwin":   # macOS
                subprocess.Popen(["open", ruta])
            else:                       # Linux
                subprocess.Popen(["xdg-open", ruta])

            self.status_var.set("📊 Abriendo Power BI...")
        except PermissionError:
            messagebox.showerror("❌ Permiso denegado",
                                 "No se tienen permisos para abrir el archivo.")
        except Exception as e:
            messagebox.showerror("❌ Error al abrir Power BI",
                                 f"No se pudo abrir el archivo:\n{e}")

    # ── Reloj en tiempo real ──────────────────────────────────
    def _actualizar_reloj(self):
        ahora = datetime.now().strftime("%A, %d %b %Y — %H:%M:%S")
        self.lbl_fecha.configure(text=ahora)
        self.after(1000, self._actualizar_reloj)


# ══════════════════════════════════════════════════════════════
# Ventana emergente: Registrar TRM
# ══════════════════════════════════════════════════════════════
class VentanaRegistrar(tk.Toplevel):
    def __init__(self, parent, divisas: list):
        super().__init__(parent)
        self.title("➕ Registrar TRM")
        self.configure(bg=COLORS["bg_primary"])
        self.geometry("400x300")
        self.resizable(False, False)
        self.grab_set()   # Modal
        self.resultado = None
        self._construir(divisas)

    def _construir(self, divisas):
        tk.Label(self, text="Registrar Nueva TRM", font=("Segoe UI", 14, "bold"),
                 bg=COLORS["bg_primary"], fg=COLORS["accent"]).pack(pady=16)

        frame = tk.Frame(self, bg=COLORS["bg_primary"], padx=30)
        frame.pack(fill="x")

        # Divisa
        tk.Label(frame, text="Divisa:", font=FONT_LABEL,
                 bg=COLORS["bg_primary"], fg=COLORS["text_gray"]).grid(row=0, column=0, sticky="w", pady=6)
        simbolos = [d["simbolo"] for d in divisas]
        self.combo = ttk.Combobox(frame, values=simbolos, state="readonly", width=14)
        self.combo.set(simbolos[0] if simbolos else "")
        self.combo.grid(row=0, column=1, sticky="w", padx=8)

        # Fecha
        tk.Label(frame, text="Fecha (YYYY-MM-DD):", font=FONT_LABEL,
                 bg=COLORS["bg_primary"], fg=COLORS["text_gray"]).grid(row=1, column=0, sticky="w", pady=6)
        self.entry_fecha = tk.Entry(frame, width=16, bg=COLORS["bg_secondary"],
                                    fg=COLORS["text_white"], insertbackground="white")
        self.entry_fecha.insert(0, datetime.today().strftime("%Y-%m-%d"))
        self.entry_fecha.grid(row=1, column=1, sticky="w", padx=8)

        # Valor TRM
        tk.Label(frame, text="Valor TRM ($COP):", font=FONT_LABEL,
                 bg=COLORS["bg_primary"], fg=COLORS["text_gray"]).grid(row=2, column=0, sticky="w", pady=6)
        self.entry_valor = tk.Entry(frame, width=16, bg=COLORS["bg_secondary"],
                                    fg=COLORS["text_white"], insertbackground="white")
        self.entry_valor.grid(row=2, column=1, sticky="w", padx=8)

        # Botones
        btn_frame = tk.Frame(self, bg=COLORS["bg_primary"])
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="✅ Registrar", command=self._confirmar,
                  bg=COLORS["accent"], fg=COLORS["bg_primary"], font=FONT_BTN,
                  relief="flat", padx=14, pady=6, cursor="hand2").pack(side="left", padx=8)
        tk.Button(btn_frame, text="Cancelar", command=self.destroy,
                  bg=COLORS["bg_secondary"], fg=COLORS["text_gray"], font=FONT_BTN,
                  relief="flat", padx=14, pady=6, cursor="hand2").pack(side="left", padx=8)

    def _confirmar(self):
        try:
            divisa = self.combo.get()
            fecha  = self.entry_fecha.get().strip()
            valor_str = self.entry_valor.get().strip().replace(",", ".")
            if not valor_str:
                raise ValueError("El valor TRM no puede estar vacío.")
            valor = float(valor_str)
            self.resultado = {"divisa": divisa, "fecha": fecha, "valor": valor}
            self.destroy()
        except ValueError as e:
            messagebox.showerror("⚠️ Error de entrada",
                                 f"Verifique los datos ingresados:\n{e}", parent=self)


# ── Punto de entrada ──────────────────────────────────────────
def iniciar_app():
    app = DolarTrackApp()
    app.mainloop()
