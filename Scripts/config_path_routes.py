import os
import sys


class ConfigPathRoutes:
    """
    Clase responsable de configurar las rutas del proyecto para asegurar que los módulos y paquetes sean correctamente detectados y importados, evitando problemas de detección y conflictos en los imports.
    """

    def __init__(self):
        """
        Inicializa una instancia de ConfigPathRoutes, determinando y almacenando las rutas relevantes para el proyecto: el directorio actual y el directorio padre.
        """
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        self.parent_dir = os.path.dirname(self.current_dir)

    def _modificar_path(self):
        """
        Modifica el sistema de búsqueda de módulos (`sys.path`) añadiendo las rutas del directorio actual y su directorio padre.

        Esta operación es útil para garantizar que se puedan importar módulos de forma coherente desde cualquier
        parte del proyecto.
        """
        sys.path.append(self.current_dir)
        sys.path.append(self.parent_dir)

        
# Extender path.
cnf_path_routes = ConfigPathRoutes()
cnf_path_routes._modificar_path()
    