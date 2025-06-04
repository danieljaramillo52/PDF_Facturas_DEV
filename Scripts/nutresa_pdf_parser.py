import re
import pdfplumber
import pandas as pd
from typing import Dict, Any, Optional

from itertools import chain, repeat


def concatenar_lista_itertools(lista: list, n: int) -> list:
    """Versión optimizada para grandes listas o n."""
    return list(chain.from_iterable(repeat(lista, n)))


class ProcesadorPDFNutresa:
    def __init__(self, pdf_path: str, dict_claves: Any):
        self.pdf_path = pdf_path
        self.dict_claves = dict_claves
        self.regex_dict = self._compilar_regex()
        self.texto = self._extraer_texto_pdf()
        self.lineas = self.texto.split("\n")
        self.cabecera = {}
        self.cabecera_extendida = {}
        self.productos = []
        self.observaciones = ""

    def _parsear_producto_desde_linea(
        self, linea: str, list_claves_prod: list
    ) -> dict | None:
        tokens = linea.strip().split()

        if len(tokens) < 10:
            return None

        try:
            codigo_barras = tokens[0]
            idx_bodega = next(
                i for i, t in enumerate(tokens[1:], 1) if re.match(r"^\d{5}$", t)
            )
            descripcion = " ".join(tokens[1:idx_bodega])
            campos = tokens[idx_bodega : idx_bodega + 7]

            return {
                "EAN_UN": codigo_barras,
                "descripcion": descripcion,
                **dict(zip(list_claves_prod, campos)),
            }
        except (StopIteration, IndexError):
            return None

    def _compilar_regex(self) -> Dict[str, re.Pattern]:
        return {
            "fecha": re.compile(r"\d{2}/\d{2}/\d{4}"),
            "EAN_UN": re.compile(r"\d{13}"),
            "precio": re.compile(r"\$\d{1,3}(?:\.\d{3})*,\d{2}"),
            "observación": re.compile(r"^Observación:.*"),
            "Número":re.compile(r"Número:\s+(\d{3}-[A-Z]{3}-\d{8})")
        }

    def _extraer_texto_pdf(self) -> Optional[str]:
        """
        Extrae texto de todas las páginas de un PDF, incluyendo documentos multipágina.

        Returns:
            str: Texto concatenado de todas las páginas
            None: Si ocurre un error o el PDF está vacío

        Raises:
            FileNotFoundError: Si el archivo PDF no existe
            PDFSyntaxError: Si el PDF está corrupto o encriptado
        """
        texto_completo = []

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                # Iterar sobre todas las páginas del documento
                for pagina in pdf.pages:
                    # Extraer texto y manejar páginas vacías
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto_completo.append(texto_pagina.strip())

                return "\n".join(texto_completo) if texto_completo else None

        except FileNotFoundError:
            print(f"Error: Archivo no encontrado - {self.pdf_path}")
            return None
        except pdfplumber.pdf.PDFSyntaxError as e:
            print(f"Error en formato PDF: {str(e)}")
            return None
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            return None

    def _obtener_patrones_y_lineas_filtradas(self):
        """
        Obtiene los patrones y filtra las líneas según las expresiones regulares
        definidas para productos y observaciones.

        Returns:
            tuple: (pattern_obs, pattern_prod, lineas_sin_coincidencias, lineas_observaciones, lineas_productos)
        """
        pattern_obs = self.regex_dict["observación"]
        pattern_prod = self.regex_dict["EAN_UN"]

        lineas_observaciones = list(filter(pattern_obs.search, self.lineas))
        lineas_productos = list(filter(pattern_prod.search, self.lineas))

        lineas_sin_coincidencias = [
            linea
            for linea in self.lineas
            if not (pattern_obs.search(linea) or pattern_prod.search(linea))
        ]

        return (
            pattern_obs,
            pattern_prod,
            lineas_sin_coincidencias,
            lineas_observaciones,
            lineas_productos,
        )

    def _procesar_lineas(self):
        """
        Procesa el contenido del PDF dividiéndolo en tres secciones: cabecera, productos y observaciones.
        Optimiza el procesamiento deteniendo la lectura de cabecera cuando se detecta la palabra 'Item'.
        """
        _, _, lineas_posible_cabecera, lineas_observaciones, lineas_productos = (
            self._obtener_patrones_y_lineas_filtradas()
        )

        self._procesar_cabecera(lineas_posible_cabecera=lineas_posible_cabecera)

        for linea in lineas_productos:
            self._procesar_productos(linea)

        self._procesar_observaciones(list_observaciones=lineas_observaciones)

    def _procesar_cabecera(self, lineas_posible_cabecera):
        """
        Procesa las líneas iniciales del PDF para extraer la cabecera del documento.
        Detecta tipo de documento, fecha y campos configurados según etiquetas.
        La lectura se detiene automáticamente al encontrar el marcador 'Item',
        que indica el inicio de la sección de productos.
        """
        mapeo = self.dict_claves.mapeo_cabecera
        for i, linea in enumerate(lineas_posible_cabecera):
            if "DEVOLUCIONES DE AVERIAS" in linea:
                self.cabecera["tipo_documento"] = linea.strip()

            elif "Número" in linea and "Número" not in self.cabecera:
                match = self.regex_dict["Número"].search(linea)
                if match:
                    self.cabecera["Número"] = match.group(1)
                    continue
                    
            elif self._es_linea_de_etiqueta(linea, mapeo):
                self._extraer_valor_etiqueta(linea, i, mapeo)

    def _es_linea_de_etiqueta(self, linea: str, mapeo) -> bool:
        """
        Determina si una línea contiene alguna de las etiquetas definidas
        en el mapeo de cabecera.

        Args:
            linea (str): Línea del PDF a analizar.
            mapeo: Objeto con el diccionario de etiquetas y claves de cabecera.

        Returns:
            bool: True si la línea contiene al menos una etiqueta válida.
        """
        return any(etiqueta in linea for etiqueta in mapeo.as_dict)

    def _extraer_valor_etiqueta(self, linea: str, i: int, mapeo):
        """
        Extrae el valor asociado a una etiqueta de cabecera en la línea actual,
        y lo guarda en el diccionario `cabecera_extendida`. El valor se obtiene
        de la línea siguiente a la etiqueta encontrada.

        Args:
            linea (str): Línea actual que contiene una etiqueta.
            i (int): Índice de la línea actual.
            mapeo: Objeto con el diccionario de etiquetas y claves configuradas.
        """
        for etiqueta, clave in mapeo.as_dict.items():
            if etiqueta in linea and i + 1 < len(self.lineas):
                valor = self.lineas[i + 1].strip()
                if clave == "telefono":
                    valor = valor.split()[0]
                self.cabecera_extendida[clave] = valor
                break

    def _procesar_productos(self, linea: str) -> str:
        """
        Procesa una línea dentro del estado 'productos'. Detecta líneas con productos mediante expresiones
        regulares y utiliza un parser externo para extraer los datos. También detecta el cambio a estado
        'observaciones' si corresponde.

        Args:
            linea (str): Línea de texto a procesar.

        Returns:
            str: El nuevo estado si hay un cambio, o None si el estado permanece igual.
        """
        producto = self._parsear_producto_desde_linea(
            linea=linea, list_claves_prod=self.dict_claves.productos
        )
        if producto:
            self.productos.append(producto)

    def _procesar_observaciones(self, list_observaciones: str):
        """
        Procesa una línea dentro del estado 'observaciones', concatenándola al texto total
        de observaciones con espacios para mantener la coherencia.

        Args:
            linea (str): Línea de texto a agregar a las observaciones.
        """
        for linea in list_observaciones:
            self.observaciones += linea.split(":", 1)[1].strip()

    def _limpiar_cabecera(self) -> Dict[str, str]:
        texto_comb = " ".join(
            [
                self.cabecera_extendida.get("NIT", ""),
                self.cabecera_extendida.get("proveedor", ""),
                self.cabecera_extendida.get("contacto", ""),
                self.cabecera_extendida.get("direccion", ""),
                self.cabecera_extendida.get("ciudad", ""),
                self.cabecera_extendida.get("telefono", ""),
                
            ]
        )

        patron_campos = self.dict_claves.patrones_cabecera

        cabecera_limpia = {
            "tipo_documento": self.cabecera.get("tipo_documento", ""),
            "Número": self.cabecera.get("Número", ""),
           
        }

        for clave, patron in patron_campos.as_dict.items():
            match = re.search(patron, texto_comb)
            if match:
                cabecera_limpia[clave] = (
                    match.group(1).strip() if match.group(1) else ""
                )

        return cabecera_limpia

    def _construir_dict_info_pdf(self, cabecera_limpia: dict) -> dict:
        return {
            "cabecera": cabecera_limpia,
            "productos": self.productos,
            "observaciones": self.observaciones.strip(),
        }

    @staticmethod
    def _crear_df_productos(dict_info_pdf: dict) -> pd.DataFrame:
        """Retrona el dataframe con la información de los productos, extrayendo esta clave del diccionario.

        Args:
            dict_info_pdf (dict): diccionario de donde se hace la extracción.

        Returns:
            pd.Dataframe: DataFrame de productos convertido.
        """
        df_productos = pd.DataFrame(dict_info_pdf["productos"])
        return df_productos

    def procesar(self) -> Dict[str, pd.DataFrame]:
        """
        Orquesta el flujo de procesamiento del PDF estructurado.

        Este método ejecuta los pasos principales para procesar la información:
        1. Extrae y organiza las líneas del documento.
        2. Limpia y estructura la cabecera.
        3. Construye un diccionario con la información relevante.
        4. Convierte los productos a un DataFrame de pandas.

        Returns:
            Dict[str, pd.DataFrame]: Un diccionario con dos claves:
                - "info_pdf": contiene la información estructurada del PDF.
                - "df_productos": DataFrame con los productos extraídos.
        """
        self._procesar_lineas()
        cabecera_limpia = self._limpiar_cabecera()
        dict_info_pdf = self._construir_dict_info_pdf(cabecera_limpia)
        df_productos = self._crear_df_productos(dict_info_pdf)

        return {"info_pdf": dict_info_pdf, "df_productos": df_productos}
