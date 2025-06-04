import os
import yaml
from loguru import logger  # O usa print si no estás usando loguru


def Procesar_configuracion(nombre_archivo_config: str) -> dict:
    """
    Carga y procesa un archivo de configuración YAML.

    Args:
        nombre_archivo_config (str): Nombre del archivo YAML (ej. "config.yaml").

    Returns:
        dict: Diccionario con la configuración cargada.

    Raises:
        FileNotFoundError: Si no se encuentra el archivo de configuración.
        yaml.YAMLError: Si hay un error al parsear el archivo YAML.
    """
    try:
        # Ruta absoluta del archivo actual (config_loader.py)
        ruta_actual = os.path.dirname(os.path.abspath(__file__))
        ruta_completa_config = os.path.join(ruta_actual, nombre_archivo_config)

        # Solo para debug: mostrar qué ruta está buscando
        logger.debug(f"Buscando archivo de configuración en: {ruta_completa_config}")

        with open(ruta_completa_config, "r", encoding="utf-8") as archivo:
            config = yaml.safe_load(archivo)

        logger.success("Archivo de configuración cargado correctamente.")
        return config

    except FileNotFoundError:
        logger.critical(f"No se encontró el archivo: {ruta_completa_config}")
        raise

    except yaml.YAMLError as e:
        logger.critical(f"Error al parsear YAML: {e}")
        raise

class ConfigWrapper:
    """
    Wrapper para un diccionario que permite el acceso a claves anidadas mediante atributos.

    Esta clase actúa como un contenedor (wrapper) para un diccionario, proporcionando una forma 
    más conveniente de acceder a claves anidadas utilizando notación de puntos (atributos), 
    en lugar de índices basados en cadenas. También permite acceder directamente a valores 
    con un método auxiliar.

    Args:
        config (dict): Diccionario que se desea envolver para acceder a sus claves de forma anidada.

    Métodos:
        __getattr__(item):
            Permite acceder a claves anidadas del diccionario como si fueran atributos. Si el valor 
            correspondiente es otro diccionario, lo envuelve automáticamente en otra instancia de 
            `ConfigWrapper`.

        get(key, default=None):
            Proporciona una forma explícita de obtener un valor del diccionario usando su clave. 
            Similar al método `get` de un diccionario estándar.

    """

    def __init__(self, config_dict: dict):
        """
        Inicializa la instancia de `ConfigWrapper`.

        Args:
            config (dict): Diccionario para envolver.
        """
        self.__config_dict = config_dict

    @property
    def as_dict(self):
        return self.__config_dict
    
    def __repr__(self):
        return repr(self.__config_dict)

    def __getattr__(self, item):
        """
        Permite acceder a claves del diccionario como atributos.

        Args:
            item (str): Clave del diccionario que se desea acceder.

        Returns:
            Cualquier valor asociado con la clave `item`. Si es un diccionario, 
            devuelve una instancia de `ConfigWrapper`.

        Raises:
            AttributeError: Si la clave no existe en el diccionario."""

        value = self.as_dict.get(item)
        if isinstance(value, dict):
            return ConfigWrapper(value)
        return value

    def get(self, key, default=None):
        """
        Proporciona acceso explícito a valores del diccionario, similar al método `get` de un diccionario estándar.

        Args:
            key (str): Clave del diccionario que se desea acceder.
            default (any, optional): Valor predeterminado si la clave no existe. Por defecto es `None`.

        Returns:
            Cualquier valor asociado con la clave `key`, o el valor predeterminado si no existe.
        """
        return self.as_dict.get(key, default)

NOM_CONFIG = "config.yaml"
config_dict = Procesar_configuracion(NOM_CONFIG)