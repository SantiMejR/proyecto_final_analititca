"""
API Flask que expone la rutina de analitica al frontend.

Por defecto trabaja con datos COMBINADOS:
  - empleados y ventas reales (del back en :8080)
  - + filas simuladas con errores (para que la limpieza haga su trabajo)

Si el back no esta disponible, cae a modo "simulado" automaticamente.
Tambien admite ?fuente=simulado para forzar solo datos simulados.
"""
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS

from simulacion import (
    simular_empleados, simular_ventas,
    simular_empleados_ruido, simular_ventas_ruido,
)
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


def _generar_dataset(fuente: str = "combinado"):
    """
    Pipeline completo: obtiene datos -> limpia -> analiza novedades.
    fuente:
      - "combinado": back + ruido simulado (default)
      - "simulado":  solo datos simulados (sin pegarle al back)

    Devuelve (ventas_raw, empleados_raw, ventas_limpias, empleados_limpios, info).
    """
    info = {"fuente_solicitada": fuente, "back_ok": False,
            "filas_back": {"empleados": 0, "ventas": 0},
            "filas_simuladas": {"empleados": 0, "ventas": 0}}

    empleados_back = pd.DataFrame()
    ventas_back = pd.DataFrame()

    if fuente == "combinado":
        try:
            empleados_back = obtener_empleados_back()
            ventas_back = obtener_ventas_back()
            info["back_ok"] = True
            info["filas_back"]["empleados"] = len(empleados_back)
            info["filas_back"]["ventas"] = len(ventas_back)
        except Exception as e:
            print(f"[analitica] no se pudo obtener data del back: {e}")
            info["back_error"] = str(e)

    # IDs de empleados reales para que las ventas simuladas tambien
    # apunten a vendedores que existen en el back
    ids_empleados_reales = (
        empleados_back["id_empleado"].tolist() if not empleados_back.empty else None
    )

    # Generar ruido simulado (siempre — para que la limpieza tenga errores que corregir)
    if fuente == "combinado" and not empleados_back.empty:
        empleados_sim = simular_empleados_ruido(n=6)
        ventas_sim = simular_ventas_ruido(n=30, ids_empleados=ids_empleados_reales)
    else:
        # Modo "simulado" puro o fallback si el back fallo
        empleados_sim = simular_empleados(n=15)
        ventas_sim = simular_ventas(n=60)

    info["filas_simuladas"]["empleados"] = len(empleados_sim)
    info["filas_simuladas"]["ventas"] = len(ventas_sim)

    # Concatenar reales + simulados
    empleados_raw = pd.concat([empleados_back, empleados_sim], ignore_index=True)
    ventas_raw = pd.concat([ventas_back, ventas_sim], ignore_index=True)

    # Pipeline de limpieza
    ventas, empleados = limpiar_ventas_empleados(ventas_raw, empleados_raw)
    ventas = analizar_novedades(ventas)

    return ventas_raw, empleados_raw, ventas, empleados, info


def _fuente_param() -> str:
    f = (request.args.get("fuente") or "combinado").lower()
    return f if f in ("combinado", "simulado") else "combinado"


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "back_disponible": back_disponible(),
    })


@app.get("/simular")
def simular():
    """Datos crudos (con errores) para mostrar el 'antes'."""
    ventas_raw, empleados_raw, _, _, info = _generar_dataset(_fuente_param())
    return jsonify({
        "ventas_html": ventas_raw.head(20).to_html(classes="tabla", index=False, border=0),
        "empleados_html": empleados_raw.head(20).to_html(classes="tabla", index=False, border=0),
        "ventas_total": int(len(ventas_raw)),
        "empleados_total": int(len(empleados_raw)),
        "info": info,
    })


@app.get("/limpiar")
def limpiar():
    """Datos ya limpios para mostrar el 'despues'."""
    _, _, ventas, empleados, info = _generar_dataset(_fuente_param())
    return jsonify({
        "ventas_html": ventas.head(20).to_html(classes="tabla", index=False, border=0),
        "empleados_html": empleados.head(20).to_html(classes="tabla", index=False, border=0),
        "ventas_total": int(len(ventas)),
        "empleados_total": int(len(empleados)),
        "info": info,
    })


@app.get("/analizar")
def analizar():
    """Descripcion estadistica + graficos."""
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
    cargos_disponibles = sorted(empleados["cargo"].dropna().unique().tolist())
    resultado = filtrar_empleados(empleados, ventas, cargo=cargo, ids=ids)
    resultado["cargos_disponibles"] = cargos_disponibles
    resultado["info"] = info
    return jsonify(resultado)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
