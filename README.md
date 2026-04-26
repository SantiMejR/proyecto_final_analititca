# proyecto_final_analititca

Servicio Flask que expone la rutina de analitica para el proyecto final.

## Estructura

- `simulacion.py` — genera ventas y empleados con errores intencionales.
- `limpieza.py` — dos funciones: `limpiar_ventas_empleados` y `analizar_novedades`.
- `analitica.py` — pandas (describe, filtros con `isin`, agrupaciones con `groupby`) y graficos en base64.
- `app.py` — API Flask con CORS habilitado.

## Endpoints

| Metodo | Ruta        | Descripcion                                     |
|--------|-------------|-------------------------------------------------|
| GET    | /health     | Verifica que el servicio responde               |
| GET    | /simular    | Devuelve datos crudos (con errores) en HTML     |
| GET    | /limpiar    | Devuelve datos ya limpios en HTML               |
| GET    | /analizar   | Descripcion estadistica + graficos en base64    |
| GET    | /filtrar    | Filtra empleados por `cargo` o `ids` y agrupa   |

## Como correr

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

El servicio queda en `http://localhost:5000`.
