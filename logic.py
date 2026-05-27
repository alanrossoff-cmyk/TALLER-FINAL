"""
logic.py — Lógica de negocio de Dolar-Track
Separa las reglas de análisis financiero de la capa de datos.
"""

import statistics
from dataclasses import dataclass, field
from typing import List, Optional
from Backend.database import Database


# ──────────────────────────────────────────────────────────────
# Data-classes de transferencia (DTOs)
# ──────────────────────────────────────────────────────────────
@dataclass
class ResultadoTRM:
    divisa:              str
    fecha:               str
    valor_trm:           float
    promedio_historico:  float
    volatilidad:         float
    diferencia_promedio: float
    alerta:              str
    mensaje_alerta:      str  = ""

    def __post_init__(self):
        self.mensaje_alerta = self._generar_mensaje()

    def _generar_mensaje(self) -> str:
        mensajes = {
            "COMPRA":      f"📉 SEÑAL DE COMPRA: La TRM (${self.valor_trm:,.2f}) está por "
                           f"debajo del promedio (${self.promedio_historico:,.2f}). "
                           f"Buen momento para comprar {self.divisa}.",
            "VENTA":       f"📈 SEÑAL DE VENTA: La TRM (${self.valor_trm:,.2f}) supera el "
                           f"promedio (${self.promedio_historico:,.2f}). "
                           f"Considere vender {self.divisa}.",
            "ALERTA_ALTA": f"🚨 ALERTA ALTA: La TRM (${self.valor_trm:,.2f}) supera en más "
                           f"del 2% el promedio. Venta muy favorable.",
            "ALERTA_BAJA": f"🚨 ALERTA BAJA: La TRM (${self.valor_trm:,.2f}) cae más del 2% "
                           f"bajo el promedio. Compra muy favorable.",
            "NEUTRAL":     f"⚖️  NEUTRAL: La TRM (${self.valor_trm:,.2f}) está en rango "
                           f"normal respecto al promedio (${self.promedio_historico:,.2f}).",
        }
        return mensajes.get(self.alerta, "Sin información de alerta.")


@dataclass
class ResumenAnalisis:
    divisa:     str
    n_registros: int
    promedio:   float
    volatilidad: float
    minimo:     float
    maximo:     float
    rango:      float
    tendencia:  str         # 'ALCISTA', 'BAJISTA', 'LATERAL'
    registros:  List[dict] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────
# Clase de lógica de negocio
# ──────────────────────────────────────────────────────────────
class DolarTrackLogic:
    """Orquesta las reglas de análisis financiero para Dolar-Track."""

    def __init__(self):
        self.db = Database()

    # ── Registrar TRM (con validación) ───────────────────────
    def registrar_trm(self, simbolo: str, fecha: str, valor: float) -> ResultadoTRM:
        """Valida y persiste un nuevo registro TRM."""
        self._validar_valor(valor)
        self._validar_fecha(fecha)
        self._validar_divisa(simbolo)

        datos = self.db.registrar_trm(simbolo, fecha, valor)

        return ResultadoTRM(
            divisa              = datos["divisa"],
            fecha               = datos["fecha"],
            valor_trm           = datos["valor_trm"],
            promedio_historico  = datos["promedio_historico"],
            volatilidad         = datos["volatilidad"],
            diferencia_promedio = datos["diferencia_promedio"],
            alerta              = datos["alerta"],
        )

    # ── Ver todos los registros ───────────────────────────────
    def obtener_registros(self) -> List[dict]:
        return self.db.obtener_todos()

    # ── Actualizar TRM ────────────────────────────────────────
    def actualizar_trm(self, id_hecho: int, nuevo_valor: float) -> bool:
        self._validar_valor(nuevo_valor)
        return self.db.actualizar_trm(id_hecho, nuevo_valor)

    # ── Eliminar TRM ──────────────────────────────────────────
    def eliminar_trm(self, id_hecho: int) -> bool:
        return self.db.eliminar_trm(id_hecho)

    # ── Análisis / Resumen ────────────────────────────────────
    def resumen_por_divisa(self, simbolo: str = "USD") -> Optional[ResumenAnalisis]:
        """Calcula estadísticas completas para una divisa."""
        registros = [r for r in self.db.obtener_todos() if r["divisa"] == simbolo]
        if not registros:
            return None

        valores = [r["valor_trm"] for r in registros]
        promedio   = round(statistics.mean(valores), 2)
        vol        = round(statistics.stdev(valores) if len(valores) > 1 else 0.0, 4)
        minimo     = round(min(valores), 2)
        maximo     = round(max(valores), 2)
        rango      = round(maximo - minimo, 2)

        # Tendencia: compara primera vs última mitad
        mitad = len(valores) // 2
        if mitad > 0:
            primera = statistics.mean(valores[:mitad])
            segunda = statistics.mean(valores[mitad:])
            if segunda > primera * 1.005:
                tendencia = "ALCISTA 📈"
            elif segunda < primera * 0.995:
                tendencia = "BAJISTA 📉"
            else:
                tendencia = "LATERAL ⚖️"
        else:
            tendencia = "INSUFICIENTE"

        return ResumenAnalisis(
            divisa      = simbolo,
            n_registros = len(registros),
            promedio    = promedio,
            volatilidad = vol,
            minimo      = minimo,
            maximo      = maximo,
            rango       = rango,
            tendencia   = tendencia,
            registros   = registros,
        )

    def obtener_divisas(self) -> List[dict]:
        return self.db.obtener_divisas()

    # ── Validaciones internas ─────────────────────────────────
    @staticmethod
    def _validar_valor(valor: float) -> None:
        if not isinstance(valor, (int, float)):
            raise TypeError("El valor TRM debe ser numérico.")
        if valor <= 0:
            raise ValueError("El valor TRM debe ser mayor que cero.")
        if valor > 100_000:
            raise ValueError("Valor TRM inusualmente alto. Verifique el dato.")

    @staticmethod
    def _validar_fecha(fecha: str) -> None:
        from datetime import datetime
        try:
            datetime.strptime(fecha, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Formato de fecha inválido: '{fecha}'. Use YYYY-MM-DD.")

    def _validar_divisa(self, simbolo: str) -> None:
        divisas = [d["simbolo"] for d in self.db.obtener_divisas()]
        if simbolo not in divisas:
            raise ValueError(f"Divisa '{simbolo}' no existe. Opciones: {divisas}")
