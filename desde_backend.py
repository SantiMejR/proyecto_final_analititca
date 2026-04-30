"""
Adaptador del backend Spring Boot.

Consume los endpoints del back (puerto 8080) y convierte la respuesta JSON
en DataFrames de pandas con el mismo esquema que usa la rutina de analitica.
Asi los datos reales (precargados + nuevos registros) entran al pipeline
junto con los datos simulados.
"""
import random
from datetime import datetime, timedelta

import pandas as pd
import requests

BACK_URL = "http://localhost:8080/api"
TIMEOUT = 4

# Mapeo de categorias del back -> nombres de prenda que usa la analitica
CATEGORIA_A_PRENDA = {
    "Camisetas": "Camisa",
    "Pantalones": "Pantalon",
    "Vestidos": "Vestido",
    "Chaquetas": "Chaqueta",
    "Faldas": "Falda",
    "Calzado": "Zapatos",
    "Sombreros": "Sombrero",
}

# Mapeo de talla del back (S/M/L/XL o numerica) -> numero_prenda valido (28-46)
TALLA_A_NUMERO = {
    "XS": 28, "S": 30, "M": 34, "L": 38, "XL": 42, "XXL": 44,
}


def _talla_a_numero(talla: str) -> int:
    """Convierte una talla del back en un numero dentro del rango valido."""
    if not talla:
        return 34
    talla = str(talla).strip().upper()
    if talla in TALLA_A_NUMERO:
        return TALLA_A_NUMERO[talla]
    try:
        n = int(talla)
        # Si la talla numerica esta dentro del rango valido la usamos directo
        if 28 <= n <= 46:
            return n
    except ValueError:
        pass
    return 34  # default razonable


def disponible() -> bool:
    """Verifica si el back responde."""
    try:
        r = requests.get(f"{BACK_URL}/usuarios", timeout=TIMEOUT)
        return r.ok
    except requests.RequestException:
        return False


def obtener_empleados_back() -> pd.DataFrame:
    """
    Trae los usuarios con rol VENDEDOR del back y los adapta al schema de empleados.
    El back no tiene salario ni fecha de ingreso, asi que se rellenan con valores
    deterministas (mismo seed) para que sean reproducibles.
    """
    rng = random.Random(42)
    resp = requests.get(f"{BACK_URL}/usuarios/rol/VENDEDOR", timeout=TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    filas = []
    for u in data:
        filas.append({
            "id_empleado": int(u["id"]),
            "nombre": f"{u.get('nombre', '').strip()} {u.get('apellido', '').strip()}".strip(),
            "cargo": "Vendedor",
            "salario": rng.randint(1300000, 4500000),
            "fecha_ingreso": (
                datetime(2020, 1, 1) + timedelta(days=rng.randint(0, 1700))
            ).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(filas)


def obtener_ventas_back() -> pd.DataFrame:
    """
    Trae las ventas del back y las "aplana" en filas por cada DetalleVenta,
    con el schema que espera la analitica.
    """
    # Indice de productos para obtener categoria y talla a partir del id
    productos_resp = requests.get(f"{BACK_URL}/productos", timeout=TIMEOUT)
    productos_resp.raise_for_status()
    productos_idx = {int(p["id"]): p for p in productos_resp.json()}

    ventas_resp = requests.get(f"{BACK_URL}/ventas", timeout=TIMEOUT)
    ventas_resp.raise_for_status()
    ventas_data = ventas_resp.json()

    filas = []
    for v in ventas_data:
        fecha_iso = v.get("fecha") or ""
        fecha_str = fecha_iso[:10] if fecha_iso else ""  # YYYY-MM-DD
        vendedor_id = int(v.get("vendedorId") or 0)

        for d in v.get("detalles", []) or []:
            producto = productos_idx.get(int(d.get("productoId", 0)), {})
            categoria = producto.get("categoria", "")
            talla = producto.get("talla", "")
            filas.append({
                # ID compuesto para evitar choque con IDs simulados
                "id_venta": int(v["id"]) * 1000 + int(d.get("id", 0)),
                "id_empleado": vendedor_id,
                "prenda": CATEGORIA_A_PRENDA.get(categoria, "Camisa"),
                "numero_prenda": _talla_a_numero(talla),
                "cantidad": int(d.get("cantidad", 0)),
                "precio_unitario": int(d.get("precioUnitario", 0)),
                "fecha": fecha_str,
                "novedad": "",  # el back no tiene novedades
            })

    return pd.DataFrame(filas, columns=[
        "id_venta", "id_empleado", "prenda", "numero_prenda",
        "cantidad", "precio_unitario", "fecha", "novedad",
    ])
