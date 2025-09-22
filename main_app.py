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
import math

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
        crear_grafico_circular_interactivo,
        crear_grafico_barras_comparativo,
        crear_grafico_lineas_tendencia,
        crear_grafico_area_acumulado,
        mostrar_visualizaciones,
        mostrar_analisis,
        actualizar_grafico_circular_drilldown,
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
        crear_costos_preoperativos_ejemplo,  # NUEVA FUNCIÓN
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
            max_value=6,
            value=datos_ejemplo.get("meses_preoperativos", 3),
            help="Período antes del inicio de operaciones",
        )
        proyecto.meses_preoperativos = meses_preop

    # NUEVA SECCIÓN: COSTOS PREOPERATIVOS
    st.markdown("### 💸 Costos Preoperativos")

    # Opción para costos preoperativos (igual que egresos)
    opcion_costos_preop = st.radio(
        "Seleccione origen de costos preoperativos:",
        [
            "Usar datos de ejemplo",
            "Cargar archivo Excel",
            "Ingresar manualmente",
            "Sin costos preoperativos",
        ],
        help="Seleccione cómo desea ingresar los costos preoperativos",
        key="radio_costos_preop",
    )

    df_costos_preop = pd.DataFrame()

    if opcion_costos_preop == "Usar datos de ejemplo":
        df_costos_preop = crear_costos_preoperativos_ejemplo()
        st.success("✅ Usando datos de ejemplo para costos preoperativos")
        st.dataframe(df_costos_preop, use_container_width=True)

    elif opcion_costos_preop == "Cargar archivo Excel":
        archivo_costos_preop = st.file_uploader(
            "Cargar archivo Excel con costos preoperativos",
            type=["xlsx", "xls"],
            help="El archivo debe contener columnas: Concepto, Monto",
            key="upload_costos_preop",
        )

        if archivo_costos_preop:
            df_costos_preop, errores = cargar_archivo_excel_mejorado(
                archivo_costos_preop
            )

            if df_costos_preop is not None:
                st.success("✅ Archivo cargado exitosamente")

                if errores:
                    st.warning("⚠️ Advertencias:")
                    for error in errores:
                        st.warning(f"• {error}")

                st.dataframe(df_costos_preop, use_container_width=True)

                # Estadísticas del archivo
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Conceptos", len(df_costos_preop))
                with col2:
                    st.metric(
                        "Total Mensual", f"${df_costos_preop['Monto'].sum():,.0f}"
                    )
                with col3:
                    st.metric("Promedio", f"${df_costos_preop['Monto'].mean():,.0f}")

    elif opcion_costos_preop == "Ingresar manualmente":
        st.markdown("#### ✏️ Ingreso Manual de Costos Preoperativos")

        if "num_conceptos_preop" not in st.session_state:
            st.session_state.num_conceptos_preop = 3

        num_conceptos_preop = st.number_input(
            "Número de conceptos preoperativos",
            min_value=1,
            max_value=15,
            value=st.session_state.num_conceptos_preop,
            key="num_conceptos_preop_input",
        )

        conceptos_preop = []
        montos_preop = []

        for i in range(num_conceptos_preop):
            col1, col2 = st.columns(2)

            with col1:
                concepto = st.text_input(
                    f"Concepto Preop {i+1}", key=f"concepto_preop_{i}"
                )
                conceptos_preop.append(concepto)

            with col2:
                monto = st.number_input(
                    f"Monto Preop {i+1}",
                    min_value=0.0,
                    value=0.0,
                    key=f"monto_preop_{i}",
                )
                montos_preop.append(monto)

        if st.button("Crear tabla de costos preoperativos"):
            # Filtrar entradas vacías
            datos_validos_preop = [
                (c, m)
                for c, m in zip(conceptos_preop, montos_preop)
                if c.strip() and m > 0
            ]

            if datos_validos_preop:
                df_costos_preop = pd.DataFrame(
                    datos_validos_preop, columns=["Concepto", "Monto"]
                )
                st.success(f"✅ Tabla creada con {len(df_costos_preop)} conceptos")
                st.dataframe(df_costos_preop, use_container_width=True)

    # Guardar costos preoperativos en session_state
    if not df_costos_preop.empty:
        st.session_state.costos_preoperativos = df_costos_preop
        proyecto.costos_preoperativos = dict(
            zip(df_costos_preop["Concepto"], df_costos_preop["Monto"])
        )

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

    # Mostrar tabla de distribución CON COSTOS PREOPERATIVOS
    if st.button("📄 Calcular Saldos Preoperativos"):
        # Obtener costos preoperativos
        costos_preop_dict = getattr(proyecto, "costos_preoperativos", {})

        saldos, saldo_final = proyecto.calcular_saldos_preoperativos_con_costos(
            inversion, meses_preop, distribucion, costos_preop_dict
        )
        proyecto.saldos_preoperativos = saldos

        df_saldos = pd.DataFrame(saldos)

        st.dataframe(
            df_saldos.style.format(
                {
                    "inversion_inicial_mes": "${:,.0f}",
                    "costos_operativos_mes": "${:,.0f}",
                    "disponible_neto_mes": "${:,.0f}",
                    "saldo_final_acumulado": "${:,.0f}",
                    "porcentaje_amortizado": "{:.1f}%",
                }
            ),
            use_container_width=True,
        )

        # Mostrar excedente/déficit final
        saldo_final = saldos[-1]["saldo_final_acumulado"] if saldos else 0
        if saldo_final > 0:
            st.success(
                f"💰 Excedente preoperativo: ${saldo_final:,.2f} (pasa a fase operativa)"
            )
        elif saldo_final < 0:
            st.error(
                f"⚠️ Déficit preoperativo: ${abs(saldo_final):,.2f} (se requiere financiamiento adicional)"
            )
        else:
            st.info("💼 Inversión preoperativa ejecutada exactamente")

        # Guardar saldo final para la fase operativa
        proyecto.saldo_preoperativo_final = saldo_final


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

        # Información sobre normalización
        if tipo_flujos == "Flujos acumulados":
            st.info(
                """
                **Normalización Automática:**
                - Los saldos acumulados se convertirán a flujos por período
                - Esto permite calcular la TIR correctamente según metodología Excel
                """
            )

    with col2:
        metodo_tir = st.selectbox(
            "Método de cálculo TIR:",
            ["Excel compatible (Newton-Raphson)", "Scipy optimize"],
            help="Método para calcular TIR",
        )

        # Explicación de la TIR
        st.info(
            """
            **Sobre la TIR mostrada:**
            - Se calcula por período (mensual) como Excel IRR
            - Se anualiza para visualización: (1+r_mes)¹² - 1
            - Usa Newton-Raphson: 20 iteraciones, tolerancia 0.00001%
            """
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

    # SE INCLUYE -------------------------------------------------------------------

    # NUEVA SECCIÓN: Configuración de Proyección
    st.markdown("### ⚙️ Configuración de Proyección")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        tipo_proyeccion_ingresos = st.selectbox(
            "Tipo Proyección Ingresos:",
            ["Constante", "Lineal", "Exponencial", "Estacional"],
            help="Tipo de proyección para ingresos"
        )
        
        # Solo mostrar tasa si no es constante
        if tipo_proyeccion_ingresos != "Constante":
            tasa_var_ingresos = st.slider(
                "Tasa Variación Ingresos (%)",
                min_value=-5.0,
                max_value=10.0,
                value=2.0,
                step=0.1,
                help="Tasa de crecimiento/decrecimiento mensual de ingresos"
            )
        else:
            tasa_var_ingresos = 0.0
            st.info("Ingresos constantes: 0% variación")
    
    with col2:
        tipo_proyeccion_egresos = st.selectbox(
            "Tipo Proyección Egresos:",
            ["Constante", "Lineal", "Exponencial", "Estacional"],
            help="Tipo de proyección para egresos"
        )
        
        # Solo mostrar tasa si no es constante
        if tipo_proyeccion_egresos != "Constante":
            tasa_var_egresos = st.slider(
                "Tasa Variación Egresos (%)",
                min_value=-5.0,
                max_value=10.0,
                value=1.5,
                step=0.1,
                help="Tasa de crecimiento/decrecimiento mensual de egresos"
            )
        else:
            tasa_var_egresos = 0.0
            st.info("Egresos constantes: 0% variación")
    
    with col3:
        # Opciones avanzadas
        incluir_estacionalidad = st.checkbox(
            "Incluir Estacionalidad",
            help="Agregar variación estacional a las proyecciones"
        )
        
        if incluir_estacionalidad:
            amplitud_estacional = st.slider(
                "Amplitud Estacional (%)",
                min_value=5,
                max_value=30,
                value=15,
                help="Variación estacional máxima"
            ) / 100
    
    # Mostrar vista previa de proyección
    if st.button("👁️ Vista Previa de Proyección"):
        # Generar proyección de muestra (6 meses)
        config_ingresos = proyecto.configuracion_ingresos.copy()
        config_ingresos['tasa_variacion'] = tasa_var_ingresos
        
        # Usar función corregida
        ingresos_muestra, _, _ = proyecto.calcular_ingresos_operativos(config_ingresos, 6)
        
        st.markdown("**Vista Previa - Primeros 6 Meses:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Mes 1-2:**")
            st.write(f"${ingresos_muestra[0]:,.0f} → ${ingresos_muestra[1]:,.0f}")
        
        with col2:
            st.markdown("**Mes 3-4:**")
            st.write(f"${ingresos_muestra[2]:,.0f} → ${ingresos_muestra[3]:,.0f}")
        
        with col3:
            st.markdown("**Mes 5-6:**")
            st.write(f"${ingresos_muestra[4]:,.0f} → ${ingresos_muestra[5]:,.0f}")
        
        # Verificar si es realmente constante cuando debería serlo
        if tasa_var_ingresos == 0:
            if len(set(ingresos_muestra)) == 1:
                st.success("✅ Proyección constante verificada")
            else:
                st.error("❌ Error: Proyección debería ser constante")
    # FIN SE INCLUYE --------------------------------------------------------------


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

                egresos, total_base, detalle_egresos = (
                    proyecto.calcular_egresos_operativos(
                        egresos_base, meses_operativos, tasa_var_egresos
                    )
                )

                # Verificar que los egresos se calcularon correctamente
                if not egresos or len(egresos) != meses_operativos:
                    st.error("❌ Error calculando egresos operativos")
                    return

                # Paso 4: Calcular flujo de efectivo CON INTEGRACIÓN PREOPERATIVA
                status_text.text("📊 Calculando flujo de efectivo completo...")
                progress_bar.progress(70)

                # Verificar que ambas listas tengan la misma longitud
                if len(ingresos) != len(egresos):
                    st.error(
                        f"❌ Error: Ingresos ({len(ingresos)}) y egresos ({len(egresos)}) tienen diferente longitud"
                    )
                    return

                # CALCULAR flujo de efectivo completo (operativo + saldo preoperativo)
                flujo_efectivo = proyecto.calcular_flujo_efectivo_completo(
                    ingresos, egresos
                )

                # Verificar que el flujo se calculó correctamente
                if not flujo_efectivo or len(flujo_efectivo) != len(ingresos):
                    st.error("❌ Error calculando flujo de efectivo completo")
                    return

                # Mostrar información del saldo preoperativo si existe
                if (
                    hasattr(proyecto, "saldo_preoperativo_final")
                    and proyecto.saldo_preoperativo_final != 0
                ):
                    saldo = proyecto.saldo_preoperativo_final
                    if saldo > 0:
                        st.info(
                            f"💰 Excedente preoperativo de ${saldo:,.2f} añadido al primer mes operativo"
                        )
                    else:
                        st.warning(
                            f"⚠️ Déficit preoperativo de ${abs(saldo):,.2f} restado del primer mes operativo"
                        )

                # Paso 5: Calcular indicadores financieros
                status_text.text("🎯 Calculando indicadores financieros...")
                progress_bar.progress(85)

                # Verificar que hay inversión inicial
                if proyecto.inversion_inicial <= 0:
                    st.error("❌ Error: La inversión inicial debe ser mayor a cero")
                    return

                # Configurar parámetros de TIR según tipo seleccionado
                params_tir = {}
                if tipo_flujos == "Flujos acumulados":
                    params_tir["input_tipo"] = "acumulado"
                else:
                    params_tir["input_tipo"] = "periodo"

                if metodo_tir == "Excel compatible (Newton-Raphson)":
                    params_tir["excel_compatible"] = True
                else:
                    params_tir["excel_compatible"] = False

                # Calcular TIR
                try:
                    tir = proyecto.calcular_tir(
                        flujo_efectivo, proyecto.inversion_inicial, **params_tir
                    )
                except Exception as e:
                    st.warning(f"⚠️ No se pudo calcular TIR: {e}")
                    tir = None

                # Calcular VPN (método Excel)
                try:
                    vpn = proyecto.calcular_vpn(
                        flujo_efectivo, proyecto.inversion_inicial, tasa_descuento_total
                    )
                except Exception as e:
                    st.error(f"❌ Error calculando VPN: {e}")
                    return

                # Calcular ROI (método Excel)
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

            except Exception as e:
                # Error handling detallado
                progress_bar.progress(0)
                status_text.text("❌ Error en el proceso")

                st.error("❌ Error en los cálculos:")
                st.code(f"Tipo de error: {type(e).__name__}\nMensaje: {str(e)}")

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


# FUNCIONES FALTANTES AÑADIDAS

#ANADIDA------------------------------------------------------------
def validar_coherencia_proyeccion(self, tipo_proyeccion, tasa_variacion, valores_proyectados):
    """
    Valida que la proyección sea coherente con los parámetros
    """
    if tipo_proyeccion.lower() == "constante":
        # Todos los valores deben ser iguales
        if len(set(round(x, 2) for x in valores_proyectados)) != 1:
            return False, f"Proyección constante inconsistente: {valores_proyectados[:3]}"
    
    elif tipo_proyeccion.lower() == "lineal" and tasa_variacion == 0:
        # Sin tasa de variación debe ser constante
        if len(set(round(x, 2) for x in valores_proyectados)) != 1:
            return False, f"Proyección sin variación inconsistente: {valores_proyectados[:3]}"
    
    elif tipo_proyeccion.lower() == "lineal" and tasa_variacion > 0:
        # Debe ser creciente
        for i in range(1, min(5, len(valores_proyectados))):
            if valores_proyectados[i] <= valores_proyectados[i-1]:
                return False, f"Proyección creciente inconsistente en mes {i+1}"
    
    elif tipo_proyeccion.lower() == "lineal" and tasa_variacion < 0:
        # Debe ser decreciente
        for i in range(1, min(5, len(valores_proyectados))):
            if valores_proyectados[i] >= valores_proyectados[i-1]:
                return False, f"Proyección decreciente inconsistente en mes {i+1}"
    
    return True, "Proyección coherente"
# FIN AÑADIDA------------------------------------------------------------

def generar_proyeccion_avanzada(self, valor_base, meses, tipo_proyeccion, parametros=None):
    """
    Genera proyecciones avanzadas según tipo especificado
    
    Args:
        valor_base: Valor inicial
        meses: Número de meses
        tipo_proyeccion: 'constante', 'lineal', 'exponencial', 'estacional', 'custom'
        parametros: Parámetros específicos del tipo
    """
    if parametros is None:
        parametros = {}
    
    proyeccion = []
    
    if tipo_proyeccion == 'constante':
        # Proyección constante (sin variación)
        for mes in range(meses):
            proyeccion.append(valor_base)
    
    elif tipo_proyeccion == 'lineal':
        # Proyección con crecimiento/decrecimiento lineal
        tasa_mensual = parametros.get('tasa_mensual', 0) / 100
        
        for mes in range(meses):
            factor = (1 + tasa_mensual) ** mes
            proyeccion.append(valor_base * factor)
    
    elif tipo_proyeccion == 'exponencial':
        # Proyección exponencial con límite
        tasa_inicial = parametros.get('tasa_inicial', 2) / 100
        factor_decaimiento = parametros.get('decaimiento', 0.95)
        
        for mes in range(meses):
            tasa_efectiva = tasa_inicial * (factor_decaimiento ** mes)
            factor = (1 + tasa_efectiva) ** mes
            proyeccion.append(valor_base * factor)
    
    elif tipo_proyeccion == 'estacional':
        # Proyección con patrón estacional
        amplitud = parametros.get('amplitud', 0.2)  # ±20% variación
        periodo = parametros.get('periodo', 12)  # Ciclo anual
        
        for mes in range(meses):
            ciclo = math.sin(2 * math.pi * mes / periodo)
            factor_estacional = 1 + (amplitud * ciclo)
            
            # Aplicar también crecimiento base si existe
            tasa_base = parametros.get('tasa_base', 0) / 100
            factor_crecimiento = (1 + tasa_base) ** mes
            
            valor_mes = valor_base * factor_crecimiento * factor_estacional
            proyeccion.append(valor_mes)
    
    elif tipo_proyeccion == 'custom':
        # Proyección personalizada con factores específicos
        factores = parametros.get('factores_mensuales', [1.0] * meses)
        
        for mes in range(min(meses, len(factores))):
            proyeccion.append(valor_base * factores[mes])
        
        # Rellenar con último factor si faltan meses
        if len(factores) < meses:
            ultimo_factor = factores[-1] if factores else 1.0
            for mes in range(len(factores), meses):
                proyeccion.append(valor_base * ultimo_factor)
    
    return [round(x, 2) for x in proyeccion]


def mostrar_analisis(proyecto):
    """Muestra análisis financiero completo"""

    st.header("📊 Análisis Financiero Detallado")

    # Verificar integridad de datos
    es_integro, problemas = verificar_integridad_datos(proyecto)

    if not es_integro:
        st.error("❌ Problemas encontrados en los datos:")
        for problema in problemas:
            st.error(f"• {problema}")
        st.info("👆 Por favor, complete la configuración en la sección anterior.")
        return

    # Tabs para organizar el análisis
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 Indicadores", "🎯 Sensibilidad", "📊 Escenarios", "🔍 Detalle"]
    )

    with tab1:
        mostrar_indicadores_principales(proyecto)

    with tab2:
        mostrar_analisis_sensibilidad(proyecto)

    with tab3:
        mostrar_analisis_escenarios(proyecto)

    with tab4:
        mostrar_analisis_detallado(proyecto)


def mostrar_indicadores_principales(proyecto):
    """Muestra los indicadores financieros principales"""

    st.subheader("📈 Indicadores Financieros Principales")

    if not hasattr(proyecto, "indicadores") or not proyecto.indicadores:
        st.warning("⚠️ No hay indicadores calculados")
        return

    indicadores = proyecto.indicadores

    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        tir = indicadores.get("tir", 0)
        if tir is not None:
            st.metric(
                "TIR",
                f"{tir:.2%}",
                delta=(
                    "Excelente" if tir > 0.20 else "Bueno" if tir > 0.15 else "Revisar"
                ),
            )
        else:
            st.metric("TIR", "No calculable")

    with col2:
        vpn = indicadores.get("vpn", 0)
        st.metric("VPN", f"${vpn:,.0f}", delta="Positivo" if vpn > 0 else "Negativo")

    with col3:
        roi = indicadores.get("roi", 0)
        st.metric("ROI", f"{roi:.1f}%")

    with col4:
        periodo = indicadores.get("periodo_recuperacion", {})
        if periodo.get("recuperado", False):
            st.metric("Recuperación", f"{periodo['meses']:.1f} meses")
        else:
            st.metric("Recuperación", "No se recupera")

    # Análisis de viabilidad
    st.markdown("### 🎯 Análisis de Viabilidad")

    if tir and tir > 0.15 and vpn > 0:
        st.success("✅ **PROYECTO VIABLE**: Cumple criterios de rentabilidad")
    elif tir and tir > 0.10 or vpn > 0:
        st.warning("⚠️ **PROYECTO MARGINAL**: Requiere análisis adicional")
    else:
        st.error("❌ **PROYECTO NO VIABLE**: No cumple criterios mínimos")


def mostrar_analisis_sensibilidad(proyecto):
    """Muestra análisis de sensibilidad"""

    st.subheader("🎯 Análisis de Sensibilidad")

    # Configurar variaciones
    col1, col2 = st.columns(2)

    with col1:
        var_ing = st.multiselect(
            "Variaciones en Ingresos (%)",
            [-30, -20, -10, -5, 0, 5, 10, 20, 30],
            default=[-20, -10, 0, 10, 20],
        )

    with col2:
        var_egr = st.multiselect(
            "Variaciones en Egresos (%)",
            [-20, -15, -10, -5, 0, 5, 10, 15, 20],
            default=[-15, -10, 0, 10, 15],
        )

    if st.button("📊 Ejecutar Análisis de Sensibilidad"):
        if var_ing and var_egr:
            with st.spinner("Calculando sensibilidad..."):
                resultados = proyecto.analisis_sensibilidad(var_ing, var_egr, 0.13)

                if resultados:
                    # Mostrar matriz de resultados
                    st.markdown("#### Matriz TIR (%)")
                    matriz_tir = np.array(resultados["tir_matriz"]) * 100
                    df_tir = pd.DataFrame(
                        matriz_tir,
                        index=[f"{e:+}%" for e in var_egr],
                        columns=[f"{i:+}%" for i in var_ing],
                    )
                    st.dataframe(df_tir.style.format("{:.2f}%"))

                    st.markdown("#### Matriz VPN ($)")
                    matriz_vpn = np.array(resultados["vpn_matriz"])
                    df_vpn = pd.DataFrame(
                        matriz_vpn,
                        index=[f"{e:+}%" for e in var_egr],
                        columns=[f"{i:+}%" for i in var_ing],
                    )
                    st.dataframe(df_vpn.style.format("${:,.0f}"))
        else:
            st.warning("⚠️ Seleccione al menos una variación para cada parámetro")


def mostrar_analisis_escenarios(proyecto):
    """Muestra análisis de escenarios configurables"""
    
    st.subheader("📊 Análisis de Escenarios")
    
    if not hasattr(proyecto, "indicadores"):
        st.warning("⚠️ No hay datos para análisis de escenarios")
        return
    
    # NUEVA SECCIÓN: Configuración de Escenarios
    st.markdown("### ⚙️ Configurar Escenarios")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Escenario Pesimista:**")
        pesimista_ing = st.slider("Ingresos Pesimista (%)", -50, 0, -20, key="pesimista_ing")
        pesimista_egr = st.slider("Egresos Pesimista (%)", 0, 50, 20, key="pesimista_egr")
    
    with col2:
        st.markdown("**Escenario Optimista:**")
        optimista_ing = st.slider("Ingresos Optimista (%)", 0, 50, 20, key="optimista_ing")
        optimista_egr = st.slider("Egresos Optimista (%)", -50, 0, -10, key="optimista_egr")
    
    # Definir escenarios con parámetros del usuario
    escenarios = {
        "Pesimista": {"ing_factor": 1 + pesimista_ing/100, "egr_factor": 1 + pesimista_egr/100},
        "Base": {"ing_factor": 1.0, "egr_factor": 1.0},
        "Optimista": {"ing_factor": 1 + optimista_ing/100, "egr_factor": 1 + optimista_egr/100},
    }
    
    # Botón para recalcular
    if st.button("🔄 Recalcular Escenarios"):
        resultados_escenarios = []
        
        for nombre, factores in escenarios.items():
            # CALCULAR REAL (no aproximación)
            if hasattr(proyecto, 'ingresos_operativos') and hasattr(proyecto, 'egresos_operativos'):
                ingresos_ajustados = [ing * factores["ing_factor"] for ing in proyecto.ingresos_operativos]
                egresos_ajustados = [egr * factores["egr_factor"] for egr in proyecto.egresos_operativos]
                flujos_ajustados = [ing - egr for ing, egr in zip(ingresos_ajustados, egresos_ajustados)]
                
                # Calcular indicadores reales
                tir_escenario = proyecto.calcular_tir(flujos_ajustados, proyecto.inversion_inicial)
                vpn_escenario = proyecto.calcular_vpn(flujos_ajustados, proyecto.inversion_inicial, 0.13)
                roi_escenario = proyecto.calcular_roi(flujos_ajustados, proyecto.inversion_inicial)
                
                resultados_escenarios.append({
                    "Escenario": nombre,
                    "Parámetros": f"Ing:{factores['ing_factor']-1:+.0%}, Egr:{factores['egr_factor']-1:+.0%}",
                    "TIR": f"{tir_escenario:.2%}" if tir_escenario else "No calc.",
                    "VPN": f"${vpn_escenario:,.0f}",
                    "ROI": f"{roi_escenario:.1f}%"
                })
        
        # Mostrar tabla de escenarios
        df_escenarios = pd.DataFrame(resultados_escenarios)
        st.dataframe(df_escenarios, use_container_width=True)
        
        # Guardar para gráficos
        st.session_state.escenarios_calculados = resultados_escenarios


def mostrar_analisis_detallado(proyecto):
    """Muestra análisis detallado del proyecto"""

    st.subheader("🔍 Análisis Detallado")

    if not hasattr(proyecto, "flujo_efectivo") or not proyecto.flujo_efectivo:
        st.warning("⚠️ No hay flujo de efectivo para análisis detallado")
        return

    # Estadísticas del flujo de efectivo
    flujos = np.array(proyecto.flujo_efectivo)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📈 Flujo de Efectivo**")
        st.metric("Promedio Mensual", f"${np.mean(flujos):,.0f}")
        st.metric("Desviación Estándar", f"${np.std(flujos):,.0f}")
        st.metric("Flujo Mínimo", f"${np.min(flujos):,.0f}")

    with col2:
        st.markdown("**💰 Análisis Acumulado**")
        flujo_acum = np.cumsum([-proyecto.inversion_inicial] + proyecto.flujo_efectivo)
        st.metric("Flujo Final", f"${flujo_acum[-1]:,.0f}")
        st.metric("Punto Máximo", f"${np.max(flujo_acum):,.0f}")
        st.metric("Punto Mínimo", f"${np.min(flujo_acum):,.0f}")

    with col3:
        st.markdown("**📊 Métricas de Riesgo**")
        coef_var = (
            (np.std(flujos) / np.mean(flujos) * 100) if np.mean(flujos) != 0 else 0
        )
        st.metric("Coef. Variación", f"{coef_var:.1f}%")

        flujos_negativos = sum(1 for f in flujos if f < 0)
        st.metric("Meses Negativos", f"{flujos_negativos}")
        st.metric(
            "% Meses Positivos",
            f"{((len(flujos)-flujos_negativos)/len(flujos)*100):.1f}%",
        )

    # Tabla detallada de flujos (primeros 12 meses)
    st.markdown("### 📋 Detalle de Flujos (Primeros 12 Meses)")

    meses_mostrar = min(12, len(proyecto.flujo_efectivo))

    datos_detalle = []
    for i in range(meses_mostrar):
        datos_detalle.append(
            {
                "Mes": i + 1,
                "Ingresos": (
                    f"${proyecto.ingresos_operativos[i]:,.0f}"
                    if hasattr(proyecto, "ingresos_operativos")
                    else "N/A"
                ),
                "Egresos": (
                    f"${proyecto.egresos_operativos[i]:,.0f}"
                    if hasattr(proyecto, "egresos_operativos")
                    else "N/A"
                ),
                "Flujo Neto": f"${proyecto.flujo_efectivo[i]:,.0f}",
                "Flujo Acumulado": f"${sum(proyecto.flujo_efectivo[:i+1]) - proyecto.inversion_inicial:,.0f}",
            }
        )

    df_detalle = pd.DataFrame(datos_detalle)
    st.dataframe(df_detalle, use_container_width=True)


def mostrar_visualizaciones(proyecto):
    """Muestra todas las visualizaciones usando st.pyplot"""

    st.header("📈 Visualizaciones Interactivas")

    if not verificar_integridad_datos(proyecto)[0]:
        st.warning(
            "⚠️ Complete la configuración financiera para ver las visualizaciones"
        )
        return

    # Tabs para organizar visualizaciones
    tab1, tab2, tab3, tab4, tab5 , tab6 = st.tabs(
        [
            "🎯 Dashboard",
            "💰 Flujo Efectivo",
            "📊 Sensibilidad",
            "📄 Escenarios",
            "📋 Ejecutivo",
            "🥧 Composición Financiera"
        ]
    )

    with tab1:
        st.subheader("Dashboard de Indicadores Principales")
        # USAR st.pyplot en lugar de st.plotly_chart
        fig_tir, fig_vpn, fig_recuperacion = crear_dashboard_indicadores(proyecto)

        col1, col2 = st.columns(2)
        with col1:
            if fig_tir:
                st.pyplot(fig_tir, use_container_width=True)

        with col2:
            if fig_vpn:
                st.pyplot(fig_vpn, use_container_width=True)

        if fig_recuperacion:
            st.pyplot(fig_recuperacion, use_container_width=True)

    with tab2:
        st.subheader("Análisis Completo de Flujo de Efectivo")
        fig_flujo = crear_analisis_flujo_efectivo(proyecto)
        if fig_flujo:
            st.pyplot(fig_flujo, use_container_width=True)

    with tab3:
        st.subheader("Análisis de Sensibilidad Visual")
        variaciones_ing = [-20, -10, -5, 0, 5, 10, 20]
        variaciones_egr = [-15, -10, -5, 0, 5, 10, 15]

        with st.spinner("Calculando análisis de sensibilidad..."):
            resultados_sens = proyecto.analisis_sensibilidad(
                variaciones_ing, variaciones_egr, 0.13
            )

        fig_tir_sens, fig_vpn_sens = crear_analisis_sensibilidad_visual(resultados_sens)

        if fig_tir_sens:
            st.pyplot(fig_tir_sens, use_container_width=True)

        if fig_vpn_sens:
            st.pyplot(fig_vpn_sens, use_container_width=True)

    with tab4:
        st.subheader("Comparación de Escenarios")
        fig_escenarios = crear_comparacion_escenarios(proyecto)
        if fig_escenarios:
            st.pyplot(fig_escenarios, use_container_width=True)

    with tab5:
        st.subheader("Resumen Ejecutivo Visual")
        fig_ejecutivo = crear_resumen_ejecutivo_visual(proyecto)
        if fig_ejecutivo:
            st.pyplot(fig_ejecutivo, use_container_width=True)

    with tab6:  # Nueva tab
        st.subheader("🥧 Composición Financiera Interactiva")
        
        fig_circular, datos_jerarquicos = crear_grafico_circular_interactivo(proyecto)
        
        if fig_circular:
            # Mostrar gráfico principal
            selected_points = st.plotly_chart(fig_circular, use_container_width=True, key="circular_main")
            
            # Botones para drill-down
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("📈 Desglose Ingresos"):
                    fig_detalle = actualizar_grafico_circular_drilldown(datos_jerarquicos, "Ingresos Totales")
                    st.plotly_chart(fig_detalle, use_container_width=True)
            
            with col2:
                if st.button("📉 Desglose Egresos"):
                    fig_detalle = actualizar_grafico_circular_drilldown(datos_jerarquicos, "Egresos Totales")
                    st.plotly_chart(fig_detalle, use_container_width=True)
            
            with col3:
                if st.button("🔄 Volver General"):
                    st.rerun()

def generar_reportes(proyecto):
    """Genera y permite descargar reportes"""

    st.header("📄 Generación de Reportes")

    if not verificar_integridad_datos(proyecto)[0]:
        st.warning("⚠️ Complete la configuración financiera para generar reportes")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Reporte Excel Completo")
        st.markdown(
            """
       **Incluye:**
       - Resumen ejecutivo
       - Flujo de efectivo detallado
       - Análisis de sensibilidad
       - Datos de entrada
       - Tablas para gráficos
       """
        )

        if st.button("📄 Generar Excel", type="primary"):
            with st.spinner("Generando archivo Excel..."):
                try:
                    excel_buffer = generar_excel_completo(proyecto)
                    if excel_buffer:
                        st.success("✅ Archivo Excel generado exitosamente")
                        crear_boton_descarga_excel(
                            excel_buffer,
                            f"Analisis_Proyecto_SEMAVENCA_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                        )
                    else:
                        st.error("❌ Error generando archivo Excel")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    with col2:
        st.subheader("📋 Reporte Ejecutivo PDF")
        st.markdown(
            """
       **Incluye:**
       - Resumen de indicadores
       - Análisis de viabilidad
       - Recomendaciones
       - Interpretación profesional
       """
        )

        if st.button("📄 Generar PDF", type="secondary"):
            with st.spinner("Generando reporte PDF..."):
                try:
                    pdf_buffer = generar_reporte_ejecutivo_pdf(proyecto)
                    if pdf_buffer:
                        st.success("✅ Reporte PDF generado exitosamente")
                        crear_boton_descarga_pdf(
                            pdf_buffer,
                            f"Reporte_Ejecutivo_SEMAVENCA_{pd.Timestamp.now().strftime('%Y%m%d')}.pdf",
                        )
                    else:
                        st.error("❌ Error generando reporte PDF")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

    st.markdown("---")

    # Resumen final del proyecto
    st.subheader("📋 Resumen Final del Proyecto")

    if hasattr(proyecto, "indicadores") and proyecto.indicadores:
        indicadores = proyecto.indicadores

        # Determinar viabilidad
        tir = indicadores.get("tir", 0)
        vpn = indicadores.get("vpn", 0)

        if tir and tir > 0.15 and vpn > 0:
            estado = "✅ VIABLE"
            color = "success"
            mensaje = "El proyecto cumple con todos los criterios de viabilidad."
        elif tir and tir > 0.10 or vpn > 0:
            estado = "⚠️ MARGINAL"
            color = "warning"
            mensaje = "El proyecto requiere análisis adicional y posibles mejoras."
        else:
            estado = "❌ NO VIABLE"
            color = "error"
            mensaje = "El proyecto no cumple con los criterios mínimos de rentabilidad."

        # Mostrar resultado
        if color == "success":
            st.success(f"**Estado del Proyecto**: {estado}")
        elif color == "warning":
            st.warning(f"**Estado del Proyecto**: {estado}")
        else:
            st.error(f"**Estado del Proyecto**: {estado}")

        st.info(mensaje)

        # Tabla resumen final
        datos_finales = [
            ["Inversión Inicial", f"${proyecto.inversion_inicial:,.0f}"],
            ["TIR", f"{tir:.2%}" if tir else "No calculable"],
            ["VPN", f"${vpn:,.0f}"],
            ["ROI", f"{indicadores.get('roi', 0):.1f}%"],
            ["Meses de Análisis", f"{len(getattr(proyecto, 'flujo_efectivo', []))}"],
            ["Código del Proyecto", generar_codigo_proyecto()],
        ]

        df_final = pd.DataFrame(datos_finales, columns=["Métrica", "Valor"])
        st.dataframe(df_final, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
