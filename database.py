"""
database.py — Capa de datos del proyecto Dolar-Track
Esquema Estrella:
  • dim_divisa   → Dimensión de divisas (USD, EUR, etc.)
  • dim_fecha    → Dimensión de tiempo (descomposición de la fecha)
  • dim_alerta   → Dimensión de tipos de alerta
  • hechos_trm   → Tabla de hechos con los registros TRM diarios
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

# Ruta absoluta de la base de datos (junto a este archivo)
DB_PATH = os.path.join(os.path.dirname(__file__), "dolar_track.db")


# ──────────────────────────────────────────────────────────────
# Clase principal de acceso a datos
# ──────────────────────────────────────────────────────────────
class Database:
    """Gestiona la conexión y las operaciones CRUD sobre SQLite."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._inicializar()

    # ── Conexión ──────────────────────────────────────────────
    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")   # Activar FK
        conn.row_factory = sqlite3.Row             # Acceso por nombre de columna
        return conn

    # ── Creación del esquema estrella ─────────────────────────
    def _crear_tablas(self, conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()

        # DIMENSIÓN 1: Divisa
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_divisa (
                id_divisa   INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre      TEXT    NOT NULL UNIQUE,
                simbolo     TEXT    NOT NULL,
                descripcion TEXT
            )
        """)

        # DIMENSIÓN 2: Fecha
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_fecha (
                id_fecha    INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha       TEXT    NOT NULL UNIQUE,  -- 'YYYY-MM-DD'
                dia         INTEGER NOT NULL,
                mes         INTEGER NOT NULL,
                anio        INTEGER NOT NULL,
                trimestre   INTEGER NOT NULL,
                dia_semana  TEXT    NOT NULL
            )
        """)

        # DIMENSIÓN 3: Tipo de Alerta
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dim_alerta (
                id_alerta   INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo        TEXT    NOT NULL UNIQUE,  -- 'COMPRA', 'VENTA', 'NEUTRAL'
                descripcion TEXT
            )
        """)

        # TABLA DE HECHOS: TRM diaria
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hechos_trm (
                id_hecho            INTEGER PRIMARY KEY AUTOINCREMENT,
                id_divisa           INTEGER NOT NULL REFERENCES dim_divisa(id_divisa),
                id_fecha            INTEGER NOT NULL REFERENCES dim_fecha(id_fecha),
                id_alerta           INTEGER          REFERENCES dim_alerta(id_alerta),
                valor_trm           REAL    NOT NULL,
                promedio_historico  REAL,
                volatilidad         REAL,
                diferencia_promedio REAL,
                fecha_registro      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """)

        conn.commit()

    # ── Datos semilla (≥ 5 registros por tabla) ───────────────
    def _insertar_datos_semilla(self, conn: sqlite3.Connection) -> None:
        cursor = conn.cursor()

        # — dim_divisa (5 registros) —
        divisas = [
            ("Dólar Estadounidense", "USD", "Moneda de reserva global"),
            ("Euro",                 "EUR", "Moneda de la Unión Europea"),
            ("Libra Esterlina",      "GBP", "Moneda del Reino Unido"),
            ("Yen Japonés",          "JPY", "Moneda del Japón"),
            ("Franco Suizo",         "CHF", "Moneda de Suiza"),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO dim_divisa (nombre, simbolo, descripcion) VALUES (?,?,?)",
            divisas
        )

        # — dim_alerta (3 registros base + 2 extra = 5) —
        alertas = [
            ("COMPRA",  "TRM por debajo del promedio: momento favorable para comprar"),
            ("VENTA",   "TRM por encima del promedio: momento favorable para vender"),
            ("NEUTRAL", "TRM en rango normal respecto al promedio"),
            ("ALERTA_ALTA",  "TRM supera en más de 2% el promedio histórico"),
            ("ALERTA_BAJA",  "TRM cae más de 2% por debajo del promedio histórico"),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO dim_alerta (tipo, descripcion) VALUES (?,?)",
            alertas
        )

        # — dim_fecha: 5 días recientes —
        dias_semana_es = {
            "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
            "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado",
            "Sunday": "Domingo"
        }
        hoy = datetime.today()
        for i in range(5, 0, -1):
            d = hoy - timedelta(days=i)
            fecha_str = d.strftime("%Y-%m-%d")
            trimestre = (d.month - 1) // 3 + 1
            dia_sem_en = d.strftime("%A")
            cursor.execute(
                """INSERT OR IGNORE INTO dim_fecha
                   (fecha, dia, mes, anio, trimestre, dia_semana)
                   VALUES (?,?,?,?,?,?)""",
                (fecha_str, d.day, d.month, d.year, trimestre, dias_semana_es[dia_sem_en])
            )

        conn.commit()

        # — hechos_trm: 5 registros USD históricos —
        cursor.execute("SELECT id_divisa FROM dim_divisa WHERE simbolo='USD'")
        row_div = cursor.fetchone()
        if row_div is None:
            return
        id_usd = row_div[0]

        cursor.execute("SELECT id_alerta FROM dim_alerta WHERE tipo='NEUTRAL'")
        id_neutral = cursor.fetchone()[0]

        cursor.execute("SELECT id_fecha, fecha FROM dim_fecha ORDER BY fecha")
        fechas = cursor.fetchall()

        trm_base = [4_185.50, 4_210.30, 4_198.75, 4_220.60, 4_175.90]
        for idx, (id_fecha, _) in enumerate(fechas):
            valor = trm_base[idx]
            promedio = sum(trm_base[:idx+1]) / (idx + 1)
            # Determinar alerta
            if valor > promedio * 1.002:
                cursor.execute("SELECT id_alerta FROM dim_alerta WHERE tipo='VENTA'")
            elif valor < promedio * 0.998:
                cursor.execute("SELECT id_alerta FROM dim_alerta WHERE tipo='COMPRA'")
            else:
                cursor.execute("SELECT id_alerta FROM dim_alerta WHERE tipo='NEUTRAL'")
            id_alerta = cursor.fetchone()[0]

            import statistics
            vol = statistics.stdev(trm_base[:idx+1]) if idx > 0 else 0.0

            cursor.execute("""
                INSERT OR IGNORE INTO hechos_trm
                    (id_divisa, id_fecha, id_alerta, valor_trm,
                     promedio_historico, volatilidad, diferencia_promedio)
                VALUES (?,?,?,?,?,?,?)
            """, (id_usd, id_fecha, id_alerta, valor, round(promedio, 2),
                  round(vol, 4), round(valor - promedio, 2)))

        conn.commit()

    # ── Inicialización completa ───────────────────────────────
    def _inicializar(self) -> None:
        with self._conectar() as conn:
            self._crear_tablas(conn)
            self._insertar_datos_semilla(conn)

    # ══════════════════════════════════════════════════════════
    # CRUD — hechos_trm
    # ══════════════════════════════════════════════════════════

    def registrar_trm(self, simbolo_divisa: str, fecha: str,
                      valor_trm: float) -> dict:
        """Inserta un nuevo registro de TRM y calcula métricas automáticamente."""
        with self._conectar() as conn:
            cursor = conn.cursor()

            # 1. Obtener / crear dimensión divisa
            cursor.execute("SELECT id_divisa FROM dim_divisa WHERE simbolo=?",
                           (simbolo_divisa,))
            row = cursor.fetchone()
            if row is None:
                raise ValueError(f"Divisa '{simbolo_divisa}' no registrada.")
            id_divisa = row[0]

            # 2. Obtener / crear dimensión fecha
            d = datetime.strptime(fecha, "%Y-%m-%d")
            trimestre = (d.month - 1) // 3 + 1
            dias_semana_es = {
                "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
                "Thursday": "Jueves", "Friday": "Viernes",
                "Saturday": "Sábado", "Sunday": "Domingo"
            }
            dia_sem = dias_semana_es[d.strftime("%A")]
            cursor.execute(
                "INSERT OR IGNORE INTO dim_fecha (fecha,dia,mes,anio,trimestre,dia_semana) "
                "VALUES (?,?,?,?,?,?)",
                (fecha, d.day, d.month, d.year, trimestre, dia_sem)
            )
            cursor.execute("SELECT id_fecha FROM dim_fecha WHERE fecha=?", (fecha,))
            id_fecha = cursor.fetchone()[0]

            # 3. Calcular promedio y volatilidad históricos (misma divisa)
            cursor.execute(
                "SELECT valor_trm FROM hechos_trm WHERE id_divisa=? ORDER BY id_fecha",
                (id_divisa,)
            )
            historico = [r[0] for r in cursor.fetchall()] + [valor_trm]
            import statistics
            promedio  = round(statistics.mean(historico), 2)
            vol       = round(statistics.stdev(historico) if len(historico) > 1 else 0.0, 4)
            diff      = round(valor_trm - promedio, 2)

            # 4. Determinar alerta
            if valor_trm > promedio * 1.02:
                tipo_alerta = "ALERTA_ALTA"
            elif valor_trm > promedio:
                tipo_alerta = "VENTA"
            elif valor_trm < promedio * 0.98:
                tipo_alerta = "ALERTA_BAJA"
            elif valor_trm < promedio:
                tipo_alerta = "COMPRA"
            else:
                tipo_alerta = "NEUTRAL"

            cursor.execute("SELECT id_alerta FROM dim_alerta WHERE tipo=?", (tipo_alerta,))
            id_alerta = cursor.fetchone()[0]

            # 5. Insertar hecho
            cursor.execute("""
                INSERT INTO hechos_trm
                    (id_divisa, id_fecha, id_alerta, valor_trm,
                     promedio_historico, volatilidad, diferencia_promedio)
                VALUES (?,?,?,?,?,?,?)
            """, (id_divisa, id_fecha, id_alerta, valor_trm, promedio, vol, diff))
            conn.commit()

            return {
                "id_hecho": cursor.lastrowid,
                "divisa": simbolo_divisa,
                "fecha": fecha,
                "valor_trm": valor_trm,
                "promedio_historico": promedio,
                "volatilidad": vol,
                "diferencia_promedio": diff,
                "alerta": tipo_alerta,
            }

    def obtener_todos(self) -> list:
        """Devuelve todos los registros de hechos_trm con JOINs."""
        sql = """
            SELECT
                h.id_hecho,
                d.simbolo        AS divisa,
                f.fecha,
                h.valor_trm,
                h.promedio_historico,
                h.volatilidad,
                h.diferencia_promedio,
                a.tipo           AS alerta,
                h.fecha_registro
            FROM  hechos_trm  h
            JOIN  dim_divisa  d ON d.id_divisa = h.id_divisa
            JOIN  dim_fecha   f ON f.id_fecha  = h.id_fecha
            LEFT JOIN dim_alerta  a ON a.id_alerta = h.id_alerta
            ORDER BY f.fecha DESC, h.id_hecho DESC
        """
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]

    def actualizar_trm(self, id_hecho: int, nuevo_valor: float) -> bool:
        """Actualiza el valor_trm de un registro y recalcula métricas."""
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id_divisa FROM hechos_trm WHERE id_hecho=?",
                           (id_hecho,))
            row = cursor.fetchone()
            if row is None:
                return False
            id_divisa = row[0]

            # Recalcular promedio sin el registro actual, luego agregar nuevo valor
            cursor.execute(
                "SELECT valor_trm FROM hechos_trm WHERE id_divisa=? AND id_hecho!=?",
                (id_divisa, id_hecho)
            )
            historico = [r[0] for r in cursor.fetchall()] + [nuevo_valor]
            import statistics
            promedio = round(statistics.mean(historico), 2)
            vol      = round(statistics.stdev(historico) if len(historico) > 1 else 0.0, 4)
            diff     = round(nuevo_valor - promedio, 2)

            if nuevo_valor > promedio * 1.02:
                tipo = "ALERTA_ALTA"
            elif nuevo_valor > promedio:
                tipo = "VENTA"
            elif nuevo_valor < promedio * 0.98:
                tipo = "ALERTA_BAJA"
            elif nuevo_valor < promedio:
                tipo = "COMPRA"
            else:
                tipo = "NEUTRAL"

            cursor.execute("SELECT id_alerta FROM dim_alerta WHERE tipo=?", (tipo,))
            id_alerta = cursor.fetchone()[0]

            cursor.execute("""
                UPDATE hechos_trm
                SET valor_trm=?, promedio_historico=?, volatilidad=?,
                    diferencia_promedio=?, id_alerta=?
                WHERE id_hecho=?
            """, (nuevo_valor, promedio, vol, diff, id_alerta, id_hecho))
            conn.commit()
            return cursor.rowcount > 0

    def eliminar_trm(self, id_hecho: int) -> bool:
        """Elimina un registro de la tabla de hechos."""
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hechos_trm WHERE id_hecho=?", (id_hecho,))
            conn.commit()
            return cursor.rowcount > 0

    def obtener_divisas(self) -> list:
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT simbolo, nombre FROM dim_divisa ORDER BY simbolo")
            return [dict(row) for row in cursor.fetchall()]
