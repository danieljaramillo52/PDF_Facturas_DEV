# Importaciones de librerías estándar y externas.
import config_path_routes
import nutresa_pdf_parser as npp
from pandas import DataFrame, concat
from typing import Dict
from collections import defaultdict

# Importaciones de módulos específicos del proyecto.
import general_functions as gf
import transformation_functions as tf
from config_loader import ConfigWrapper, config_dict


class Run:
    def __init__(self):
        """
        Inicializa la clase configurando el wrapper y cargando las claves necesarias.

        Args:
            ruta_pdf (str): Ruta al archivo PDF que se desea procesar.
        """
        self.config_wrapper = ConfigWrapper(config_dict=config_dict)
        self.paths = self.config_wrapper.config_paths
        self.path_pdfs = self.paths.path_facturas
        self.inusmos_adic = self.paths.path_insumos_adic
        self.path_plant_ecazdo = self.paths.path_plant_encabezado
        self.dict_claves = self.config_wrapper.config_claves_pdf
        self.insumos = self.config_wrapper.Insumos

    def main(self) -> Dict[str, DataFrame]:
        """
        Ejecuta el proceso principal del programa
        """
        COD_MATERIAL = "COD_MATERIAL"
        CONCATENADA = "concatenado"
        EAN_UN = "EAN_UN"
        PDV = "PDV"

        list_path_pdfs = gf.listar_elementos_rutas_completas(self.path_pdfs)

        dict_pdfs_cabecera = defaultdict(list)
        for cada_pdf in list_path_pdfs:
            procesor_pdf = npp.ProcesadorPDFNutresa(
                pdf_path=cada_pdf, dict_claves=self.dict_claves
            )
            dict_pdf_obser_prod = procesor_pdf.procesar()

            num_cabecera = dict_pdf_obser_prod["info_pdf"]["cabecera"]["Número"][0:3]

            observación = dict_pdf_obser_prod["info_pdf"]["observaciones"]

            dict_pdfs_cabecera[(num_cabecera, observación)].append(
                dict_pdf_obser_prod["df_productos"]
            )

        # Procesar maestra de precios
        lector_insumos_excel = gf.ExcelReader(path=self.inusmos_adic)
        df_precios = lector_insumos_excel.Lectura_insumos_excel(
            nom_insumo=self.insumos.maestra_precios.nom_base,
            nom_hoja=self.insumos.maestra_precios.nom_hoja,
        )
        df_data_megatiendas = lector_insumos_excel.Lectura_insumos_excel(
            nom_insumo=self.insumos.maestra_megatiendas.nom_base,
            nom_hoja=self.insumos.maestra_megatiendas.nom_hoja,
        )

        # Filtrar por cadenas regionales.
        # df_prec_fil_por_cadnea = df_precios[
        #    df_precios["DESCR_GCLT"] == "Cadenas Regionales"
        # ]
        # df_precios =
        
        df_prec_select = tf.seleccionar_columnas_pd(
            df=df_precios,
            cols_elegidas=self.insumos.maestra_precios.cols,
        )

        df_prec_select_sin_dup = df_prec_select.drop_duplicates(
            subset=EAN_UN, inplace=False
        )

        # Cargar la plantilla base una sola vez
        plantilla_base = tf.ExcelPlantilla.cargar_desde_archivo(self.path_plant_ecazdo)

        cols_concatenar = self.insumos.maestra_megatiendas.cols[0:-1]

        df_data_megatiendas[CONCATENADA] = (
            df_data_megatiendas[cols_concatenar].astype(str).agg("_".join, axis=1)
        )

        dict_oficina_nombre = tf.Crear_diccionario_desde_dataframe(
            df=df_data_megatiendas, col_clave=PDV, col_valor=CONCATENADA
        )

        # Procesar por cada key
        # Claves faltantes insumo.
        list_faltantes_df_precios_total = []
        for cada_tuple_key, list_dfs in dict_pdfs_cabecera.items():
            if len(list_dfs) > 1:
                df_product_combinado = concat(list_dfs, axis=0)
            else:
                df_product_combinado = list_dfs[0]

            df_precios_merge = tf.pd_left_merge(
                base_left=df_product_combinado,
                base_right=df_prec_select_sin_dup,
                key=EAN_UN,
            )
            df_precios_merge

            list_faltantes_df_precios = df_precios_merge[
                df_precios_merge[COD_MATERIAL].isnull()
            ][EAN_UN].tolist()

            # Modifcar elementos flatantes
            if len(list_faltantes_df_precios) > 0:
                list_faltantes_df_precios = [
                    cada_tuple_key[0] + " " + cada_ean
                    for cada_ean in list_faltantes_df_precios
                ]
            
            list_faltantes_df_precios_total.extend(list_faltantes_df_precios)

            df_plantilla_cols_finales = tf.seleccionar_columnas_pd(
                df=df_precios_merge,
                cols_elegidas=self.config_wrapper.config_claves_pdf.cols_finales,
            )

            cod_dva = cada_tuple_key[0]
            nomb = dict_oficina_nombre[cada_tuple_key[0]]
            obs = cada_tuple_key[1]

            plantilla = plantilla_base.clonar_con_salida(
                ruta_salida=f"Plantilla_Resultado\devolución_{cod_dva}_{nomb}_{obs}.xlsx"
            )

            plantilla.insertar_dataframe(df_plantilla_cols_finales)

            plantilla.aplicar_lista_desplegable(
                columna=tf.ExcelPlantilla.COL_MOTIVOS,
                opciones=self.config_wrapper.config_claves_pdf.motivos_devolucion,
            )

            plantilla.guardar()

        with open(
            "Plantilla_Resultado\Codigos_EAN_Faltantes.txt", "w", encoding="utf-8"
        ) as f:
            for item in list_faltantes_df_precios_total:
                f.write(f"{item}\n")


if __name__ == "__main__":
    # Obteenr lugar de ejecución.
    import config_path_routes
    config_path_routes.Obtener_lugar_de_ejecucion()

    # Configuración básica del logger
    gf.logger_basic_config()

    # Crear instancia de Run y ejecutar
    Iniciar_proceso = Run()
    Iniciar_proceso.main()
