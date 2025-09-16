"""
Módulo de Utilidades - VERSIÓN COMPLETA
Contiene todas las funciones auxiliares necesarias para el sistema SEMAVENCA
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import re
from typing import Dict, List, Tuple, Optional, Union
from PIL import Image
import base64
from io import BytesIO
import random


def crear_header_empresa():
    st.markdown(
        """
        <style>
        .header-container {
            background: #fcfcfc;
            padding: 50px 30px;
            border-radius: 12px;
            color: #2c2c2c;
            text-align: left;
            font-family: 'Segoe UI', sans-serif;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-bottom: 40px;
            position: relative;
            width: 90%;
            max-width: 900px;
            margin-left: auto;
            margin-right: auto;
        }

        .postit-style {
            background: linear-gradient(135deg, #fdfdfd, #f0f0f0);
            border-left: 6px solid #F9A825;
            padding: 20px 25px;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        }

        .company-title {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 5px;
            color: #1a1a1a;
        }

        .project-subtitle {
            font-size: 20px;
            font-weight: 500;
            margin-bottom: 12px;
            color: #444;
        }

        .author-info {
            font-size: 14px;
            color: #333;
            font-style: italic;
        }

        .semaforo-lines {
            margin-top: 25px;
            display: flex;
            justify-content: flex-start;
            gap: 10px;
        }

        .line {
            width: 60px;
            height: 6px;
            border-radius: 3px;
            transition: background-color 1s ease-in-out;
        }

        .line.red { background-color: #C62828; }
        .line.yellow { background-color: #F9A825; }
        .line.green { background-color: #2E7D32; }

        @keyframes pulse {
            0% { opacity: 0.5; }
            50% { opacity: 1; }
            100% { opacity: 0.5; }
        }

        .line.red, .line.yellow, .line.green {
            animation: pulse 3s infinite;
        }

        .sphere {
            position: absolute;
            border-radius: 50%;
            width: 26px;
            height: 26px;
            opacity: 0.25;
            animation: drift 10s linear infinite;
        }

        .sphere.red { background-color: #FF4C4C; animation-delay: 0s; }
        .sphere.yellow { background-color: #FFF176; animation-delay: 3s; }
        .sphere.green { background-color: #66BB6A; animation-delay: 6s; }

        @keyframes drift {
            0%   { top: 0%; left: 0%; }
            25%  { top: 30%; left: 80%; }
            50%  { top: 70%; left: 60%; }
            75%  { top: 90%; left: 20%; }
            100% { top: 0%; left: 0%; }
        }
        </style>

        <div class="header-container">
            <div class="postit-style">
                <div class="company-title">SEMAVENCA</div>
                <div class="project-subtitle">Estudio Financiero de Proyectos de Inversión</div>
                <div class="author-info">
                Sistema de Evaluación de Proyectos v1.0 
                </div>
                <div class="semaforo-lines">
                    <div class="line red"></div>
                    <div class="line yellow"></div>
                    <div class="line green"></div>
                </div>
            </div>
            <div class="sphere red"></div>
            <div class="sphere yellow"></div>
            <div class="sphere green"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def validar_datos_entrada(datos: dict) -> Tuple[bool, List[str]]:
    """
    Valida los datos de entrada del proyecto

    Args:
        datos: Diccionario con los datos a validar

    Returns:
        tuple: (es_valido, lista_errores)
    """
    errores = []

    # Validar inversión inicial
    if "inversion_inicial" in datos:
        if datos["inversion_inicial"] <= 0:
            errores.append("La inversión inicial debe ser mayor a cero")
    else:
        errores.append("Falta especificar la inversión inicial")

    # Validar meses operativos
    if "meses_operativos" in datos:
        if datos["meses_operativos"] < 1 or datos["meses_operativos"] > 120:
            errores.append("Los meses operativos deben estar entre 1 y 120")

    # Validar flujos de efectivo
    if "flujos_efectivo" in datos:
        if not datos["flujos_efectivo"] or len(datos["flujos_efectivo"]) == 0:
            errores.append("No hay flujos de efectivo definidos")
        elif any(pd.isna(flujo) for flujo in datos["flujos_efectivo"]):
            errores.append("Hay flujos de efectivo con valores nulos")

    return len(errores) == 0, errores


def formatear_numero(numero: float, formato: str = "moneda") -> str:
    """
    Formatea números según el tipo especificado

    Args:
        numero: Número a formatear
        formato: Tipo de formato ('moneda', 'porcentaje', 'numero', 'miles')

    Returns:
        str: Número formateado
    """
    if pd.isna(numero):
        return "N/A"

    try:
        if formato == "moneda":
            return f"${numero:,.2f}"
        elif formato == "porcentaje":
            return f"{numero:.2%}"
        elif formato == "numero":
            return f"{numero:,.2f}"
        elif formato == "miles":
            return f"{numero/1000:.1f}K"
        else:
            return str(numero)
    except:
        return str(numero)


def crear_tarjeta_metrica(titulo: str, valor: float, formato: str = "numero") -> str:
    """
    Crea una tarjeta HTML con métricas estilizada

    Args:
        titulo: Título de la métrica
        valor: Valor de la métrica
        formato: Formato del valor

    Returns:
        str: HTML de la tarjeta
    """
    valor_formateado = formatear_numero(valor, formato)

    # Determinar color según el valor
    if formato == "porcentaje":
        color = "green" if valor > 0.15 else "orange" if valor > 0.10 else "red"
    elif formato == "moneda":
        color = "green" if valor > 0 else "red"
    else:
        color = "blue"

    return f"""
    <div style='background: white; padding: 20px; border-radius: 10px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 4px solid {color}; margin: 10px 0;'>
        <h3 style='margin: 0 0 10px 0; color: #333; font-size: 1.1em;'>{titulo}</h3>
        <p style='margin: 0; font-size: 1.8em; font-weight: bold; color: {color};'>{valor_formateado}</p>
    </div>
    """


def mostrar_alerta_personalizada(mensaje: str, tipo: str = "info"):
    """
    Muestra alertas personalizadas estilizadas

    Args:
        mensaje: Mensaje a mostrar
        tipo: Tipo de alerta ('success', 'error', 'warning', 'info')
    """
    colores = {
        "success": {"bg": "#d4edda", "border": "#28a745", "text": "#155724"},
        "error": {"bg": "#f8d7da", "border": "#dc3545", "text": "#721c24"},
        "warning": {"bg": "#fff3cd", "border": "#ffc107", "text": "#856404"},
        "info": {"bg": "#d1ecf1", "border": "#17a2b8", "text": "#0c5460"},
    }

    color_config = colores.get(tipo, colores["info"])

    st.markdown(
        f"""
        <div style='background-color: {color_config["bg"]}; 
                   border: 1px solid {color_config["border"]}; 
                   border-radius: 5px; padding: 15px; margin: 10px 0;
                   color: {color_config["text"]}; border-left: 4px solid {color_config["border"]};'>
            <strong>📢 {mensaje}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )


def cargar_archivo_excel(archivo) -> Tuple[Optional[pd.DataFrame], List[str]]:
    """
    Carga y valida archivo Excel con validaciones mejoradas

    Args:
        archivo: Archivo subido por streamlit

    Returns:
        tuple: (DataFrame procesado, lista de errores)
    """
    errores = []

    try:
        # Leer archivo Excel
        if archivo.name.endswith(".xlsx"):
            df = pd.read_excel(archivo, engine="openpyxl")
        elif archivo.name.endswith(".xls"):
            df = pd.read_excel(archivo, engine="xlrd")
        else:
            return None, ["Formato de archivo no soportado. Use .xlsx o .xls"]

        # Validar que no esté vacío
        if df.empty:
            return None, ["El archivo está vacío"]

        # Validar columnas requeridas
        columnas_requeridas = ["Concepto", "Monto"]
        columnas_faltantes = [
            col for col in columnas_requeridas if col not in df.columns
        ]

        if columnas_faltantes:
            # Intentar detectar columnas similares
            columnas_similares = _detectar_columnas_similares(
                df.columns, columnas_requeridas
            )
            if columnas_similares:
                # Renombrar columnas automáticamente
                df = df.rename(columns=columnas_similares)
                errores.append(
                    f"Columnas renombradas automáticamente: {columnas_similares}"
                )
            else:
                return None, [f"Columnas faltantes: {', '.join(columnas_faltantes)}"]

        # Limpiar datos
        df_limpio = _limpiar_datos_excel(df)

        # Validar datos después de limpieza
        if df_limpio.empty:
            return None, ["No hay datos válidos después de procesar el archivo"]

        return df_limpio, errores

    except Exception as e:
        return None, [f"Error procesando archivo: {str(e)}"]


def _detectar_columnas_similares(
    columnas_archivo: List[str], columnas_requeridas: List[str]
) -> Dict[str, str]:
    """
    Detecta columnas con nombres similares
    """
    import difflib

    similares = {}
    for requerida in columnas_requeridas:
        matches = difflib.get_close_matches(
            requerida.lower(),
            [col.lower() for col in columnas_archivo],
            n=1,
            cutoff=0.6,
        )
        if matches:
            for col in columnas_archivo:
                if col.lower() == matches[0]:
                    similares[col] = requerida
                    break

    return similares


def _limpiar_datos_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y valida datos del Excel según especificaciones
    """
    df_limpio = df[["Concepto", "Monto"]].copy()

    # Limpiar conceptos
    df_limpio["Concepto"] = df_limpio["Concepto"].astype(str).str.strip()

    # Reemplazar conceptos vacíos
    conceptos_vacios = (
        (df_limpio["Concepto"].isna())
        | (df_limpio["Concepto"] == "")
        | (df_limpio["Concepto"] == "nan")
    )
    df_limpio.loc[conceptos_vacios, "Concepto"] = "Gasto por identificar"

    # Limpiar montos
    df_limpio["Monto"] = pd.to_numeric(df_limpio["Monto"], errors="coerce")

    # Eliminar filas con montos cero, negativos o NaN
    df_limpio = df_limpio[
        (df_limpio["Monto"].notna()) & (df_limpio["Monto"] > 0)
    ].reset_index(drop=True)

    return df_limpio


def generar_datos_ejemplo() -> Dict:
    """
    Genera datos de ejemplo para el sistema

    Returns:
        dict: Datos de ejemplo
    """
    return {
        "inversion_inicial": 120000.0,
        "meses_preoperativos": 3,
        "multas_diarias": 200.0,
        "valor_multa_descuento": 180.0,
        "pct_pago_voluntario": 10.0,
        "pct_ingreso_operativo": 60.0,
        "meses_operativos": 45,
        "tasa_crecimiento_ingresos": 0.5,
        "tasa_crecimiento_egresos": 2.0,
    }


def crear_egresos_ejemplo() -> pd.DataFrame:
    """
    Crea DataFrame de ejemplo con egresos operativos

    Returns:
        pd.DataFrame: Datos de egresos de ejemplo
    """
    datos_egresos = {
        "Concepto": [
            "Sueldos y Salarios Personal",
            "Prestaciones Sociales",
            "Servicios Públicos",
            "Alquiler de Oficina",
            "Materiales de Oficina",
            "Combustible y Transporte",
            "Mantenimiento Equipos",
            "Seguros",
            "Servicios Profesionales",
            "Publicidad y Marketing",
            "Telecomunicaciones",
            "Gastos Bancarios",
            "Depreciación Equipos",
            "Otros Gastos Operativos",
        ],
        "Monto": [
            15000,
            4500,
            2800,
            3500,
            800,
            1200,
            1000,
            600,
            2000,
            1500,
            900,
            300,
            1800,
            1200,
        ],
    }

    return pd.DataFrame(datos_egresos)


def crear_costos_preoperativos_ejemplo() -> pd.DataFrame:
    """
    Crea DataFrame de ejemplo con costos preoperativos

    Returns:
        pd.DataFrame: Datos de costos preoperativos de ejemplo
    """
    datos_costos_preop = {
        "Concepto": [
            "Constitución Legal de la Empresa",
            "Permisos y Licencias",
            "Instalación y Adecuación Local",
            "Compra de Equipos Informáticos",
            "Software y Licencias",
            "Capacitación Personal",
            "Gastos de Marketing Pre-lanzamiento",
            "Estudios de Mercado",
            "Consultoría Legal y Contable",
            "Gastos de Organización",
        ],
        "Monto": [5000, 3000, 8000, 12000, 4000, 2500, 6000, 3500, 4500, 2000],
    }

    return pd.DataFrame(datos_costos_preop)


def calcular_estadisticas_descriptivas(serie: pd.Series) -> Dict[str, float]:
    """
    Calcula estadísticas descriptivas de una serie

    Args:
        serie: Serie de pandas con los datos

    Returns:
        dict: Estadísticas calculadas
    """
    if serie.empty:
        return {}

    serie_clean = serie.dropna()

    if serie_clean.empty:
        return {}

    estadisticas = {
        "Media": serie_clean.mean(),
        "Mediana": serie_clean.median(),
        "Desviación Estándar": serie_clean.std(),
        "Mínimo": serie_clean.min(),
        "Máximo": serie_clean.max(),
        "Suma Total": serie_clean.sum(),
        "Coeficiente de Variación": (
            (serie_clean.std() / serie_clean.mean() * 100)
            if serie_clean.mean() != 0
            else 0
        ),
        "Percentil 25": serie_clean.quantile(0.25),
        "Percentil 75": serie_clean.quantile(0.75),
        "Rango": serie_clean.max() - serie_clean.min(),
    }

    return estadisticas


def verificar_integridad_datos(proyecto) -> Tuple[bool, List[str]]:
    """
    Verifica la integridad de los datos del proyecto

    Args:
        proyecto: Instancia de ProyectoInversion

    Returns:
        tuple: (es_integro, lista_problemas)
    """
    problemas = []

    # Verificar inversión inicial
    if not hasattr(proyecto, "inversion_inicial") or proyecto.inversion_inicial <= 0:
        problemas.append("Inversión inicial no definida o inválida")

    # Verificar configuración de ingresos
    if (
        not hasattr(proyecto, "configuracion_ingresos")
        or not proyecto.configuracion_ingresos
    ):
        problemas.append("Configuración de ingresos no definida")

    # Verificar que hay datos de egresos en session_state
    if (
        "egresos_ejemplo" not in st.session_state
        or st.session_state.egresos_ejemplo.empty
    ):
        problemas.append("No hay datos de egresos configurados")

    # Verificar flujos calculados
    if not hasattr(proyecto, "flujo_efectivo") or not proyecto.flujo_efectivo:
        problemas.append("Flujos de efectivo no calculados")

    # Verificar indicadores
    if not hasattr(proyecto, "indicadores") or not proyecto.indicadores:
        problemas.append("Indicadores financieros no calculados")

    return len(problemas) == 0, problemas


def generar_codigo_proyecto() -> str:
    """
    Genera un código único para el proyecto

    Returns:
        str: Código del proyecto
    """
    from datetime import datetime
    import random

    timestamp = datetime.now().strftime("%Y%m%d")
    random_num = random.randint(1000, 9999)

    return f"SEMAVENCA-{timestamp}-{random_num}"


def mostrar_progreso_calculo(mensaje: str, progreso: int):
    """
    Muestra progreso de cálculos

    Args:
        mensaje: Mensaje a mostrar
        progreso: Porcentaje de progreso (0-100)
    """
    st.progress(progreso)
    st.text(mensaje)


def validar_rango_numerico(
    valor: float, minimo: float, maximo: float, nombre_campo: str
) -> Tuple[bool, str]:
    """
    Valida que un valor numérico esté dentro de un rango

    Args:
        valor: Valor a validar
        minimo: Valor mínimo permitido
        maximo: Valor máximo permitido
        nombre_campo: Nombre del campo para el mensaje de error

    Returns:
        tuple: (es_valido, mensaje_error)
    """
    if pd.isna(valor):
        return False, f"{nombre_campo}: El valor no puede estar vacío"

    if valor < minimo:
        return False, f"{nombre_campo}: El valor debe ser mayor o igual a {minimo}"

    if valor > maximo:
        return False, f"{nombre_campo}: El valor debe ser menor o igual a {maximo}"

    return True, ""


def crear_resumen_metricas(proyecto) -> Dict[str, any]:
    """
    Crea un resumen de todas las métricas del proyecto

    Args:
        proyecto: Instancia de ProyectoInversion

    Returns:
        dict: Resumen de métricas
    """
    if not hasattr(proyecto, "indicadores") or not proyecto.indicadores:
        return {}

    indicadores = proyecto.indicadores

    resumen = {
        "datos_basicos": {
            "inversion_inicial": getattr(proyecto, "inversion_inicial", 0),
            "meses_operativos": len(getattr(proyecto, "flujo_efectivo", [])),
            "fecha_analisis": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "indicadores_rentabilidad": {
            "tir": indicadores.get("tir", None),
            "vpn": indicadores.get("vpn", 0),
            "roi": indicadores.get("roi", 0),
            "periodo_recuperacion": indicadores.get("periodo_recuperacion", {}),
        },
        "flujos_efectivo": {
            "ingresos_totales": sum(getattr(proyecto, "ingresos_operativos", [])),
            "egresos_totales": sum(getattr(proyecto, "egresos_operativos", [])),
            "flujo_neto_total": sum(getattr(proyecto, "flujo_efectivo", [])),
            "flujo_promedio_mensual": (
                np.mean(getattr(proyecto, "flujo_efectivo", [0]))
                if getattr(proyecto, "flujo_efectivo", [])
                else 0
            ),
        },
        "analisis_riesgo": {
            "volatilidad_flujos": (
                np.std(getattr(proyecto, "flujo_efectivo", [0]))
                if getattr(proyecto, "flujo_efectivo", [])
                else 0
            ),
            "coeficiente_variacion": _calcular_coeficiente_variacion(
                getattr(proyecto, "flujo_efectivo", [])
            ),
            "meses_flujo_negativo": sum(
                1 for f in getattr(proyecto, "flujo_efectivo", []) if f < 0
            ),
        },
    }

    return resumen


def _calcular_coeficiente_variacion(flujos: List[float]) -> float:
    """
    Calcula el coeficiente de variación de los flujos
    """
    if not flujos or len(flujos) == 0:
        return 0

    media = np.mean(flujos)
    if media == 0:
        return 0

    return (np.std(flujos) / abs(media)) * 100


def exportar_dataframe_excel(df: pd.DataFrame, nombre_archivo: str) -> bytes:
    """
    Exporta DataFrame a Excel en memoria

    Args:
        df: DataFrame a exportar
        nombre_archivo: Nombre del archivo

    Returns:
        bytes: Archivo Excel en bytes
    """
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Datos", index=False)

        # Formatear el archivo
        workbook = writer.book
        worksheet = writer.sheets["Datos"]

        # Formato para números
        money_format = workbook.add_format({"num_format": "$#,##0.00"})
        percent_format = workbook.add_format({"num_format": "0.00%"})

        # Aplicar formatos si hay columnas de Monto
        if "Monto" in df.columns:
            col_idx = df.columns.get_loc("Monto")
            worksheet.set_column(col_idx, col_idx, 15, money_format)

    output.seek(0)
    return output.getvalue()


def validar_archivo_subido(archivo) -> Tuple[bool, str]:
    """
    Valida el archivo subido por el usuario

    Args:
        archivo: Archivo subido por streamlit

    Returns:
        tuple: (es_valido, mensaje)
    """
    if archivo is None:
        return False, "No se ha seleccionado ningún archivo"

    # Validar extensión
    if not archivo.name.lower().endswith((".xlsx", ".xls")):
        return False, "El archivo debe ser un Excel (.xlsx o .xls)"

    # Validar tamaño (máximo 10MB)
    if archivo.size > 10 * 1024 * 1024:
        return False, "El archivo es demasiado grande (máximo 10MB)"

    return True, "Archivo válido"


def crear_tabla_comparacion(datos_comparacion: Dict[str, Dict]) -> pd.DataFrame:
    """
    Crea tabla de comparación de escenarios

    Args:
        datos_comparacion: Datos para comparar

    Returns:
        pd.DataFrame: Tabla de comparación
    """
    if not datos_comparacion:
        return pd.DataFrame()

    # Convertir datos a DataFrame
    df_comparacion = pd.DataFrame.from_dict(datos_comparacion, orient="index")

    # Ordenar columnas si existen
    columnas_orden = ["TIR", "VPN", "ROI", "Payback"]
    columnas_existentes = [
        col for col in columnas_orden if col in df_comparacion.columns
    ]

    if columnas_existentes:
        df_comparacion = df_comparacion[columnas_existentes]

    return df_comparacion


def calcular_metricas_sensibilidad(matriz_resultados: np.ndarray) -> Dict[str, float]:
    """
    Calcula métricas del análisis de sensibilidad

    Args:
        matriz_resultados: Matriz de resultados del análisis

    Returns:
        dict: Métricas de sensibilidad
    """
    if matriz_resultados.size == 0:
        return {}

    metricas = {
        "rango_total": np.max(matriz_resultados) - np.min(matriz_resultados),
        "valor_central": (
            matriz_resultados[
                len(matriz_resultados) // 2, len(matriz_resultados[0]) // 2
            ]
            if matriz_resultados.ndim == 2
            else np.median(matriz_resultados)
        ),
        "desviacion_estandar": np.std(matriz_resultados),
        "coeficiente_variacion": (
            (np.std(matriz_resultados) / abs(np.mean(matriz_resultados)) * 100)
            if np.mean(matriz_resultados) != 0
            else 0
        ),
        "percentil_5": np.percentile(matriz_resultados, 5),
        "percentil_95": np.percentile(matriz_resultados, 95),
    }

    return metricas


def generar_alerta_validacion(
    campo: str, valor: any, es_valido: bool, mensaje: str = ""
):
    """
    Genera alertas de validación para campos específicos

    Args:
        campo: Nombre del campo
        valor: Valor del campo
        es_valido: Si el valor es válido
        mensaje: Mensaje personalizado
    """
    if es_valido:
        st.success(f"✅ {campo}: Válido")
    else:
        st.error(f"❌ {campo}: {mensaje}")


def formatear_tabla_financiera(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica formato financiero a un DataFrame

    Args:
        df: DataFrame a formatear

    Returns:
        pd.DataFrame: DataFrame formateado
    """
    df_formateado = df.copy()

    # Columnas que típicamente contienen montos
    columnas_dinero = ["Monto", "VPN", "Inversión", "Flujo", "Ingreso", "Egreso"]

    for col in df_formateado.columns:
        if any(palabra in col for palabra in columnas_dinero):
            if df_formateado[col].dtype in ["float64", "int64"]:
                df_formateado[col] = df_formateado[col].apply(
                    lambda x: f"${x:,.2f}" if pd.notna(x) else "N/A"
                )

    # Columnas de porcentaje
    columnas_porcentaje = ["TIR", "ROI", "%"]

    for col in df_formateado.columns:
        if any(palabra in col for palabra in columnas_porcentaje):
            if col not in [
                c for c in df_formateado.columns if any(p in c for p in columnas_dinero)
            ]:  # No formatear si ya es dinero
                if df_formateado[col].dtype in ["float64", "int64"]:
                    df_formateado[col] = df_formateado[col].apply(
                        lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
                    )

    return df_formateado


def validar_coherencia_flujos(
    ingresos: List[float], egresos: List[float]
) -> Tuple[bool, List[str]]:
    """
    Valida la coherencia entre ingresos y egresos

    Args:
        ingresos: Lista de ingresos
        egresos: Lista de egresos

    Returns:
        tuple: (es_coherente, lista_advertencias)
    """
    advertencias = []

    # Verificar longitud
    if len(ingresos) != len(egresos):
        advertencias.append(
            f"Diferencia en longitud: {len(ingresos)} ingresos vs {len(egresos)} egresos"
        )

    # Verificar valores negativos
    ingresos_negativos = sum(1 for i in ingresos if i < 0)
    egresos_negativos = sum(1 for e in egresos if e < 0)

    if ingresos_negativos > 0:
        advertencias.append(f"{ingresos_negativos} períodos con ingresos negativos")

    if egresos_negativos > 0:
        advertencias.append(f"{egresos_negativos} períodos con egresos negativos")

    # Verificar proporciones extremas
    if ingresos and egresos:
        ratio_promedio = (
            np.mean(ingresos) / np.mean(egresos)
            if np.mean(egresos) > 0
            else float("inf")
        )

        if ratio_promedio < 0.5:
            advertencias.append(
                "Los egresos son más del doble de los ingresos promedio"
            )
        elif ratio_promedio > 5:
            advertencias.append("Los ingresos son más de 5 veces los egresos promedio")

    return len(advertencias) == 0, advertencias


def crear_configuracion_exportacion() -> Dict[str, any]:
    """
    Crea configuración para exportación de reportes

    Returns:
        dict: Configuración de exportación
    """
    return {
        "formato_numeros": {
            "moneda": "${:,.2f}",
            "porcentaje": "{:.2%}",
            "numero": "{:,.2f}",
            "entero": "{:,}",
        },
        "colores": {
            "positivo": "#28a745",
            "negativo": "#dc3545",
            "neutro": "#6c757d",
            "principal": "#007bff",
        },
        "configuracion_excel": {
            "incluir_graficos": True,
            "incluir_tablas_dinamicas": True,
            "proteger_hojas": False,
            "formato_profesional": True,
        },
    }
