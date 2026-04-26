"""
Bloque de limpieza: dos funciones obligatorias.

1) limpiar_ventas_empleados: valida tipos, formato de fecha, numero de prenda
   y caracteristicas de la venta.
2) analizar_novedades: revisa el campo novedad (texto libre) y lo clasifica.
"""
import re

import numpy as np
import pandas as pd

PRENDAS_VALIDAS = ["Camisa", "Pantalon", "Chaqueta", "Vestido", "Zapatos", "Sombrero", "Falda"]
NUMERO_PRENDA_VALIDO = list(range(28, 47))


def _parsear_fecha(valor):
    """Intenta varios formatos. Devuelve NaT si todos fallan."""
    if pd.isna(valor):
        return pd.NaT
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return pd.to_datetime(valor, format=fmt)
        except (ValueError, TypeError):
            continue
    return pd.NaT


def _parsear_numero(valor):
    """Convierte a entero si se puede, NaN si no."""
    if pd.isna(valor):
        return np.nan
    try:
        return int(str(valor).strip())
    except (ValueError, TypeError):
        return np.nan


def limpiar_ventas_empleados(df_ventas: pd.DataFrame, df_empleados: pd.DataFrame):
    """
    Funcion 1 del bloque de limpieza.

    Limpia ambos dataframes: normaliza textos, valida tipos numericos,
    valida formatos de fecha y descarta filas con campos clave invalidos.
    Retorna (ventas_limpias, empleados_limpios).
    """
    emp = df_empleados.copy()
    emp["nombre"] = emp["nombre"].astype(str).str.strip().replace({"None": np.nan, "nan": np.nan})
    emp["cargo"] = emp["cargo"].astype(str).str.strip().str.title()
    emp["salario"] = emp["salario"].apply(_parsear_numero)
    emp["fecha_ingreso"] = emp["fecha_ingreso"].apply(_parsear_fecha)
    emp = emp.drop_duplicates(subset=["id_empleado"])
    emp = emp.dropna(subset=["nombre", "salario", "fecha_ingreso"])

    ven = df_ventas.copy()
    ven["prenda"] = ven["prenda"].astype(str).str.strip().str.title()
    ven["numero_prenda"] = ven["numero_prenda"].apply(_parsear_numero)
    ven["cantidad"] = ven["cantidad"].apply(_parsear_numero)
    ven["precio_unitario"] = ven["precio_unitario"].apply(_parsear_numero)
    ven["fecha"] = ven["fecha"].apply(_parsear_fecha)

    # Validez con isin: prenda y numero_prenda dentro de catalogo permitido
    ven = ven[ven["prenda"].isin(PRENDAS_VALIDAS)]
    ven = ven[ven["numero_prenda"].isin(NUMERO_PRENDA_VALIDO)]
    ven = ven[ven["cantidad"] > 0]
    ven = ven.dropna(subset=["precio_unitario", "fecha"])
    ven = ven.drop_duplicates(subset=["id_venta"])

    ven["total"] = ven["cantidad"] * ven["precio_unitario"]

    return ven.reset_index(drop=True), emp.reset_index(drop=True)


def analizar_novedades(df_ventas: pd.DataFrame) -> pd.DataFrame:
    """
    Funcion 2 del bloque de limpieza.

    Analiza el texto del campo 'novedad' y agrega la columna 'tipo_novedad'.
    Tambien deja una marca booleana de si la novedad es relevante.
    """
    if "novedad" not in df_ventas.columns:
        return df_ventas

    out = df_ventas.copy()
    out["novedad"] = out["novedad"].fillna("").astype(str).str.strip()

    def clasificar(texto: str) -> str:
        if not texto:
            return "sin_novedad"
        t = texto.lower()
        if re.search(r"queja|demora|reclamo", t):
            return "queja"
        if re.search(r"defect", t):
            return "defecto"
        if re.search(r"descuento", t):
            return "descuento"
        if re.search(r"cambio|talla", t):
            return "cambio"
        if re.search(r"pago|metodo", t):
            return "pago"
        return "otra"

    out["tipo_novedad"] = out["novedad"].apply(clasificar)
    out["novedad_relevante"] = out["tipo_novedad"].isin(["queja", "defecto"])
    return out
