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

# Estilo por defecto de los graficos
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "figure.facecolor": "white",
})


def describir(df: pd.DataFrame) -> dict:
    """Resumen tipo df.describe() pero serializable a JSON."""
    if df is None or df.empty:
        return {"filas": 0, "columnas": [], "describe_html": "<p>Sin datos.</p>"}
    desc = df.describe(include="all").fillna("").reset_index()
    return {
        "filas": int(len(df)),
        "columnas": list(df.columns),
        "describe_html": desc.to_html(classes="tabla", index=False, border=0),
    }


def filtrar_empleados(df_emp: pd.DataFrame, df_ven: pd.DataFrame,
                      cargo: str | None = None,
                      ids: list[int] | None = None) -> dict:
    """Filtra empleados por cargo o ids (isin) y agrupa sus ventas."""
    emp = df_emp.copy()
    if cargo:
        emp = emp[emp["cargo"].str.lower() == cargo.lower()]
    if ids:
        emp = emp[emp["id_empleado"].isin(ids)]

    ids_filtrados = emp["id_empleado"].tolist()
    ventas_filtradas = df_ven[df_ven["id_empleado"].isin(ids_filtrados)]

    if not ventas_filtradas.empty:
        agrupado = (
            ventas_filtradas
            .groupby("id_empleado")
            .agg(num_ventas=("id_venta", "count"),
                 total_vendido=("total", "sum"),
                 prendas_distintas=("prenda", "nunique"))
            .reset_index()
            .merge(emp[["id_empleado", "nombre", "cargo"]], on="id_empleado", how="left")
        )
        agrupado_html = agrupado.to_html(classes="tabla", index=False, border=0)
    else:
        agrupado_html = "<p>Sin ventas para los empleados filtrados.</p>"

    return {
        "empleados_html": emp.to_html(classes="tabla", index=False, border=0)
                          if not emp.empty else "<p>Sin empleados.</p>",
        "ventas_html": ventas_filtradas.head(50).to_html(classes="tabla", index=False, border=0)
                       if not ventas_filtradas.empty else "<p>Sin ventas.</p>",
        "agrupado_html": agrupado_html,
        "empleados_count": int(len(emp)),
        "ventas_count": int(len(ventas_filtradas)),
    }


def agrupar_ventas_por_prenda(df_ven: pd.DataFrame) -> pd.DataFrame:
    if df_ven is None or df_ven.empty:
        return pd.DataFrame(columns=["prenda", "num_ventas", "total_vendido", "cantidad_total"])
    return (
        df_ven.groupby("prenda")
              .agg(num_ventas=("id_venta", "count"),
                   total_vendido=("total", "sum"),
                   cantidad_total=("cantidad", "sum"))
              .reset_index()
              .sort_values("total_vendido", ascending=False)
    )


# -------- helpers de graficos --------

def _fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=110, facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def _grafico_vacio(mensaje: str = "Sin datos") -> str:
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.text(0.5, 0.5, mensaje, ha="center", va="center",
            fontsize=14, color="#6c757d", transform=ax.transAxes)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return _fig_to_base64(fig)


def _formato_cop(n: float) -> str:
    return f"${n:,.0f}".replace(",", ".")


# -------- graficos --------

def grafico_ventas_por_prenda(df_ven: pd.DataFrame) -> str:
    g = agrupar_ventas_por_prenda(df_ven)
    if g.empty:
        return _grafico_vacio("Sin ventas para graficar")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(g["prenda"], g["total_vendido"], color="#6C63FF", edgecolor="white")
    ax.set_title("Total vendido por prenda", pad=12)
    ax.set_xlabel("Prenda")
    ax.set_ylabel("Total (COP)")
    ax.tick_params(axis="x", rotation=20)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: _formato_cop(x)))

    # Valor encima de cada barra
    ymax = g["total_vendido"].max() or 1
    for bar, valor in zip(bars, g["total_vendido"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + ymax * 0.02,
                _formato_cop(valor), ha="center", va="bottom", fontsize=8)
    ax.set_ylim(0, ymax * 1.15)

    return _fig_to_base64(fig)


def grafico_ventas_por_empleado(df_ven: pd.DataFrame, df_emp: pd.DataFrame) -> str:
    if df_ven is None or df_ven.empty:
        return _grafico_vacio("Sin ventas para graficar")

    agrup = (df_ven.groupby("id_empleado")["total"].sum()
                   .reset_index()
                   .merge(df_emp[["id_empleado", "nombre"]], on="id_empleado", how="left")
                   .sort_values("total", ascending=False)
                   .head(10))
    if agrup.empty or agrup["total"].sum() == 0:
        return _grafico_vacio("Sin ventas para graficar")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    nombres = agrup["nombre"].fillna("(sin nombre)")
    bars = ax.barh(nombres, agrup["total"], color="#10b981", edgecolor="white")
    ax.set_title("Top 10 empleados por monto vendido", pad=12)
    ax.set_xlabel("Total (COP)")
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: _formato_cop(x)))

    xmax = agrup["total"].max() or 1
    for bar, valor in zip(bars, agrup["total"]):
        ax.text(bar.get_width() + xmax * 0.01, bar.get_y() + bar.get_height() / 2,
                _formato_cop(valor), ha="left", va="center", fontsize=8)
    ax.set_xlim(0, xmax * 1.18)

    return _fig_to_base64(fig)


def grafico_novedades(df_ven: pd.DataFrame) -> str:
    if df_ven is None or df_ven.empty or "tipo_novedad" not in df_ven.columns:
        return _grafico_vacio("Sin novedades para graficar")

    conteo = df_ven["tipo_novedad"].value_counts()
    if conteo.empty:
        return _grafico_vacio("Sin novedades para graficar")

    colores = ["#6C63FF", "#FF6584", "#10b981", "#f59e0b", "#0ea5e9", "#a855f7", "#94a3b8"]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    wedges, texts, autotexts = ax.pie(
        conteo.values, labels=conteo.index, autopct="%1.0f%%",
        startangle=90, colors=colores[:len(conteo)],
        wedgeprops=dict(edgecolor="white", linewidth=2),
        textprops=dict(fontsize=9),
    )
    for at in autotexts:
        at.set_color("white")
        at.set_fontweight("bold")
    ax.set_title("Distribucion de tipos de novedad", pad=12)
    return _fig_to_base64(fig)
