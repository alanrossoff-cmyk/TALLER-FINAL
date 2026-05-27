# 📊 Dolar-Track — Sistema de Análisis de TRM

> **Taller Final Corte 3 | Ecosistema Tecnológico End-to-End**
> Universidad de La Sabana · Programación y Decisiones 2026-1

---

## 📌 ¿De qué trata el proyecto?

**Dolar-Track** es una aplicación de escritorio que permite a un inversionista registrar,
analizar y visualizar el comportamiento histórico de la **Tasa Representativa del Mercado (TRM)**
del dólar (USD), euro (EUR) y otras divisas frente al peso colombiano (COP).

El sistema calcula automáticamente:
- 📈 **Promedio histórico** de la TRM
- 📉 **Volatilidad** (desviación estándar)
- 🚦 **Alertas de compra** (TRM < promedio) y **venta** (TRM > promedio)

---

## 🏗️ Arquitectura del Proyecto

```
DolarTrack/
├── main.py                   ← Orquestador principal (punto de entrada)
├── DolarTrack.pbix           ← Dashboard Power BI
├── README.md
│
├── Backend/
│   ├── __init__.py
│   ├── database.py           ← Capa de datos: SQLite, Esquema Estrella, CRUD
│   ├── logic.py              ← Lógica de negocio: cálculos, validaciones, POO
│   └── dolar_track.db        ← Base de datos SQLite (se genera automáticamente)
│
└── Frontend/
    ├── __init__.py
    ├── gui.py                ← Interfaz gráfica Tkinter
    └── logo.png              ← Logo del proyecto (opcional)
```

### Patrón de diseño
| Capa | Archivo | Responsabilidad |
|------|---------|----------------|
| Datos | `Backend/database.py` | Conexión SQLite, DDL, CRUD puro |
| Negocio | `Backend/logic.py` | Cálculos TRM, validaciones, DTOs |
| Presentación | `Frontend/gui.py` | UI Tkinter, eventos, messagebox |
| Orquestación | `main.py` | Arranque del sistema |

---

## 🗄️ Esquema Estrella (Base de Datos)

```
        ┌─────────────┐
        │  dim_divisa │  (USD, EUR, GBP, JPY, CHF…)
        │  id_divisa  │
        └──────┬──────┘
               │
┌──────────┐   │   ┌────────────┐
│ dim_fecha│───┤───│ hechos_trm │←── Tabla de Hechos
│ id_fecha │   │   │  id_hecho  │    (valor_trm, promedio,
└──────────┘   │   │  id_divisa │     volatilidad, diferencia)
               │   │  id_fecha  │
┌─────────────┐│   │  id_alerta │
│  dim_alerta ├┘   └────────────┘
│  id_alerta  │  (COMPRA, VENTA,
└─────────────┘   NEUTRAL…)
```

**Tablas:**
- `dim_divisa` — 5 divisas internacionales
- `dim_fecha` — Descomposición temporal (día, mes, año, trimestre, día semana)
- `dim_alerta` — 5 tipos de señal de mercado
- `hechos_trm` — Registros TRM con métricas calculadas

---

## ⚙️ Requerimientos del Sistema

- Python **3.9+**
- Librerías estándar únicamente: `tkinter`, `sqlite3`, `statistics`, `datetime`
- Power BI Desktop (para abrir el `.pbix`)

---

## 🚀 Instrucciones de Ejecución

### 1. Clonar el repositorio
```bash
git clone https://github.com/<TU_USUARIO>/DolarTrack.git
cd DolarTrack
```

### 2. (Opcional) Crear entorno virtual
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Ejecutar la aplicación
```bash
python main.py
```

> La base de datos `Backend/dolar_track.db` se crea **automáticamente** con datos semilla
> en el primer arranque. No es necesario ejecutar ningún script SQL.

### 4. Abrir Power BI
- Desde la interfaz: clic en el botón amarillo **"📊 Abrir Power BI"**
- O manualmente: abra `DolarTrack.pbix` con Power BI Desktop

---

## 🖥️ Funcionalidades de la Interfaz

| Botón | Función |
|-------|---------|
| ➕ Registrar | Ingresa fecha, divisa y valor TRM; calcula alerta automáticamente |
| 📋 Ver Tabla | Recarga todos los registros con formato y código de color |
| ✏️ Actualizar | Modifica el valor TRM del registro seleccionado |
| 🗑️ Eliminar | Elimina el registro seleccionado (con confirmación) |
| 📊 Abrir Power BI | Lanza el archivo `.pbix` con Power BI Desktop |

**Código de colores en la tabla:**
- 🟢 Verde → COMPRA (TRM bajo el promedio)
- 🟠 Naranja → VENTA (TRM sobre el promedio)
- 🔴 Rojo → ALERTA_ALTA / ALERTA_BAJA (desviación > 2%)
- ⚪ Gris → NEUTRAL

---

## 📊 Power BI — Dashboard

El archivo `DolarTrack.pbix` incluye:

| Gráfica | Tipo | Descripción |
|---------|------|-------------|
| Evolución TRM | Línea | Valor TRM por fecha vs promedio |
| Distribución Alertas | Dona | % de señales COMPRA / VENTA / NEUTRAL |
| Volatilidad Mensual | Barras | Desviación estándar agrupada por mes |
| TRM por Divisa | Barras horizontales | Comparativo entre divisas |

**Medidas DAX implementadas:**
```dax
-- Medida DAX 1: Promedio Ponderado TRM
Promedio_TRM = AVERAGE(hechos_trm[valor_trm])

-- Medida DAX 2: Volatilidad Global
Volatilidad_Global = STDEV.P(hechos_trm[valor_trm])

-- Columna Calculada DAX: Clasificación de Señal
Clasificacion_Señal =
IF(hechos_trm[diferencia_promedio] > 0, "Por encima del promedio", "Por debajo del promedio")
```

---

## 👥 Integrantes del Grupo

| # | Nombre | GitHub |
|---|--------|--------|
| 1 | [Nombre 1] | [@usuario1](https://github.com/usuario1) |
| 2 | [Nombre 2] | [@usuario2](https://github.com/usuario2) |
| 3 | [Nombre 3] | [@usuario3](https://github.com/usuario3) |

---

## 📋 Rúbrica Cubierta

| Criterio | Implementación |
|----------|---------------|
| ✅ Backend + SQLite | `database.py` con esquema estrella, 4 tablas, ≥5 registros/tabla |
| ✅ POO | Clases `Database`, `DolarTrackLogic`, `ResultadoTRM`, `ResumenAnalisis` |
| ✅ Frontend Tkinter | `gui.py` con 4 botones CRUD + botón Power BI + `messagebox` |
| ✅ try-except | Implementado en cada acción del usuario |
| ✅ Power BI | `.pbix` con modelo estrella, 4 gráficas, 2 medidas DAX |
| ✅ GitHub | Repositorio público, estructura modular, README detallado |

---

*Universidad de La Sabana · Semestre 2026-1 · Programación y Decisiones*
