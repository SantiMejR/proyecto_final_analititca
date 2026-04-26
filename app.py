"""
API Flask que expone la rutina de analitica al frontend.
CORS habilitado para que el HTML pueda consumirla via fetch.
"""
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

app = Flask(__name__)
CORS(app)


def _generar_dataset():
    """Pipeline completo: simula -> limpia -> analiza novedades."""
    ventas_raw = simular_ventas()
    empleados_raw = simular_empleados()
    ventas, empleados = limpiar_ventas_empleados(ventas_raw, empleados_raw)
    ventas = analizar_novedades(ventas)
    return ventas_raw, empleados_raw, ventas, empleados


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/simular")
def simular():
    """Devuelve los datos crudos (con errores) para mostrar el antes."""
    ventas_raw = simular_ventas()
    empleados_raw = simular_empleados()
    return jsonify({
        "ventas_html": ventas_raw.head(20).to_html(classes="tabla", index=False, border=0),
        "empleados_html": empleados_raw.head(20).to_html(classes="tabla", index=False, border=0),
        "ventas_total": int(len(ventas_raw)),
        "empleados_total": int(len(empleados_raw)),
    })


@app.get("/limpiar")
def limpiar():
    """Devuelve los datos limpios para mostrar el despues."""
    _, _, ventas, empleados = _generar_dataset()
    return jsonify({
        "ventas_html": ventas.head(20).to_html(classes="tabla", index=False, border=0),
        "empleados_html": empleados.head(20).to_html(classes="tabla", index=False, border=0),
        "ventas_total": int(len(ventas)),
        "empleados_total": int(len(empleados)),
    })


@app.get("/analizar")
def analizar():
    """Descripcion estadistica + graficos."""
    _, _, ventas, empleados = _generar_dataset()
    return jsonify({
        "descripcion_ventas": describir(ventas),
        "descripcion_empleados": describir(empleados),
        "grafico_prenda": grafico_ventas_por_prenda(ventas),
        "grafico_empleados": grafico_ventas_por_empleado(ventas, empleados),
        "grafico_novedades": grafico_novedades(ventas),
    })


@app.get("/filtrar")
def filtrar():
    """
    Componente de filtros + agrupaciones.
    Acepta ?cargo=Vendedor o ?ids=1,2,3
    """
    cargo = request.args.get("cargo") or None
    ids_param = request.args.get("ids")
    ids = None
    if ids_param:
        try:
            ids = [int(x) for x in ids_param.split(",") if x.strip()]
        except ValueError:
            return jsonify({"error": "ids debe ser una lista de enteros separados por coma"}), 400

    _, _, ventas, empleados = _generar_dataset()
    cargos_disponibles = sorted(empleados["cargo"].dropna().unique().tolist())
    resultado = filtrar_empleados(empleados, ventas, cargo=cargo, ids=ids)
    resultado["cargos_disponibles"] = cargos_disponibles
    return jsonify(resultado)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
