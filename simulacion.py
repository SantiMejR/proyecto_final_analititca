"""
Bloque de simulacion: genera datos falsos de ventas y empleados.
Inyecta errores intencionalmente para que el bloque de limpieza tenga trabajo.
"""
import random
from datetime import datetime, timedelta

import pandas as pd

random.seed(7)

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


def simular_empleados(n: int = 15) -> pd.DataFrame:
    filas = []
    for i in range(1, n + 1):
        nombre = random.choice(NOMBRES)
        cargo = random.choice(CARGOS)
        salario = random.randint(1300000, 4500000)
        fecha_ingreso = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1700))

        # Inyeccion de errores
        if i % 7 == 0:
            salario = "  no registrado  "  # tipo invalido
        if i % 5 == 0:
            cargo = cargo.upper() + "   "  # espacios y mayusculas
        if i % 11 == 0:
            nombre = None  # nulo
        fecha_str = fecha_ingreso.strftime("%Y-%m-%d")
        if i % 4 == 0:
            fecha_str = fecha_ingreso.strftime("%d/%m/%Y")  # formato distinto
        if i % 9 == 0:
            fecha_str = "fecha desconocida"  # invalido

        filas.append({
            "id_empleado": i,
            "nombre": nombre,
            "cargo": cargo,
            "salario": salario,
            "fecha_ingreso": fecha_str,
        })

    # Duplicado intencional
    filas.append(filas[0].copy())
    return pd.DataFrame(filas)


def simular_ventas(n: int = 60) -> pd.DataFrame:
    filas = []
    for i in range(1, n + 1):
        prenda = random.choice(PRENDAS)
        numero_prenda = random.randint(28, 46)
        cantidad = random.randint(1, 5)
        precio_unit = random.choice([45000, 60000, 89000, 120000, 175000])
        id_emp = random.randint(1, 15)
        fecha = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 450))

        # Inyeccion de errores
        if i % 8 == 0:
            numero_prenda = "  XL "  # texto en numero
        if i % 6 == 0:
            cantidad = -1  # cantidad invalida
        if i % 10 == 0:
            precio_unit = None  # nulo
        if i % 13 == 0:
            prenda = prenda.lower() + "  "  # espacios

        fecha_str = fecha.strftime("%Y-%m-%d")
        if i % 7 == 0:
            fecha_str = fecha.strftime("%d-%m-%Y")
        if i % 17 == 0:
            fecha_str = "2024/13/40"  # fecha invalida

        filas.append({
            "id_venta": i,
            "id_empleado": id_emp,
            "prenda": prenda,
            "numero_prenda": numero_prenda,
            "cantidad": cantidad,
            "precio_unitario": precio_unit,
            "fecha": fecha_str,
            "novedad": random.choice(NOVEDADES),
        })

    # Duplicado intencional
    filas.append(filas[0].copy())
    return pd.DataFrame(filas)
