# Proyecto Final — Analítica

Servicio HTTP que expone la **rutina de analítica** del proyecto: simula
datos de ventas y empleados, los limpia, los analiza con pandas y entrega
gráficos listos para mostrar en el frontend.

Es uno de **tres repositorios** que conforman el proyecto:

| Repositorio | Tecnología | Puerto | Rol |
|---|---|---|---|
| `proyecto_final_front` | HTML + JS + Bootstrap | (estático) | UI |
| `proyecto_final_back` | Spring Boot + Java 21 | `8080` | CRUD de usuarios y ventas |
| `proyecto_final_analititca` | Flask + pandas | `5000` | **Este repo** — análisis |

---

## Tecnologías

- **Python 3.10+**
- **Flask 3.0** — servidor HTTP minimalista
- **Flask-CORS** — habilita CORS para que el front pueda consumirlo
- **pandas 2.2** — DataFrames, `describe()`, `groupby()`, `isin()`
- **NumPy** — soporte numérico para pandas
- **Matplotlib** — gráficos exportados a `base64` (PNG)

---

## Estructura del proyecto

```
proyecto_final_analititca/
├── app.py             # API Flask (endpoints + CORS)
├── simulacion.py      # Generación de datos (con errores intencionales)
├── limpieza.py        # 2 funciones de limpieza
├── analitica.py       # Pandas + filtros + gráficos
├── requirements.txt
└── README.md
```

### Bloques de la rutina

#### 1. Simulación — `simulacion.py`
Genera dos `DataFrame` falsos, **con errores inyectados a propósito** para
que el bloque de limpieza tenga trabajo:

- **Empleados** (`simular_empleados`) — id, nombre, cargo, salario, fecha de ingreso.
  Errores: salario como texto, cargo con espacios y mayúsculas, nombres nulos,
  formatos de fecha inconsistentes, una fecha inválida, una fila duplicada.
- **Ventas** (`simular_ventas`) — id, empleado, prenda, número de prenda,
  cantidad, precio, fecha, novedad. Errores: número de prenda como texto,
  cantidades negativas, precios nulos, fechas en distintos formatos, una
  fecha imposible (`2024/13/40`), una fila duplicada.

#### 2. Limpieza — `limpieza.py`

Dos funciones obligatorias:

- **`limpiar_ventas_empleados(df_ventas, df_empleados)`**
  - Normaliza textos (`strip`, `title`).
  - Valida tipos numéricos (salario, cantidad, número de prenda).
  - Valida formato de fecha probando varios patrones.
  - Usa **`isin`** contra catálogos válidos:
    - `PRENDAS_VALIDAS = ["Camisa", "Pantalon", "Chaqueta", "Vestido", "Zapatos", "Sombrero", "Falda"]`
    - `NUMERO_PRENDA_VALIDO = range(28, 47)`
  - Descarta duplicados y filas con campos clave inválidos.
  - Calcula `total = cantidad * precio_unitario`.

- **`analizar_novedades(df_ventas)`**
  - Lee el campo de texto `novedad` y lo clasifica con expresiones regulares
    en categorías: `queja`, `defecto`, `descuento`, `cambio`, `pago`, `otra`,
    `sin_novedad`.
  - Marca `novedad_relevante = True` cuando es queja o defecto.

#### 3. Analítica — `analitica.py`

- **`describir(df)`** — `df.describe()` listo para serializar.
- **`filtrar_empleados(df_emp, df_ven, cargo, ids)`** — componente de filtros
  que acepta un cargo o una lista de ids y devuelve también la **agrupación
  de ventas** del subconjunto filtrado.
- **`agrupar_ventas_por_prenda(df)`** — `groupby` por prenda con sumas y conteos.
- Gráficos en **base64** listos para insertar en `<img>`:
  - `grafico_ventas_por_prenda` — barras
  - `grafico_ventas_por_empleado` — top 10 horizontal
  - `grafico_novedades` — pie chart

---

## Cómo funciona

```
GET /endpoint
     │
     ▼
   simular()              # Datos crudos (con errores)
     │
     ▼
   limpiar_ventas_empleados()
   analizar_novedades()
     │
     ▼
   describe / groupby / isin / matplotlib
     │
     ▼
   JSON con HTML de tablas + PNG en base64
```

Cada endpoint regenera los datos; no hay base de datos. El frontend recibe
el HTML de las tablas (`df.to_html()`) y los gráficos en `base64`, y los
inyecta directamente en el DOM.

---

## Cómo usarlo

### Prerrequisitos

- **Python 3.10+** (probado con 3.10–3.13)
- **pip**

### Instalación

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
```

### Ejecutar

```bash
python app.py
```

El servicio queda en [http://localhost:5000](http://localhost:5000).

### Probar manualmente

```bash
curl http://localhost:5000/health
curl http://localhost:5000/simular
curl http://localhost:5000/limpiar
curl http://localhost:5000/analizar
curl "http://localhost:5000/filtrar?cargo=Vendedor"
curl "http://localhost:5000/filtrar?ids=1,2,3"
```

---

## Endpoints

| Método | Ruta | Descripción | Respuesta |
|---|---|---|---|
| `GET` | `/health` | Verifica que el servicio responde | `{"status": "ok"}` |
| `GET` | `/simular` | Datos crudos (con errores) | HTML de las tablas + totales |
| `GET` | `/limpiar` | Datos ya limpios | HTML de las tablas + totales |
| `GET` | `/analizar` | `describe()` + 3 gráficos | HTML + 3 PNG en base64 |
| `GET` | `/filtrar?cargo=...&ids=1,2` | Filtra empleados y agrupa sus ventas | HTML de empleados, ventas y agrupado + cargos disponibles |

### Ejemplo de respuesta de `/analizar`

```json
{
  "descripcion_ventas":    { "filas": 47, "columnas": [...], "describe_html": "<table>...</table>" },
  "descripcion_empleados": { "filas": 12, "columnas": [...], "describe_html": "<table>...</table>" },
  "grafico_prenda":        "iVBORw0KGgoAAAANSUhEUgAA...",
  "grafico_empleados":     "iVBORw0KGgoAAAANSUhEUgAA...",
  "grafico_novedades":     "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

El front pinta los gráficos como `<img src="data:image/png;base64,..." />`.

---

## Conexión con los demás repos

- El **frontend** consume estos endpoints desde `services/analytics.js` y los
  muestra en la vista `views/analitica.html`.
- **No** consume el backend Spring Boot — los datos son simulados.

---

## Flujo de ramas

- Trabajo en **`develop`**.
- Merge a **`main`** cuando develop esté estable.
