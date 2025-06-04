"""Modulo que configura las rutas de las carpetas principales del proyecto. (Scripts / Utils) Cumple la función de que todo sea visible y accesible desde main.py"""

import sys
import os

# Obtener el directorio del script actual
current_dir = os.path.dirname(os.path.abspath(__file__))

list_dir = ["Scripts", "Utils", "Config"]

# Obtener el directorio del script actual
current_dir = os.path.dirname(os.path.abspath(__file__))

# Obtener el directorio padre
parent_dir = os.path.dirname(current_dir)

for cada_path in list_dir:
    # Obtener los path  de los directorios adicionales
    parent_dir = os.path.dirname(current_dir)
    path_agregar = os.path.join(parent_dir, cada_path)

    # Añadir al sys.path si no están ya
    if path_agregar not in sys.path:
        sys.path.append(path_agregar)


def Obtener_lugar_de_ejecucion() -> str:
    """
    Captura la respuesta del usuario sobre el lugar de ejecución y ajusta la ruta actual si es necesario.

    Returns:
        str: La respuesta del usuario, validada para ser 'si' o 'no'.
    """
    while True:
        lugar_de_ejecucion = (
            input(
                "¿Está ejecutando esta automatización desde Python IDLE ó desde cmd?: (si/no): "
            )
            .strip()
            .lower()
        )
        if lugar_de_ejecucion in ["si", "no"]:
            break
        else:
            print("Respuesta no válida. Por favor, ingrese 'si' o 'no'.")

    if lugar_de_ejecucion == "si":
        ruta_actual = os.getcwd()
        ruta_padre = os.path.dirname(ruta_actual)
        os.chdir(ruta_padre)

    return lugar_de_ejecucion
