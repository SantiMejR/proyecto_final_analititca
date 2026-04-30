"""
Bloque de simulacion: genera datos falsos de ventas y empleados con errores
intencionales para que el bloque de limpieza tenga trabajo.

Cuando se usa en modo "combinado" (junto con datos reales del back), las
funciones que terminan en _ruido producen filas con IDs altos (>= 1000)
para no chocar con los IDs reales que vienen de H2.
"""
import random
from datetime import datetime, timedelta

import pandas as pd

NOMBRES = [
    "Ana Lopez", "Carlos Perez", "Diana Ruiz", "Esteban Gomez", "Fabiola Mejia",
    "Gabriel Soto", "Helena Vargas", "Ivan Cardona", "Julia Restrepo", "Kevin Quintero",
]

CARGOS = ["Vendedor", "Cajero", "Supervisor", "Bodega", "Gerente"]

PRENDAS = ["Camisa", "Pantalon", "Chaqueta", "Vestido", "Zapatos", "Sombrero", "Falda"]

NOVEDADES = [
    "Cliente solicito cambio de talla",
    "Producto con defecto menor",
    "Pago dividido en dos metodos",
    "Descuento autorizado por supervisor",
    "Cliente registro queja por demora",
    "",  # vacio
    None,  # nulo
]


def simular_empleados(n: int = 15, start_id: int = 1) -> pd.DataFrame:
    """
    Simula empleados con errores intencionales.
    `start_id` permite desplazar los IDs para que no choquen con los del back.
    """
    rng = random.Random(7)
    filas = []
    for i in range(n):
        idx = start_id + i
        nombre = rng.choice(NOMBRES)
        cargo = rng.choice(CARGOS)
        salario = rng.randint(1300000, 4500000)
        fecha_ingreso = datetime(2020, 1, 1) + timedelta(days=rng.randint(0, 1700))

        # Inyeccion de errores
        if i % 7 == 0:
            salario = "  no registrado  "
        if i % 5 == 0:
            cargo = cargo.upper() + "   "
        if i % 11 == 0:
            nombre = None
        fecha_str = fecha_ingreso.strftime("%Y-%m-%d")
        if i % 4 == 0:
            fecha_str = fecha_ingreso.strftime("%d/%m/%Y")
        if i % 9 == 0:
            fecha_str = "fecha desconocida"

        filas.append({
            "id_empleado": idx,
            "nombre": nombre,
            "cargo": cargo,
            "salario": salario,
            "fecha_ingreso": fecha_str,
        })

    # Duplicado intencional
    if filas:
        filas.append(filas[0].copy())
    return pd.DataFrame(filas)


def simular_ventas(n: int = 60, ids_empleados: list[int] | None = None,
                   start_id: int = 1) -> pd.DataFrame:
    """
    Simula ventas con errores intencionales.
    Si se pasa `ids_empleados`, los usa como pool de id_empleado
    (asi las ventas simuladas tambien apuntan a empleados reales del back).
    """
    rng = random.Random(11)
    pool = ids_empleados if ids_empleados else list(range(1, 16))

    filas = []
    for i in range(n):
        idx = start_id + i
        prenda = rng.choice(PRENDAS)
        numero_prenda = rng.randint(28, 46)
        cantidad = rng.randint(1, 5)
        precio_unit = rng.choice([45000, 60000, 89000, 120000, 175000])
        id_emp = rng.choice(pool)
        fecha = datetime(2024, 1, 1) + timedelta(days=rng.randint(0, 450))

        # Inyeccion de errores
        if i % 8 == 0:
            numero_prenda = "  XL "
        if i % 6 == 0:
            cantidad = -1
        if i % 10 == 0:
            precio_unit = None
        if i % 13 == 0:
            prenda = prenda.lower() + "  "

        fecha_str = fecha.strftime("%Y-%m-%d")
        if i % 7 == 0:
            fecha_str = fecha.strftime("%d-%m-%Y")
        if i % 17 == 0:
            fecha_str = "2024/13/40"

        filas.append({
            "id_venta": idx,
            "id_empleado": id_emp,
            "prenda": prenda,
            "numero_prenda": numero_prenda,
            "cantidad": cantidad,
            "precio_unitario": precio_unit,
            "fecha": fecha_str,
            "novedad": rng.choice(NOVEDADES),
        })

    if filas:
        filas.append(filas[0].copy())
    return pd.DataFrame(filas)


def simular_empleados_ruido(n: int = 6) -> pd.DataFrame:
    """Empleados simulados con IDs altos (1000+) para acompanar los reales del back."""
    return simular_empleados(n=n, start_id=1000)


def simular_ventas_ruido(n: int = 30, ids_empleados: list[int] | None = None) -> pd.DataFrame:
    """Ventas simuladas con IDs altos para acompanar las reales del back."""
    return simular_ventas(n=n, ids_empleados=ids_empleados, start_id=1000)
