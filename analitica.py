"""
Bloque de analitica: descripciones, filtros y agrupaciones con pandas.
Tambien genera graficos en base64 listos para insertar en <img> del front.
"""
import base64
import io

import matplotlib

matplotlib.use("Agg")  # backend sin GUI, necesario en servidor
import matplotlib.pyplot as plt
import pandas as pd


def describir(df: pd.DataFrame) -> dict:
    """Resumen tipo df.describe() pero serializable a JSON."""
    desc = df.describe(include="all").fillna("").reset_index()
    return {
        "filas": int(len(df)),
        "columnas": list(df.columns),
        "describe_html": desc.to_html(classes="tabla", index=False, border=0),
    }


def filtrar_empleados(df_emp: pd.DataFrame, df_ven: pd.DataFrame,
                      cargo: str | None = None,
                      ids: list[int] | None = None) -> dict:
    """
    Componente de filtros + agrupaciones.

    - Filtra empleados por cargo o por lista de ids (usando isin).
    - Agrupa las ventas de los empleados filtrados.
    """
    emp = df_emp.copy()
    if cargo:
        emp = emp[emp["cargo"].str.lower() == cargo.lower()]
    if ids:
        emp = emp[emp["id_empleado"].isin(ids)]

    ids_filtrados = emp["id_empleado"].tolist()
    ventas_filtradas = df_ven[df_ven["id_empleado"].isin(ids_filtrados)]

    # Agrupacion: ventas por empleado
    agrupado = (
        ventas_filtradas
        .groupby("id_empleado")
        .agg(num_ventas=("id_venta", "count"),
             total_vendido=("total", "sum"),
             prendas_distintas=("prenda", "nunique"))
        .reset_index()
        .merge(emp[["id_empleado", "nombre", "cargo"]], on="id_empleado", how="left")
    )

    return {
        "empleados_html": emp.to_html(classes="tabla", index=False, border=0),
        "ventas_html": ventas_filtradas.head(50).to_html(classes="tabla", index=False, border=0),
        "agrupado_html": agrupado.to_html(classes="tabla", index=False, border=0),
        "empleados_count": int(len(emp)),
        "ventas_count": int(len(ventas_filtradas)),
    }


def agrupar_ventas_por_prenda(df_ven: pd.DataFrame) -> pd.DataFrame:
    return (
        df_ven.groupby("prenda")
              .agg(num_ventas=("id_venta", "count"),
                   total_vendido=("total", "sum"),
                   cantidad_total=("cantidad", "sum"))
              .reset_index()
              .sort_values("total_vendido", ascending=False)
    )


def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def grafico_ventas_por_prenda(df_ven: pd.DataFrame) -> str:
    g = agrupar_ventas_por_prenda(df_ven)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(g["prenda"], g["total_vendido"], color="#4f46e5")
    ax.set_title("Total vendido por prenda")
    ax.set_xlabel("Prenda")
    ax.set_ylabel("Total ($)")
    ax.tick_params(axis="x", rotation=30)
    return _fig_to_base64(fig)


def grafico_ventas_por_empleado(df_ven: pd.DataFrame, df_emp: pd.DataFrame) -> str:
    agrup = (df_ven.groupby("id_empleado")["total"].sum()
                   .reset_index()
                   .merge(df_emp[["id_empleado", "nombre"]], on="id_empleado", how="left")
                   .sort_values("total", ascending=False)
                   .head(10))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(agrup["nombre"].fillna("(sin nombre)"), agrup["total"], color="#10b981")
    ax.set_title("Top empleados por monto vendido")
    ax.invert_yaxis()
    return _fig_to_base64(fig)


def grafico_novedades(df_ven: pd.DataFrame) -> str:
    if "tipo_novedad" not in df_ven.columns:
        return ""
    conteo = df_ven["tipo_novedad"].value_counts()
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(conteo.values, labels=conteo.index, autopct="%1.0f%%", startangle=90)
    ax.set_title("Distribucion de novedades")
    return _fig_to_base64(fig)
