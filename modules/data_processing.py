"""
Módulo de Procesamiento de Datos
Maneja importación, validación y transformación de datos del proyecto
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os
import tempfile
import warnings
import re
from io import BytesIO
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta


class DataProcessor:
    """
    Clase principal para procesamiento de datos del proyecto de inversión
    """

    def __init__(self):
        """Inicializar procesador de datos"""
        self.datos_validados = {}
        self.errores_validacion = []
        self.advertencias = []

    def validar_archivo_excel(self, archivo) -> Tuple[pd.DataFrame, List[str]]:
        """
        Valida y procesa archivo Excel de egresos

        Args:
            archivo: Archivo cargado por streamlit

        Returns:
            tuple: (DataFrame procesado, lista de errores)
        """
        errores = []

        try:
            # Intentar leer el archivo
            if archivo.name.endswith(".xlsx"):
                df = pd.read_excel(archivo, engine="openpyxl")
            elif archivo.name.endswith(".xls"):
                df = pd.read_excel(archivo, engine="xlrd")
            else:
                errores.append("Formato de archivo no soportado. Use .xlsx o .xls")
                return None, errores

            # Validar estructura básica
            if df.empty:
                errores.append("El archivo está vacío")
                return None, errores

            # Validar columnas requeridas
            columnas_requeridas = ["Concepto", "Monto"]
            columnas_faltantes = [
                col for col in columnas_requeridas if col not in df.columns
            ]

            if columnas_faltantes:
                errores.append(f"Columnas faltantes: {', '.join(columnas_faltantes)}")
                # Intentar detectar columnas similares
                columnas_similares = self._detectar_columnas_similares(
                    df.columns, columnas_requeridas
                )
                if columnas_similares:
                    errores.append(
                        f"Columnas detectadas que podrían ser correctas: {columnas_similares}"
                    )
                return None, errores

            # Limpiar y procesar datos
            df_procesado = self._limpiar_datos_egresos(df)

            # Validaciones específicas
            errores_validacion = self._validar_datos_egresos(df_procesado)
            errores.extend(errores_validacion)

            # Eliminar filas completamente vacías o inválidas
            df_final = self._filtrar_datos_validos(df_procesado)

            if df_final.empty:
                errores.append("No hay datos válidos después del procesamiento")
                return None, errores

            return df_final, errores

        except Exception as e:
            errores.append(f"Error procesando archivo: {str(e)}")
            return None, errores

    def _detectar_columnas_similares(
        self, columnas_archivo: List[str], columnas_requeridas: List[str]
    ) -> Dict[str, str]:
        """
        Detecta columnas con nombres similares a las requeridas

        Args:
            columnas_archivo: Columnas encontradas en el archivo
            columnas_requeridas: Columnas que se necesitan

        Returns:
            dict: Mapeo de columnas similares encontradas
        """
        import difflib

        similares = {}

        for requerida in columnas_requeridas:
            # Buscar coincidencias cercanas
            matches = difflib.get_close_matches(
                requerida.lower(),
                [col.lower() for col in columnas_archivo],
                n=1,
                cutoff=0.6,
            )

            if matches:
                # Encontrar la columna original correspondiente
                for col in columnas_archivo:
                    if col.lower() == matches[0]:
                        similares[requerida] = col
                        break

        return similares

    def _limpiar_datos_egresos(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y normaliza datos de egresos

        Args:
            df: DataFrame original

        Returns:
            pd.DataFrame: DataFrame limpio
        """
        df_limpio = df.copy()

        # Limpiar columna Concepto
        df_limpio["Concepto"] = (
            df_limpio["Concepto"]
            .astype(str)
            .str.strip()
            .str.title()  # Capitalizar primera letra
            .replace("", np.nan)
            .replace("Nan", np.nan)
        )

        # Limpiar y convertir columna Monto
        if df_limpio["Monto"].dtype == "object":
            # Remover símbolos monetarios y separadores
            df_limpio["Monto"] = (
                df_limpio["Monto"]
                .astype(str)
                .str.replace("$", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.replace(" ", "", regex=False)
                .str.strip()
            )

        # Convertir a numérico
        df_limpio["Monto"] = pd.to_numeric(df_limpio["Monto"], errors="coerce")

        # Detectar y corregir conceptos duplicados
        df_limpio = self._consolidar_conceptos_duplicados(df_limpio)

        return df_limpio

    def _consolidar_conceptos_duplicados(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Consolida conceptos con nombres similares o duplicados

        Args:
            df: DataFrame con posibles duplicados

        Returns:
            pd.DataFrame: DataFrame consolidado
        """
        # Buscar conceptos exactamente duplicados
        duplicados_exactos = df.groupby("Concepto")["Monto"].sum().reset_index()

        if len(duplicados_exactos) < len(df):
            advertencia = f"Se consolidaron {len(df) - len(duplicados_exactos)} conceptos duplicados"
            self.advertencias.append(advertencia)
            return duplicados_exactos

        # Buscar conceptos similares (opcional, más complejo)
        # Por ahora retornamos el DataFrame original si no hay duplicados exactos
        return df

    def _validar_datos_egresos(self, df: pd.DataFrame) -> List[str]:
        """
        Valida la calidad de los datos de egresos

        Args:
            df: DataFrame a validar

        Returns:
            list: Lista de errores encontrados
        """
        errores = []

        # Validar valores nulos
        conceptos_nulos = df["Concepto"].isna().sum()
        montos_nulos = df["Monto"].isna().sum()

        if conceptos_nulos > 0:
            errores.append(f"{conceptos_nulos} filas tienen conceptos vacíos")

        if montos_nulos > 0:
            errores.append(f"{montos_nulos} filas tienen montos inválidos")

        # Validar valores negativos
        montos_negativos = (df["Monto"] < 0).sum()
        if montos_negativos > 0:
            errores.append(f"{montos_negativos} montos son negativos")

        # Validar valores excesivamente altos (posibles errores de digitación)
        percentil_95 = df["Monto"].quantile(0.95)
        montos_atipicos = (df["Monto"] > percentil_95 * 10).sum()
        if montos_atipicos > 0:
            self.advertencias.append(
                f"{montos_atipicos} montos parecen excesivamente altos"
            )

        # Validar longitud de conceptos
        conceptos_largos = (df["Concepto"].str.len() > 100).sum()
        if conceptos_largos > 0:
            self.advertencias.append(
                f"{conceptos_largos} conceptos tienen nombres muy largos"
            )

        return errores

    def _filtrar_datos_validos(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filtra solo datos válidos

        Args:
            df: DataFrame a filtrar

        Returns:
            pd.DataFrame: DataFrame solo con datos válidos
        """
        # Eliminar filas con concepto o monto nulo
        df_valido = df.dropna(subset=["Concepto", "Monto"])

        # Eliminar montos negativos o cero
        df_valido = df_valido[df_valido["Monto"] > 0]

        # Eliminar conceptos vacíos después del procesamiento
        df_valido = df_valido[df_valido["Concepto"].str.len() > 0]

        return df_valido.reset_index(drop=True)

    def generar_distribucion_temporal(
        self,
        monto_base: float,
        meses: int,
        tipo_distribucion: str = "uniforme",
        factor_crecimiento: float = 0.02,
    ) -> Dict[int, float]:
        """
        Genera distribución temporal de montos

        Args:
            monto_base: Monto base a distribuir
            meses: Número de meses
            tipo_distribucion: Tipo de distribución
            factor_crecimiento: Factor de crecimiento mensual

        Returns:
            dict: Distribución por mes
        """
        distribucion = {}

        if tipo_distribucion == "uniforme":
            monto_mensual = monto_base / meses
            for mes in range(1, meses + 1):
                distribucion[mes] = monto_mensual

        elif tipo_distribucion == "creciente":
            # Distribución aritmética creciente
            suma_factores = sum(range(1, meses + 1))
            for mes in range(1, meses + 1):
                factor = mes / suma_factores
                distribucion[mes] = monto_base * factor

        elif tipo_distribucion == "decreciente":
            # Distribución aritmética decreciente
            suma_factores = sum(range(1, meses + 1))
            for mes in range(1, meses + 1):
                factor = (meses - mes + 1) / suma_factores
                distribucion[mes] = monto_base * factor

        elif tipo_distribucion == "exponencial":
            # Crecimiento exponencial
            for mes in range(1, meses + 1):
                factor_exp = (1 + factor_crecimiento) ** (mes - 1)
                distribucion[mes] = (monto_base / meses) * factor_exp

        elif tipo_distribucion == "estacional":
            # Distribución estacional (simulada)
            factores_estacionales = self._generar_factores_estacionales(meses)
            suma_factores = sum(factores_estacionales.values())

            for mes in range(1, meses + 1):
                factor = factores_estacionales[mes] / suma_factores
                distribucion[mes] = monto_base * factor

        return distribucion

    def _generar_factores_estacionales(self, meses: int) -> Dict[int, float]:
        """
        Genera factores estacionales simulados

        Args:
            meses: Número de meses

        Returns:
            dict: Factores por mes
        """
        import math

        factores = {}
        for mes in range(1, meses + 1):
            # Simulación de estacionalidad con función seno
            # Mayor actividad a mitad de año, menor al final/inicio
            ciclo_anual = (mes % 12) / 12 * 2 * math.pi
            factor_base = 1.0
            variacion_estacional = 0.3 * math.sin(ciclo_anual + math.pi / 2)
            factores[mes] = factor_base + variacion_estacional

        return factores

    def proyectar_serie_temporal(
        self,
        valor_base: float,
        meses: int,
        tasa_crecimiento: float = 0.0,
        volatilidad: float = 0.02,
        tendencia: str = "lineal",
    ) -> List[float]:
        """
        Proyecta serie temporal con crecimiento y volatilidad

        Args:
            valor_base: Valor inicial
            meses: Número de meses a proyectar
            tasa_crecimiento: Tasa de crecimiento mensual
            volatilidad: Nivel de volatilidad (desviación estándar)
            tendencia: Tipo de tendencia ('lineal', 'exponencial', 'logistica')

        Returns:
            list: Serie temporal proyectada
        """
        np.random.seed(42)  # Para reproducibilidad
        serie = []

        for mes in range(meses):
            if tendencia == "lineal":
                valor_tendencia = valor_base * (1 + tasa_crecimiento * mes)
            elif tendencia == "exponencial":
                valor_tendencia = valor_base * ((1 + tasa_crecimiento) ** mes)
            elif tendencia == "logistica":
                # Crecimiento logístico con límite
                limite_superior = valor_base * 2
                k = 0.5  # Tasa de crecimiento logístico
                valor_tendencia = limite_superior / (1 + np.exp(-k * (mes - meses / 2)))
            else:
                valor_tendencia = valor_base

            # Agregar ruido aleatorio
            ruido = np.random.normal(0, volatilidad * valor_tendencia)
            valor_final = max(
                0, valor_tendencia + ruido
            )  # No permitir valores negativos

            serie.append(valor_final)

        return serie

    def calcular_metricas_serie(self, serie: List[float]) -> Dict[str, float]:
        """
        Calcula métricas estadísticas de una serie temporal

        Args:
            serie: Serie de datos

        Returns:
            dict: Métricas calculadas
        """
        if not serie:
            return {}

        serie_array = np.array(serie)

        metricas = {
            "media": np.mean(serie_array),
            "mediana": np.median(serie_array),
            "desviacion_estandar": np.std(serie_array),
            "coeficiente_variacion": (
                np.std(serie_array) / np.mean(serie_array) * 100
                if np.mean(serie_array) != 0
                else 0
            ),
            "minimo": np.min(serie_array),
            "maximo": np.max(serie_array),
            "rango": np.max(serie_array) - np.min(serie_array),
            "suma_total": np.sum(serie_array),
            "percentil_25": np.percentile(serie_array, 25),
            "percentil_75": np.percentile(serie_array, 75),
            "asimetria": self._calcular_asimetria(serie_array),
            "curtosis": self._calcular_curtosis(serie_array),
            "tasa_crecimiento_promedio": self._calcular_tasa_crecimiento_promedio(
                serie_array
            ),
        }

        return metricas

    def _calcular_asimetria(self, serie: np.ndarray) -> float:
        """Calcula la asimetría de la serie"""
        try:
            from scipy import stats

            return stats.skew(serie)
        except ImportError:
            # Cálculo manual si scipy no está disponible
            n = len(serie)
            if n < 3:
                return 0

            media = np.mean(serie)
            std = np.std(serie, ddof=1)
            if std == 0:
                return 0

            asimetria = np.sum(((serie - media) / std) ** 3) * n / ((n - 1) * (n - 2))
            return asimetria

    def _calcular_curtosis(self, serie: np.ndarray) -> float:
        """Calcula la curtosis de la serie"""
        try:
            from scipy import stats

            return stats.kurtosis(serie, fisher=True)
        except ImportError:
            # Cálculo manual si scipy no está disponible
            n = len(serie)
            if n < 4:
                return 0

            media = np.mean(serie)
            std = np.std(serie, ddof=1)
            if std == 0:
                return 0

            curtosis = np.sum(((serie - media) / std) ** 4) * n * (n + 1) / (
                (n - 1) * (n - 2) * (n - 3)
            ) - 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
            return curtosis

    def _calcular_tasa_crecimiento_promedio(self, serie: np.ndarray) -> float:
        """Calcula la tasa de crecimiento promedio de la serie"""
        if len(serie) < 2:
            return 0

        # Eliminar valores cero para evitar problemas matemáticos
        serie_sin_ceros = serie[serie > 0]
        if len(serie_sin_ceros) < 2:
            return 0

        # Tasa de crecimiento geométrico
        try:
            tasa_crecimiento = (serie_sin_ceros[-1] / serie_sin_ceros[0]) ** (
                1 / (len(serie_sin_ceros) - 1)
            ) - 1
            return tasa_crecimiento * 100  # Convertir a porcentaje
        except:
            return 0

    def generar_escenarios_monte_carlo(
        self, parametros_base: Dict, num_simulaciones: int = 1000
    ) -> Dict[str, List[float]]:
        """
        Genera escenarios usando simulación Monte Carlo

        Args:
            parametros_base: Parámetros base del proyecto
            num_simulaciones: Número de simulaciones

        Returns:
            dict: Resultados de las simulaciones
        """
        np.random.seed(42)

        resultados = {"tir": [], "vpn": [], "roi": [], "payback": []}

        for _ in range(num_simulaciones):
            # Generar variaciones aleatorias en parámetros clave
            factor_ingresos = np.random.normal(1.0, 0.15)  # ±15% variación
            factor_egresos = np.random.normal(1.0, 0.10)  # ±10% variación
            factor_inversion = np.random.normal(1.0, 0.05)  # ±5% variación

            # Aplicar factores a parámetros base (simulado)
            ingresos_sim = [
                ing * factor_ingresos for ing in parametros_base.get("ingresos", [])
            ]
            egresos_sim = [
                egr * factor_egresos for egr in parametros_base.get("egresos", [])
            ]
            inversion_sim = parametros_base.get("inversion", 100000) * factor_inversion

            # Calcular métricas simuladas (simplificado)
            flujo_sim = [ing - egr for ing, egr in zip(ingresos_sim, egresos_sim)]

            # Simulación simplificada de TIR
            beneficio_total = sum(flujo_sim)
            if inversion_sim > 0 and beneficio_total > 0:
                tir_sim = (beneficio_total / inversion_sim) ** (1 / len(flujo_sim)) - 1
                vpn_sim = beneficio_total - inversion_sim  # Simplificado
                roi_sim = (beneficio_total - inversion_sim) / inversion_sim * 100

                # Payback simplificado
                acumulado = 0
                payback_sim = len(flujo_sim)
                for i, flujo in enumerate(flujo_sim):
                    acumulado += flujo
                    if acumulado >= inversion_sim:
                        payback_sim = i + 1
                        break

                resultados["tir"].append(tir_sim)
                resultados["vpn"].append(vpn_sim)
                resultados["roi"].append(roi_sim)
                resultados["payback"].append(payback_sim)

        return resultados

    def exportar_datos_procesados(self, datos: Dict, formato: str = "excel") -> bytes:
        """
        Exporta datos procesados en formato especificado

        Args:
            datos: Datos a exportar
            formato: Formato de exportación ('excel', 'csv', 'json')

        Returns:
            bytes: Datos exportados
        """
        from io import BytesIO
        import json

        if formato == "excel":
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                for nombre_hoja, df in datos.items():
                    if isinstance(df, pd.DataFrame):
                        df.to_excel(writer, sheet_name=nombre_hoja, index=False)
            buffer.seek(0)
            return buffer.getvalue()

        elif formato == "csv":
            # Exportar primera hoja como CSV
            if datos:
                primer_df = next(iter(datos.values()))
                if isinstance(primer_df, pd.DataFrame):
                    return primer_df.to_csv(index=False).encode("utf-8")

        elif formato == "json":
            # Convertir DataFrames a diccionarios para JSON
            datos_json = {}
            for key, value in datos.items():
                if isinstance(value, pd.DataFrame):
                    datos_json[key] = value.to_dict("records")
                else:
                    datos_json[key] = value

            return json.dumps(datos_json, indent=2, ensure_ascii=False).encode("utf-8")

        return b""

    def limpiar_cache(self):
        """Limpia cache de datos procesados"""
        self.datos_validados = {}
        self.errores_validacion = []
        self.advertencias = []
