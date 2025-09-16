import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="SEMAVENCA - Evaluación de Proyectos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===================================================================
# SISTEMA DE EVALUACIÓN DE PROYECTOS DE INVERSIÓN - SEMAVENCA
# Aplicación Principal - VERSIÓN COMPLETA CON ST.PYPLOT
# Autor: MSc Jesus Salazar Rojas, Economista-Contador Público
# Fecha: sep 2025
# ===================================================================

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import sys
import os
import chardet
from pathlib import Path
import traceback

# Carpeta actual donde está main_app.py
current_dir = Path(__file__).parent

warnings.filterwarnings("ignore")

# Importar módulos personalizados con manejo de errores
try:
    from modules.financial_calculations import ProyectoInversion
    from modules.data_processing import DataProcessor
    from modules.visualizations import (
        crear_dashboard_indicadores,
        crear_analisis_flujo_efectivo,
        crear_analisis_sensibilidad_visual,
        crear_comparacion_escenarios,
        crear_grafico_rentabilidad_temporal,
        crear_resumen_ejecutivo_visual,
    )
    from modules.reports import (
        generar_excel_completo,
        generar_reporte_ejecutivo_pdf,
        crear_boton_descarga_excel,
        crear_boton_descarga_pdf,
        generar_resumen_hallazgos,
    )
    from modules.utils import (
        crear_header_empresa,
        validar_datos_entrada,
        formatear_numero,
        crear_tarjeta_metrica,
        mostrar_alerta_personalizada,
        cargar_archivo_excel,
        generar_datos_ejemplo,
        crear_egresos_ejemplo,
        calcular_estadisticas_descriptivas,
        verificar_integridad_datos,
        generar_codigo_proyecto,
        mostrar_progreso_calculo,
    )

    MODULES_LOADED = True

except ImportError as e:
    st.error(f"❌ Error importando módulos: {e}")
    st.info("🔧 Asegúrese de que todos los archivos del módulo estén presentes")
    MODULES_LOADED = False


# Cargar CSS personalizado si existe
def load_css():
    """Carga estilos CSS personalizados"""
    css_file = current_dir / "assets" / "style.css"
    if css_file.exists():
        rawdata = css_file.read_bytes()
        result = chardet.detect(rawdata)
        encoding = result["encoding"] if result["encoding"] else "utf-8"
        with open(css_file, encoding=encoding) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ No se encontró el archivo style.css")


def main():
    """Función principal de la aplicación"""

    # Verificar que los módulos se cargaron correctamente
    if not MODULES_LOADED:
        st.error("❌ Sistema no puede iniciarse. Módulos faltantes.")
        st.stop()

    # Cargar estilos
    load_css()

    # Header corporativo
    crear_header_empresa()

    # Inicialización del estado de sesión
    if "proyecto" not in st.session_state:
        st.session_state.proyecto = ProyectoInversion()

    if "data_processor" not in st.session_state:
        st.session_state.data_processor = DataProcessor()

    proyecto = st.session_state.proyecto
    data_processor = st.session_state.data_processor

    # Sidebar para navegación
    st.sidebar.title("📋 Panel de Control")

    # Estado del sistema
    with st.sidebar:
        st.markdown("---")
        es_integro, problemas = verificar_integridad_datos(proyecto)

        if es_integro:
            st.success("✅ Sistema OK")
        else:
            st.warning(f"⚠️ {len(problemas)} problemas detectados")
            with st.expander("Ver detalles"):
                for problema in problemas:
                    st.write(f"• {problema}")

    # Navegación principal
    seccion = st.sidebar.selectbox(
        "Seleccione una sección:",
        [
            "🏠 Inicio",
            "💰 Configuración Financiera",
            "📊 Análisis",
            "📈 Visualizaciones",
            "📄 Reportes",
        ],
    )

    # Routing de secciones
    if seccion == "🏠 Inicio":
        mostrar_inicio()
    elif seccion == "💰 Configuración Financiera":
        configuracion_financiera(proyecto)
    elif seccion == "📊 Análisis":
        mostrar_analisis(proyecto)
    elif seccion == "📈 Visualizaciones":
        mostrar_visualizaciones(proyecto)
    elif seccion == "📄 Reportes":
        generar_reportes(proyecto)

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.8em;'>
            <b>Desarrollado por MSc. Jesús F. Salazar Rojas</b><br>
            Economista / Contador Público<br>
            Cel +58(0414)2868869<br>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_inicio():
    """Página de inicio con información del proyecto"""

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            """
            ## 🎯 Bienvenido al Sistema de Evaluación de Proyectos de Inversión

            ### 📋 Funcionalidades Principales:
            - **Análisis Preoperativo**: Distribución de inversión y seguimiento de saldos
            - **Proyección de Ingresos**: Basado en multas y pagos voluntarios con variabilidad
            - **Gestión de Egresos**: Importación Excel y proyección temporal
            - **Indicadores Financieros**: TIR, VPN, ROI con tasas personalizadas
            - **Visualizaciones**: Gráficos interactivos y dashboards ejecutivos
            - **Reportes**: Exportación completa en Excel y PDF

            ### 📄 Proceso de Evaluación:
            1. **Configuración**: Inversión inicial y parámetros operativos
            2. **Ingresos**: Configuración de multas y porcentajes de cobro
            3. **Egresos**: Carga de archivo Excel con conceptos y montos
            4. **Análisis**: Cálculo automático de indicadores financieros
            5. **Reportes**: Descarga de resultados y análisis completo
            """
        )

        # Botón para cargar datos de ejemplo
        if st.button("🚀 Cargar Datos de Ejemplo", type="primary"):
            datos_ejemplo = generar_datos_ejemplo()
            egresos_ejemplo = crear_egresos_ejemplo()

            # Guardar en session_state
            st.session_state.datos_ejemplo = datos_ejemplo
            st.session_state.egresos_ejemplo = egresos_ejemplo

            mostrar_alerta_personalizada(
                "Datos de ejemplo cargados. Vaya a 'Configuración Financiera' para comenzar.",
                "success",
            )

    with col2:
        st.markdown("### 📊 Vista Previa del Sistema")

        # Crear métricas de ejemplo
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown(
                crear_tarjeta_metrica("TIR Ejemplo", 0.18, formato="porcentaje"),
                unsafe_allow_html=True,
            )

        with col_b:
            st.markdown(
                crear_tarjeta_metrica("VPN Ejemplo", 125000, formato="moneda"),
                unsafe_allow_html=True,
            )

        # Información técnica
        st.markdown(
            """
            ### 💡 Características Técnicas:
            - ✅ Cálculos según NIIF
            - ✅ Interface responsiva
            - ✅ Análisis de sensibilidad
            - ✅ Exportación profesional
            - ✅ Validación de datos
            """
        )


def configuracion_financiera(proyecto):
    """Sección completa de configuración financiera"""

    st.header("💰 Configuración de Datos Financieros")

    # Cargar datos de ejemplo si están disponibles
    datos_ejemplo = st.session_state.get("datos_ejemplo", {})
    egresos_ejemplo = st.session_state.get("egresos_ejemplo", pd.DataFrame())

    # Tabs para organizar la configuración
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🗗️ Inversión Inicial", "💵 Ingresos", "💸 Egresos", "📊 Proyección"]
    )

    with tab1:
        configurar_inversion_inicial(proyecto, datos_ejemplo)

    with tab2:
        configurar_ingresos(proyecto, datos_ejemplo)

    with tab3:
        configurar_egresos(proyecto, egresos_ejemplo)

    with tab4:
        generar_proyeccion_completa(proyecto)


def configurar_inversion_inicial(proyecto, datos_ejemplo):
    """Configura la inversión inicial y fase preoperativa"""

    st.subheader("🗗️ Inversión Inicial y Fase Preoperativa")

    col1, col2 = st.columns(2)

    with col1:
        inversion = st.number_input(
            "Inversión Inicial ($)",
            min_value=0.0,
            value=datos_ejemplo.get("inversion_inicial", 120000.0),
            format="%.2f",
            help="Monto total requerido para iniciar el proyecto",
        )
        proyecto.inversion_inicial = inversion

    with col2:
        meses_preop = st.number_input(
            "Meses Fase Preoperativa",
            min_value=1,
            max_value=36,
            value=datos_ejemplo.get("meses_preoperativos", 3),
            help="Período antes del inicio de operaciones",
        )
        proyecto.meses_preoperativos = meses_preop

    # Distribución mensual preoperativa
    st.markdown("### 📅 Distribución Mensual Preoperativa")

    # Opciones de distribución
    tipo_distribucion = st.selectbox(
        "Tipo de Distribución",
        ["Uniforme", "Personalizada", "Creciente", "Decreciente"],
        help="Seleccione cómo distribuir la inversión en el tiempo",
    )

    distribucion = {}

    if tipo_distribucion == "Uniforme":
        monto_mensual = inversion / meses_preop
        for mes in range(1, meses_preop + 1):
            distribucion[mes] = monto_mensual

    elif tipo_distribucion == "Personalizada":
        st.markdown("**Ingrese el monto para cada mes:**")
        cols = st.columns(min(meses_preop, 4))

        for i in range(meses_preop):
            col_idx = i % 4
            with cols[col_idx]:
                distribucion[i + 1] = st.number_input(
                    f"Mes {i+1}",
                    min_value=0.0,
                    value=inversion / meses_preop,
                    format="%.2f",
                    key=f"preop_personalizado_{i+1}",
                )

    elif tipo_distribucion == "Creciente":
        for mes in range(1, meses_preop + 1):
            factor = mes / sum(range(1, meses_preop + 1))
            distribucion[mes] = inversion * factor

    elif tipo_distribucion == "Decreciente":
        for mes in range(1, meses_preop + 1):
            factor = (meses_preop - mes + 1) / sum(range(1, meses_preop + 1))
            distribucion[mes] = inversion * factor

    proyecto.distribucion_preoperativa = distribucion

    # Validar distribución
    total_distribuido = sum(distribucion.values())
    diferencia = abs(total_distribuido - inversion)

    if diferencia > inversion * 0.01:  # Tolerancia del 1%
        st.warning(
            f"⚠️ La distribución total (${total_distribuido:,.0f}) difiere de la inversión inicial (${inversion:,.0f})"
        )

    # Mostrar tabla de distribución
    if st.button("📄 Calcular Saldos Preoperativos"):
        saldos = proyecto.calcular_saldos_preoperativos(
            inversion, meses_preop, distribucion
        )
        proyecto.saldos_preoperativos = saldos

        df_saldos = pd.DataFrame(saldos)
        st.dataframe(
            df_saldos.style.format(
                {
                    "erogacion_mes": "${:,.0f}",
                    "erogacion_acumulada": "${:,.0f}",
                    "saldo_disponible": "${:,.0f}",
                    "porcentaje_ejecutado": "{:.1f}%",
                }
            ),
            use_container_width=True,
        )


def configurar_ingresos(proyecto, datos_ejemplo):
    """Configura los parámetros de ingresos"""

    st.subheader("💵 Configuración de Ingresos Operativos")

    # Parámetros base
    col1, col2 = st.columns(2)

    with col1:
        multas_diarias = st.number_input(
            "Total Multas Diarias",
            min_value=0.0,
            value=datos_ejemplo.get("multas_diarias", 200.0),
            help="Número promedio de multas emitidas por día",
        )

        valor_multa = st.number_input(
            "Valor Multa con Descuento ($)",
            min_value=0.0,
            value=datos_ejemplo.get("valor_multa_descuento", 180.0),
            help="Valor de multa con descuento por pago voluntario",
        )

    with col2:
        pct_pago_voluntario = st.number_input(
            "% Pago Multas Voluntarias",
            min_value=0.0,
            max_value=100.0,
            value=datos_ejemplo.get("pct_pago_voluntario", 10.0),
            help="Porcentaje de multas pagadas voluntariamente",
        )

        pct_ingreso_operativo = st.number_input(
            "% Ingreso Operativo Real",
            min_value=0.0,
            max_value=100.0,
            value=datos_ejemplo.get("pct_ingreso_operativo", 60.0),
            help="Eficiencia de cobro real vs teórico",
        )

    # Cálculos intermedios
    multas_mensuales = multas_diarias * 30
    ingresos_totales = multas_mensuales * valor_multa
    pago_voluntario = ingresos_totales * (pct_pago_voluntario / 100)
    ingreso_operativo = pago_voluntario * (pct_ingreso_operativo / 100)

    # Mostrar cálculos
    st.markdown("### 📊 Cálculos de Ingresos")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Multas/Mes", f"{multas_mensuales:,.0f}")

    with col2:
        st.metric("Ingresos Teóricos", f"${ingresos_totales:,.0f}")

    with col3:
        st.metric("Pago Voluntario", f"${pago_voluntario:,.0f}")

    with col4:
        st.markdown(
            crear_tarjeta_metrica(
                "Ingreso Operativo", ingreso_operativo, formato="moneda"
            ),
            unsafe_allow_html=True,
        )

    # Guardar configuración
    proyecto.configuracion_ingresos = {
        "multas_diarias": multas_diarias,
        "valor_multa_descuento": valor_multa,
        "pct_pago_voluntario": pct_pago_voluntario,
        "pct_ingreso_operativo": pct_ingreso_operativo,
        "multas_mensuales": multas_mensuales,
        "ingresos_totales": ingresos_totales,
        "pago_voluntario": pago_voluntario,
        "ingreso_operativo_base": ingreso_operativo,
    }


def configurar_egresos(proyecto, egresos_ejemplo):
    """Configura los egresos operativos"""

    st.subheader("💸 Configuración de Egresos Operativos")

    # Opción de usar datos de ejemplo o cargar archivo
    opcion_egresos = st.radio(
        "Seleccione origen de datos:",
        ["Usar datos de ejemplo", "Cargar archivo Excel", "Ingresar manualmente"],
        help="Seleccione cómo desea ingresar los egresos operativos",
    )

    df_egresos = pd.DataFrame()

    if opcion_egresos == "Usar datos de ejemplo":
        if not egresos_ejemplo.empty:
            df_egresos = egresos_ejemplo
            st.success("✅ Usando datos de ejemplo")
            st.dataframe(df_egresos, use_container_width=True)
        else:
            df_egresos = crear_egresos_ejemplo()
            st.info("📊 Datos de ejemplo generados")
            st.dataframe(df_egresos, use_container_width=True)

    elif opcion_egresos == "Cargar archivo Excel":
        archivo_egresos = st.file_uploader(
            "Cargar archivo Excel",
            type=["xlsx", "xls"],
            help="El archivo debe contener columnas: Concepto, Monto",
        )

        if archivo_egresos:
            df_egresos, errores = cargar_archivo_excel_mejorado(archivo_egresos)

            if df_egresos is not None:
                st.success("✅ Archivo cargado exitosamente")

                if errores:
                    st.warning("⚠️ Advertencias:")
                    for error in errores:
                        st.warning(f"• {error}")

                st.dataframe(df_egresos, use_container_width=True)

                # Estadísticas del archivo
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Conceptos", len(df_egresos))
                with col2:
                    st.metric("Total Mensual", f"${df_egresos['Monto'].sum():,.0f}")
                with col3:
                    st.metric("Promedio", f"${df_egresos['Monto'].mean():,.0f}")

            else:
                st.error("❌ Error cargando archivo:")
                for error in errores:
                    st.error(f"• {error}")

    elif opcion_egresos == "Ingresar manualmente":
        st.markdown("### ✏️ Ingreso Manual de Egresos")

        # Formulario dinámico
        if "num_conceptos" not in st.session_state:
            st.session_state.num_conceptos = 5

        num_conceptos = st.number_input(
            "Número de conceptos",
            min_value=1,
            max_value=20,
            value=st.session_state.num_conceptos,
        )

        conceptos = []
        montos = []

        for i in range(num_conceptos):
            col1, col2 = st.columns(2)

            with col1:
                concepto = st.text_input(f"Concepto {i+1}", key=f"concepto_{i}")
                conceptos.append(concepto)

            with col2:
                monto = st.number_input(
                    f"Monto {i+1}", min_value=0.0, value=0.0, key=f"monto_{i}"
                )
                montos.append(monto)

        if st.button("Crear tabla de egresos"):
            # Filtrar entradas vacías
            datos_validos = [
                (c, m) for c, m in zip(conceptos, montos) if c.strip() and m > 0
            ]

            if datos_validos:
                df_egresos = pd.DataFrame(datos_validos, columns=["Concepto", "Monto"])
                st.success(f"✅ Tabla creada con {len(df_egresos)} conceptos")
                st.dataframe(df_egresos, use_container_width=True)
            else:
                st.warning("⚠️ Ingrese al menos un concepto con monto válido")

    # Guardar egresos en session_state
    if not df_egresos.empty:
        st.session_state.egresos_ejemplo = df_egresos

        # Mostrar resumen
        st.markdown("### 📊 Resumen de Egresos")
        col1, col2 = st.columns(2)

        with col1:
            # Top 5 conceptos por monto
            top_conceptos = df_egresos.nlargest(5, "Monto")
            st.markdown("**Top 5 Conceptos:**")
            for _, row in top_conceptos.iterrows():
                st.write(f"• {row['Concepto']}: ${row['Monto']:,.0f}")

        with col2:
            # Estadísticas
            total_egresos = df_egresos["Monto"].sum()
            promedio_egresos = df_egresos["Monto"].mean()

            st.metric("Total Mensual", f"${total_egresos:,.0f}")
            st.metric("Promedio por Concepto", f"${promedio_egresos:,.0f}")

            # Distribución porcentual
            df_egresos["Porcentaje"] = (df_egresos["Monto"] / total_egresos) * 100
            concepto_mayor = df_egresos.loc[df_egresos["Monto"].idxmax()]
            st.metric(
                "Mayor Concepto",
                f"{concepto_mayor['Porcentaje']:.1f}%",
                concepto_mayor["Concepto"],
            )


def cargar_archivo_excel_mejorado(archivo):
    """Versión mejorada de carga de Excel con validaciones estrictas"""
    errores = []

    try:
        # Leer el archivo
        df = pd.read_excel(archivo)

        # Validar columnas requeridas
        if "Concepto" not in df.columns or "Monto" not in df.columns:
            return None, ["El archivo debe contener las columnas 'Concepto' y 'Monto'"]

        # Limpiar datos
        df_limpio = df[["Concepto", "Monto"]].copy()

        # Procesar conceptos vacíos o NaN
        conceptos_vacios = df_limpio["Concepto"].isna() | (
            df_limpio["Concepto"].astype(str).str.strip() == ""
        )
        if conceptos_vacios.any():
            num_vacios = conceptos_vacios.sum()
            df_limpio.loc[conceptos_vacios, "Concepto"] = "Gasto por identificar"
            errores.append(
                f"{num_vacios} conceptos vacíos fueron etiquetados como 'Gasto por identificar'"
            )

        # Procesar montos
        df_limpio["Monto"] = pd.to_numeric(df_limpio["Monto"], errors="coerce")

        # Eliminar filas con montos cero, negativos o NaN
        montos_invalidos = df_limpio["Monto"].isna() | (df_limpio["Monto"] <= 0)
        if montos_invalidos.any():
            num_invalidos = montos_invalidos.sum()
            df_limpio = df_limpio[~montos_invalidos]
            errores.append(
                f"{num_invalidos} filas con montos inválidos (cero, negativos o vacíos) fueron eliminadas"
            )

        # Verificar que queden datos
        if df_limpio.empty:
            return None, ["No hay datos válidos después de la limpieza"]

        # Resetear índice
        df_limpio = df_limpio.reset_index(drop=True)

        return df_limpio, errores

    except Exception as e:
        return None, [f"Error procesando archivo: {str(e)}"]


def generar_proyeccion_completa(proyecto):
    """Genera la proyección completa del proyecto"""

    st.subheader("🚀 Proyección Completa")

    # Verificar datos previos
    if (
        not hasattr(proyecto, "configuracion_ingresos")
        or not proyecto.configuracion_ingresos
    ):
        st.warning("⚠️ Configure primero los parámetros de ingresos")
        return

    col1, col2 = st.columns(2)

    with col1:
        meses_operativos = st.number_input(
            "Meses Operativos",
            min_value=6,
            max_value=120,
            value=45,
            help="Período de operación del proyecto",
        )

        tasa_var_ingresos = st.slider(
            "Tasa Variación Ingresos (%)",
            min_value=-5.0,
            max_value=10.0,
            value=0.0,
            step=0.1,
            help="Tasa de crecimiento/decrecimiento mensual de ingresos",
        )

    with col2:
        tasa_var_egresos = st.slider(
            "Tasa Variación Egresos (%)",
            min_value=-5.0,
            max_value=10.0,
            value=0.0,
            step=0.1,
            help="Tasa de crecimiento/decrecimiento mensual de egresos",
        )

    # NUEVA OPCIÓN: Tipo de flujos para TIR
    st.markdown("### ⚙️ Configuración de Cálculos")

    col1, col2 = st.columns(2)

    with col1:
        tipo_flujos = st.radio(
            "Tipo de flujos para TIR:",
            ["Flujos constantes (Excel estándar)", "Flujos acumulados"],
            help="Seleccione si sus flujos son valores por período o acumulados",
        )

    with col2:
        metodo_tir = st.selectbox(
            "Método de cálculo TIR:",
            ["Excel compatible (Newton-Raphson)", "Scipy optimize"],
            help="Método para calcular TIR",
        )

    # Configuración de tasas de descuento
    st.markdown("### 📊 Configuración de Tasas de Descuento")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        tasa_libre_riesgo = (
            st.number_input(
                "Tasa Libre de Riesgo (%)",
                min_value=0.0,
                max_value=15.0,
                value=7.0,
                step=0.1,
            )
            / 100
        )

    with col2:
        tasa_riesgo_pais = (
            st.number_input(
                "Tasa Riesgo País (%)",
                min_value=0.0,
                max_value=15.0,
                value=3.0,
                step=0.1,
            )
            / 100
        )

    with col3:
        tasa_riesgo_proyecto = (
            st.number_input(
                "Tasa Riesgo Proyecto (%)",
                min_value=0.0,
                max_value=20.0,
                value=3.0,
                step=0.1,
            )
            / 100
        )

    with col4:
        tasa_descuento_total = (
            tasa_libre_riesgo + tasa_riesgo_pais + tasa_riesgo_proyecto
        )
        st.metric("Tasa Descuento Total", f"{tasa_descuento_total:.2%}")

    # Botón para generar proyección completa
    if st.button("🚀 Generar Proyección Completa", type="primary"):

        # Verificar egresos
        if "egresos_ejemplo" not in st.session_state:
            st.error(
                "❌ No hay datos de egresos. Configure egresos en la pestaña anterior"
            )
            return

        # Crear barra de progreso
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Paso 1: Obtener egresos
                status_text.text("📄 Obteniendo datos de egresos...")
                progress_bar.progress(10)

                df_egresos = st.session_state.egresos_ejemplo
                if df_egresos.empty:
                    st.error("❌ No hay datos de egresos válidos")
                    return

                egresos_base = dict(zip(df_egresos["Concepto"], df_egresos["Monto"]))

                # Paso 2: Calcular ingresos
                status_text.text("💰 Calculando proyección de ingresos...")
                progress_bar.progress(30)

                config_ingresos = proyecto.configuracion_ingresos.copy()
                config_ingresos["tasa_variacion"] = tasa_var_ingresos

                ingresos, ingreso_base, detalle = proyecto.calcular_ingresos_operativos(
                    config_ingresos, meses_operativos
                )

                # Verificar que los ingresos se calcularon correctamente
                if not ingresos or len(ingresos) != meses_operativos:
                    st.error("❌ Error calculando ingresos operativos")
                    return
                # Paso 3: Calcular egresos
                status_text.text("💸 Calculando proyección de egresos...")
                progress_bar.progress(50)
                try:
                    egresos, total_base, detalle_egresos = (
                        proyecto.calcular_egresos_operativos(
                            egresos_base, meses_operativos, tasa_var_egresos
                        )
                    )
                except Exception as e:
                    st.error(f"❌ Error al calcular egresos operativos: {e}")
                    return

                # Verificar que los egresos se calcularon correctamente
                if not egresos or len(egresos) != meses_operativos:
                    st.error("❌ Error calculando egresos operativos")
                return

                # Paso 4: Calcular flujo de efectivo
                status_text.text("📊 Calculando flujo de efectivo...")
                progress_bar.progress(70)

                # Verificar que ambas listas tengan la misma longitud
                if len(ingresos) != len(egresos):
                    st.error(
                        f"❌ Error: Ingresos ({len(ingresos)}) y egresos ({len(egresos)}) tienen diferente longitud"
                    )
                return

                flujo_efectivo = []
                for i, (ing, egr) in enumerate(zip(ingresos, egresos)):
                    flujo_mes = ing - egr
                    flujo_efectivo.append(flujo_mes)

                # Paso 5: Calcular indicadores financieros
                status_text.text("🎯 Calculando indicadores financieros...")
                progress_bar.progress(85)

                # Verificar que hay inversión inicial
                if proyecto.inversion_inicial <= 0:
                    st.error("❌ Error: La inversión inicial debe ser mayor a cero")
                return
                # aqui original

                st.error("❌ Error en los cálculos:")
                st.code(f"Tipo de error: {type(e).__name__}\nMensaje: {str(e)}")

                # Calcular TIR
                try:
                    tir = proyecto.calcular_tir(
                        flujo_efectivo, proyecto.inversion_inicial
                    )
                except Exception as e:
                    st.warning(f"⚠️ No se pudo calcular TIR: {e}")
                    tir = None

                # Calcular VPN
                try:
                    vpn = proyecto.calcular_vpn(
                        flujo_efectivo, proyecto.inversion_inicial, tasa_descuento_total
                    )
                except Exception as e:
                    st.error(f"❌ Error calculando VPN: {e}")
                    return

                # Calcular ROI
                try:
                    roi = proyecto.calcular_roi(
                        flujo_efectivo, proyecto.inversion_inicial
                    )
                except Exception as e:
                    st.error(f"❌ Error calculando ROI: {e}")
                    return

                # Calcular período de recuperación
                try:
                    periodo_recup = proyecto.calcular_periodo_recuperacion(
                        flujo_efectivo, proyecto.inversion_inicial
                    )
                except Exception as e:
                    st.warning(f"⚠️ Error calculando período de recuperación: {e}")
                    periodo_recup = {"recuperado": False, "meses": 0}

                # Paso 6: Guardar resultados
                status_text.text("💾 Guardando resultados...")
                progress_bar.progress(95)

                proyecto.ingresos_operativos = ingresos
                proyecto.egresos_operativos = egresos
                proyecto.flujo_efectivo = flujo_efectivo
                proyecto.indicadores = {
                    "tir": tir,
                    "vpn": vpn,
                    "roi": roi,
                    "periodo_recuperacion": periodo_recup,
                    "tasa_descuento": tasa_descuento_total,
                }

                # Actualizar configuraciones
                proyecto.configuracion_ingresos.update(
                    {
                        "meses_operativos": meses_operativos,
                        "tasa_variacion": tasa_var_ingresos,
                        "proyeccion": ingresos,
                    }
                )

                proyecto.configuracion_egresos = {
                    "egresos_base": egresos_base,
                    "total_base": total_base,
                    "tasa_variacion": tasa_var_egresos,
                    "proyeccion": egresos,
                    "detalle_mensual": detalle_egresos,
                }

                # Completado
                progress_bar.progress(100)
                status_text.text("✅ ¡Proyección completada exitosamente!")

                # Limpiar la barra de progreso después de 2 segundos
                import time

                time.sleep(1)
                progress_container.empty()

                st.success("🎉 ¡Proyección generada exitosamente!")

                # Mostrar resultados inmediatos
                st.markdown("### 📊 Resultados Principales")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if tir is not None:
                        color_tir = "normal" if tir > 0.15 else "inverse"
                        st.metric(
                            "TIR",
                            f"{tir:.2%}",
                            delta="vs 15% objetivo",
                            delta_color=color_tir,
                        )
                    else:
                        st.metric("TIR", "No calculable")

                with col2:
                    st.metric(
                        "VPN",
                        f"${vpn:,.0f}",
                        delta="Positivo" if vpn > 0 else "Negativo",
                        delta_color="normal" if vpn > 0 else "inverse",
                    )

                with col3:
                    st.metric("ROI", f"{roi:.1f}%")

                with col4:
                    if periodo_recup.get("recuperado", False):
                        st.metric("Recuperación", f"{periodo_recup['meses']:.1f} meses")
                    else:
                        st.metric("Recuperación", "No se recupera")

                    # Mostrar resumen de flujos
                    st.markdown("### 📈 Resumen de Flujos")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Ingreso Promedio Mensual",
                            f"${np.mean(ingresos):,.0f}",
                            f"±{np.std(ingresos)/np.mean(ingresos)*100:.1f}%",
                        )

                    with col2:
                        st.metric(
                            "Egreso Promedio Mensual",
                            f"${np.mean(egresos):,.0f}",
                            f"±{np.std(egresos)/np.mean(egresos)*100:.1f}%",
                        )

                    with col3:
                        flujo_promedio = np.mean(flujo_efectivo)
                        st.metric(
                            "Flujo Neto Promedio",
                            f"${flujo_promedio:,.0f}",
                            "Positivo" if flujo_promedio > 0 else "Negativo",
                        )

                # Mostrar traceback solo en modo debug
                with st.expander("🔧 Información técnica para debugging"):
                    st.code(traceback.format_exc())

                # Sugerencias de solución
                st.info("💡 **Posibles soluciones:**")
                st.markdown(
                    """
                    - Verifique que NumPy esté instalado: `pip install numpy`
                    - Asegúrese de que los datos de ingresos estén configurados
                    - Revise que los datos de egresos sean válidos
                    - Verifique que la inversión inicial sea mayor a cero
                    """
                )
            except Exception as e:
                st.error("❌ Error en los cálculos:")
                st.code(f"Tipo de error: {type(e).__name__}\nMensaje: {str(e)}")


if __name__ == "__main__":
    main()
