## Funciones básicas - Generales del proyecto_CxS Parte3
import pandas as pd
import time
import os
import inspect
import json
import time
from typing import Dict
from loguru import logger
from pathlib import Path
import openpyxl


def logger_basic_config():
    # Reconfigurar el logger para agregar una línea en blanco después de cada mensaje
    # Configurar el logger con formato de hora y minuto
    logger.remove()
    logger.add(
        sink=lambda msg: print(msg, end="\n"),
        format="<green>{time:HH:mm}</green> | <level>{level}</level> | {message}",
    )


def Registro_tiempo(original_func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = original_func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(
            "Tiempo de ejecución de {}: {:.2f} segundos".format(
                original_func.__name__, execution_time
            )
        )
        return result

    return wrapper



def listar_elementos_rutas_completas(ruta: str) -> list:
    """
    Genera rutas completas de todos los elementos en un directorio especificado.

    Parámetros:
        ruta (str): Ruta absoluta o relativa del directorio a listar.

    Retorna:
        list: Lista de strings con las rutas completas de los elementos encontrados.
               Retorna lista vacía si ocurre un error.

    Lanza:
        TypeError: Si el parámetro 'ruta' no es un string.
    
    Ejemplos:
        >>> listar_elementos_rutas_completas('/ruta/a/mi/directorio')
        ['/ruta/a/mi/directorio/archivo.txt', '/ruta/a/mi/directorio/subdirectorio']
    """
    try:
        # Validación de tipo de entrada
        if not isinstance(ruta, str):
            raise TypeError("El parámetro 'ruta' debe ser un string")
        
        # Verificar si la ruta existe y es directorio
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"La ruta no existe: {ruta}")
            
        if not os.path.isdir(ruta):
            raise NotADirectoryError(f"La ruta no es un directorio: {ruta}")

        # Generar lista de rutas completas
        return [os.path.join(ruta, elemento) for elemento in os.listdir(ruta)]

    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        print(f"Error al acceder al directorio: {str(e)}")
        return []
        
    except TypeError as e:
        print(f"Error en tipo de dato: {str(e)}")
        return []
        
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return []

class ErrorHandler:
    @staticmethod
    def log_error(e, message):
        # Usamos inspect para capturar el marco de la llamada actual
        current_frame = inspect.currentframe()
        # Vamos dos niveles arriba para capturar el punto desde donde fue llamada la función 'seleccionar_columnas_pd'
        call_frame = inspect.getouterframes(current_frame, 2)[2]
        logger.critical(
            f"{message} - Error occurred in file {call_frame.filename}, line {call_frame.lineno}"
        )


def exportar_a_excel(
    df: pd.DataFrame,
    ruta_guardado: str,
    nom_base: str,
    nom_hoja: str,
    index: bool = False,
) -> None:
    """
    Exporta un dataframe de pandas a un archivo excel en la ruta especificada.

    Args:
        ruta_guardado: Ruta donde se guardará el archivo excel.
        df: Dataframe de pandas que se exportará.
        nom_hoja: Nombre de la hoja de cálculo donde se exportará el dataframe.
        index: Indica si se debe incluir el índice del dataframe en el archivo excel.

    Returns:
        None.

    Raises:
        FileNotFoundError: Si la ruta de guardado no existe.
    """

    # Comprobar que la ruta de guardado existe
    try:
        logger.info(f"Exportando a excel: {nom_base}")
        df.to_excel(ruta_guardado + nom_base, sheet_name=nom_hoja, index=index)
    except Exception as e:
        raise Exception


def crear_diccionario_desde_dataframe(
    df: pd.DataFrame, col_clave: str, col_valor: str
) -> dict:
    """
    Crea un diccionario a partir de un DataFrame utilizando dos columnas especificadas.

    Args:
        df (pd.DataFrame): El DataFrame de entrada.
        col_clave (str): El nombre de la columna que se utilizará como clave en el diccionario.
        col_valor (str): El nombre de la columna que se utilizará como valor en el diccionario.

    Returns:
        dict: Un diccionario creado a partir de las columnas especificadas.
    """
    try:
        # Verificar si las columnas existen en el DataFrame
        if col_clave not in df.columns or col_valor not in df.columns:
            raise ValueError("Las columnas especificadas no existen en el DataFrame.")

        if col_clave == col_valor:
            resultado_dict = df[col_clave].to_dict()
        else:
            resultado_dict = df.set_index(col_clave)[col_valor].to_dict()
        return resultado_dict

    except ValueError as ve:
        # Registrar un mensaje crítico si hay un error
        logger.critical(f"Error: {ve}")
        raise ve


class ExcelReader:
    def __init__(self, path: str):
        self.path = path

    @Registro_tiempo
    def Lectura_insumos_excel(
        self,
        nom_insumo: str,
        nom_hoja: str,
        cols: int | list = None,
        skiprows: int = None,
        engine="openpyxl",
    ) -> pd.DataFrame:
        """
        Lee un archivo de Excel con opciones de personalización para la hoja, columnas y filas a omitir.

        Args:
            nom_insumo (str): Nombre del archivo de Excel a leer (incluye extensión, e.g., "archivo.xlsx").
            nom_hoja (str): Nombre de la hoja de Excel que se desea leer.
            cols (int | list, opcional):
                - Si es un entero, indica cuántas columnas iniciales se deben leer.
                - Si es una lista, especifica los índices o nombres de las columnas a leer.
                - Si es None, se leerán todas las columnas.
            skiprows (int, opcional): Número de filas iniciales que se deben omitir al leer el archivo.
                Por defecto, no omite filas.
            engine (str, opcional): Motor utilizado para leer el archivo Excel. Por defecto "openpyxl".

        Returns:
            pd.DataFrame: DataFrame con los datos leídos desde el archivo de Excel.

        Raises:
            Exception: Si ocurre un error durante la lectura del archivo, se lanza una excepción con
                detalles del problema.
        """
        if isinstance(cols, list):
            range_cols = cols
        elif isinstance(cols, int):
            range_cols = list(range(cols))
        else:
            range_cols = None  # No se especifican columnas

        try:
            logger.info(f"Inicio lectura {nom_insumo} Hoja: {nom_hoja}")
            base_leida = pd.read_excel(
                self.path + nom_insumo,
                sheet_name=nom_hoja,
                skiprows=skiprows,
                usecols=range_cols,  # Si range_cols es None, pd.read_excel leerá todas las columnas
                dtype=str,
                engine=engine,
            )
            logger.success(
                f"Lectura de {nom_insumo} Hoja: {nom_hoja} realizada con éxito"
            )
            return base_leida
        except Exception as e:
            logger.error(f"Proceso de lectura fallido: {e}")
            raise Exception(f"Error al leer el archivo: {e}")

    @Registro_tiempo
    def Lectura_simple_excel(self, nom_insumo: str, nom_hoja: str) -> pd.DataFrame:
        """
        Lee un archivo de Excel únicamente utilizando el nombre de su hoja sin parámetros adicionales.
        """
        try:
            logger.info(f"Inicio lectura simple de {nom_insumo}")
            base_leida = pd.read_excel(
                self.path + nom_insumo,
                sheet_name=nom_hoja,
                dtype=str,
            )
            logger.success(f"Lectura simple de {nom_insumo} realizada con éxito")
            return base_leida
        except Exception as e:
            logger.error(f"Proceso de lectura fallido: {e}")
            raise Exception(f"Error al leer el archivo: {e}")


def List_to_sql(values: list[str]):
    """
    Convierte una lista de valores en una cadena de valores SQL correctamenteformateada.
    Parameters:
    values (list of str): Lista de valores a convertir. Cada valor en la lista debeser una cadena (str).
    Returns:
    str: Una cadena de valores SQL separada por comas y entre comillas simples.
    Raises:
    TypeError: Si algún elemento de la lista no es una cadena (str).
    ValueError: Si la lista está vacía.
    """
    if not values:
        raise ValueError("La lista de valores no puede estar vacía.")
    for value in values:
        if not isinstance(value, str):
            raise TypeError(
                f"Todos los elementos de la lista deben ser cadenas (str). Elementoinválido: {value}"
            )
    return ", ".join(f"'{value}'" for value in values)


def crear_dict_col_llave_col_valores(df, columna_clave, columna_valores):
    """
    Crea un diccionario donde cada clave es un elemento único de una columna,
    y cada valor es una lista con los elementos correspondientes de otra columna.

    Parámetros:
    df (pd.DataFrame): El DataFrame del cual se extraerán los datos.
    columna_clave (str): El nombre de la columna que se usará como claves del diccionario.
    columna_valores (str): El nombre de la columna que se usará para los valores del diccionario.

    Retorna:
    dict: Un diccionario con las claves y valores especificados.
    """
    diccionario = {}
    for clave in df[columna_clave].unique():
        diccionario[clave] = (
            df.loc[df[columna_clave] == clave, columna_valores].unique().tolist()
        )
    return diccionario


def save_json_(dict_info_pdf, nombre_archivo="resultado_estructura.json"):
    """
    Guarda un diccionario en un archivo JSON y convierte la información en un DataFrame.

    Parámetros:
    ----------
    dict_info_pdf : dict
        Diccionario con la información extraída del PDF (por ejemplo, facturas u otra estructura).

    nombre_archivo : str, opcional
        Nombre del archivo JSON donde se guardará el diccionario. Por defecto es 'resultado_estructura.json'.

    """
    # Guardar el diccionario en un archivo JSON
    with open(nombre_archivo, "w", encoding="utf-8") as f:
        json.dump(dict_info_pdf, f, indent=2, ensure_ascii=False)


def convertir_a_dataframe(data):
    """
    Convierte un diccionario en un pandas DataFrame.

    Parámetros:
    ----------
    data : dict
        Diccionario que se desea convertir.

    Retorna:
    -------
    pd.DataFrame
        DataFrame que representa el contenido del diccionario.
    """
    return pd.DataFrame(data)