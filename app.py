"""
API Flask que expone la rutina de analitica al frontend.

Trabaja exclusivamente con los datos REALES del backend Spring Boot:
empleados (vendedores) y ventas tal como estan persistidos en H2.
Esto garantiza que las tablas y los graficos reflejen exactamente
lo mismo que se ve en el front y en el back.

Si el back no esta disponible y se quiere ver el comportamiento de la
rutina con datos artificiales, se puede pasar ?fuente=simulado para
forzar el modo de simulacion (incluye errores intencionales).
"""
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

from simulacion import simular_empleados, simular_ventas
from limpieza import limpiar_ventas_empleados, analizar_novedades
from analitica import (
    describir,
    filtrar_empleados,
    grafico_ventas_por_prenda,
    grafico_ventas_por_empleado,
    grafico_novedades,
)
from desde_backend import (
    obtener_empleados_back, obtener_ventas_back, disponible as back_disponible,
)

app = Flask(__name__)
CORS(app)


def _generar_dataset(fuente: str = "back"):
    """
    Pipeline completo: obtiene datos -> limpia -> analiza novedades.
    fuente:
      - "back" (default): solo datos reales del backend Spring Boot.
                          Si el back no responde se devuelve un dataset vacio.
      - "simulado":       solo datos simulados con errores intencionales
                          (modo de respaldo / demo offline).

    Devuelve (ventas_raw, empleados_raw, ventas_limpias, empleados_limpios, info).
    """
    info = {
        "fuente_solicitada": fuente,
        "back_ok": False,
        "filas_back": {"empleados": 0, "ventas": 0},
        "filas_simuladas": {"empleados": 0, "ventas": 0},
    }

    if fuente == "simulado":
        empleados_raw = simular_empleados(n=15)
        ventas_raw = simular_ventas(n=60)
        info["filas_simuladas"]["empleados"] = len(empleados_raw)
        info["filas_simuladas"]["ventas"] = len(ventas_raw)
    else:
        # Modo "back" — usar exclusivamente datos del backend
        try:
            empleados_raw = obtener_empleados_back()
            ventas_raw = obtener_ventas_back()
            info["back_ok"] = True
            info["filas_back"]["empleados"] = len(empleados_raw)
            info["filas_back"]["ventas"] = len(ventas_raw)
        except Exception as e:
            print(f"[analitica] no se pudo obtener data del back: {e}")
            info["back_error"] = str(e)
            empleados_raw = pd.DataFrame(columns=[
                "id_empleado", "nombre", "cargo", "salario", "fecha_ingreso",
            ])
            ventas_raw = pd.DataFrame(columns=[
                "id_venta", "id_empleado", "prenda", "numero_prenda",
                "cantidad", "precio_unitario", "fecha", "novedad",
            ])

    # Pipeline de limpieza (los datos del back ya son validos, asi que
    # esto deberia pasar sin descartar nada; en modo simulado si limpia errores).
    ventas, empleados = limpiar_ventas_empleados(ventas_raw, empleados_raw)
    ventas = analizar_novedades(ventas)

    return ventas_raw, empleados_raw, ventas, empleados, info


def _fuente_param() -> str:
    f = (request.args.get("fuente") or "back").lower()
    return f if f in ("back", "simulado") else "back"


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "back_disponible": back_disponible(),
    })


@app.get("/simular")
def simular():
    """Datos tal como vienen del back (modo 'simular' del flujo del front)."""
    ventas_raw, empleados_raw, _, _, info = _generar_dataset(_fuente_param())
    return jsonify({
        "ventas_html": ventas_raw.head(50).to_html(classes="tabla", index=False, border=0)
                       if not ventas_raw.empty else "<p>Sin ventas registradas en el backend.</p>",
        "empleados_html": empleados_raw.head(50).to_html(classes="tabla", index=False, border=0)
                          if not empleados_raw.empty else "<p>Sin vendedores registrados en el backend.</p>",
        "ventas_total": int(len(ventas_raw)),
        "empleados_total": int(len(empleados_raw)),
        "info": info,
    })


@app.get("/limpiar")
def limpiar():
    """Datos despues del pipeline de limpieza."""
    _, _, ventas, empleados, info = _generar_dataset(_fuente_param())
    return jsonify({
        "ventas_html": ventas.head(50).to_html(classes="tabla", index=False, border=0)
                       if not ventas.empty else "<p>Sin ventas para mostrar.</p>",
        "empleados_html": empleados.head(50).to_html(classes="tabla", index=False, border=0)
                          if not empleados.empty else "<p>Sin empleados para mostrar.</p>",
        "ventas_total": int(len(ventas)),
        "empleados_total": int(len(empleados)),
        "info": info,
    })


@app.get("/analizar")
def analizar():
    """Descripcion estadistica + graficos sobre los datos del back."""
    _, _, ventas, empleados, info = _generar_dataset(_fuente_param())
    return jsonify({
        "descripcion_ventas": describir(ventas),
        "descripcion_empleados": describir(empleados),
        "grafico_prenda": grafico_ventas_por_prenda(ventas),
        "grafico_empleados": grafico_ventas_por_empleado(ventas, empleados),
        "grafico_novedades": grafico_novedades(ventas),
        "info": info,
    })


@app.get("/filtrar")
def filtrar():
    """Filtros + agrupaciones de empleados (acepta ?cargo=... o ?ids=1,2,3)."""
    cargo = request.args.get("cargo") or None
    ids_param = request.args.get("ids")
    ids = None
    if ids_param:
        try:
            ids = [int(x) for x in ids_param.split(",") if x.strip()]
        except ValueError:
            return jsonify({"error": "ids debe ser una lista de enteros separados por coma"}), 400

    _, _, ventas, empleados, info = _generar_dataset(_fuente_param())
    cargos_disponibles = sorted(empleados["cargo"].dropna().unique().tolist()) \
        if not empleados.empty else []
    resultado = filtrar_empleados(empleados, ventas, cargo=cargo, ids=ids)
    resultado["cargos_disponibles"] = cargos_disponibles
    resultado["info"] = info
    return jsonify(resultado)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
