import streamlit as st

"""
Módulo de Generación de Reportes
Exporta resultados a Excel y genera reportes ejecutivos
"""
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime


def generar_excel_completo(proyecto):
    """
    Genera archivo Excel completo con todos los análisis

    Args:
        proyecto: Instancia de ProyectoInversion

    Returns:
        BytesIO: Archivo Excel en memoria
    """
    # Crear archivo Excel en memoria
    output = BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        # Formatos personalizados
        formato_titulo = workbook.add_format(
            {
                "bold": True,
                "font_size": 14,
                "bg_color": "#1f4e79",
                "font_color": "white",
                "align": "center",
            }
        )

        formato_header = workbook.add_format(
            {
                "bold": True,
                "bg_color": "#4472C4",
                "font_color": "white",
                "align": "center",
                "border": 1,
            }
        )

        formato_moneda = workbook.add_format(
            {"num_format": "$#,##0.00", "align": "right"}
        )

        formato_porcentaje = workbook.add_format(
            {"num_format": "0.00%", "align": "right"}
        )

        formato_numero = workbook.add_format({"num_format": "#,##0", "align": "right"})

        # Hoja 1: Resumen Ejecutivo
        crear_hoja_resumen_ejecutivo(
            writer,
            proyecto,
            formato_titulo,
            formato_header,
            formato_moneda,
            formato_porcentaje,
        )

        # Hoja 2: Flujo de Efectivo Detallado
        crear_hoja_flujo_efectivo(
            writer,
            proyecto,
            formato_titulo,
            formato_header,
            formato_moneda,
            formato_numero,
        )

        # Hoja 3: Análisis de Sensibilidad
        crear_hoja_sensibilidad(
            writer,
            proyecto,
            formato_titulo,
            formato_header,
            formato_porcentaje,
            formato_moneda,
        )

        # Hoja 4: Datos de Entrada
        crear_hoja_datos_entrada(
            writer,
            proyecto,
            formato_titulo,
            formato_header,
            formato_moneda,
            formato_porcentaje,
        )

        # Hoja 5: Gráficos y Análisis
        crear_hoja_graficos_datos(writer, proyecto, formato_titulo, formato_header)

    output.seek(0)
    return output


def crear_hoja_resumen_ejecutivo(
    writer, proyecto, fmt_titulo, fmt_header, fmt_moneda, fmt_porcentaje
):
    """Crea hoja de resumen ejecutivo"""

    # Datos para el resumen
    indicadores = getattr(proyecto, "indicadores", {})

    data_resumen = [
        ["PROYECTO DE INVERSIÓN - SEMAVENCA", ""],
        ["Fecha de Análisis", datetime.now().strftime("%d/%m/%Y")],
        ["", ""],
        ["PARÁMETROS PRINCIPALES", ""],
        ["Inversión Inicial", proyecto.inversion_inicial],
        ["Meses Preoperativos", getattr(proyecto, "meses_preoperativos", 0)],
        ["Meses Operativos", len(getattr(proyecto, "flujo_efectivo", []))],
        ["", ""],
        ["INDICADORES FINANCIEROS", ""],
        ["TIR (Tasa Interna de Retorno)", indicadores.get("tir", 0)],
        ["VPN (Valor Presente Neto)", indicadores.get("vpn", 0)],
        ["ROI (Return on Investment)", indicadores.get("roi", 0) / 100],
        ["", ""],
        ["ANÁLISIS DE VIABILIDAD", ""],
        [
            "Estado del Proyecto",
            "VIABLE" if indicadores.get("tir", 0) > 0.15 else "REQUIERE REVISIÓN",
        ],
        [
            "TIR vs Costo de Capital",
            "POSITIVO" if indicadores.get("tir", 0) > 0.13 else "NEGATIVO",
        ],
        ["VPN", "POSITIVO" if indicadores.get("vpn", 0) > 0 else "NEGATIVO"],
    ]

    df_resumen = pd.DataFrame(data_resumen, columns=["Concepto", "Valor"])
    df_resumen.to_excel(writer, sheet_name="Resumen Ejecutivo", index=False, startrow=2)

    worksheet = writer.sheets["Resumen Ejecutivo"]

    # Aplicar formatos
    worksheet.merge_range("A1:B1", "RESUMEN EJECUTIVO", fmt_titulo)
    worksheet.set_column("A:A", 30)
    worksheet.set_column("B:B", 20)

    # Formato condicional para valores monetarios y porcentajes
    for row in range(3, len(data_resumen) + 3):
        concepto = data_resumen[row - 3][0]
        if "Inversión" in concepto or "VPN" in concepto:
            worksheet.write(row, 1, data_resumen[row - 3][1], fmt_moneda)
        elif "TIR" in concepto or "ROI" in concepto:
            worksheet.write(row, 1, data_resumen[row - 3][1], fmt_porcentaje)


def crear_hoja_flujo_efectivo(
    writer, proyecto, fmt_titulo, fmt_header, fmt_moneda, fmt_numero
):
    """Crea hoja detallada de flujo de efectivo"""

    if not hasattr(proyecto, "flujo_efectivo") or not proyecto.flujo_efectivo:
        return

    meses = list(range(1, len(proyecto.flujo_efectivo) + 1))
    ingresos = getattr(
        proyecto, "ingresos_operativos", [0] * len(proyecto.flujo_efectivo)
    )
    egresos = getattr(
        proyecto, "egresos_operativos", [0] * len(proyecto.flujo_efectivo)
    )
    flujo_neto = proyecto.flujo_efectivo
    flujo_acumulado = np.cumsum([-proyecto.inversion_inicial] + flujo_neto)[1:]

    # Crear DataFrame
    df_flujo = pd.DataFrame(
        {
            "Mes": meses,
            "Ingresos": ingresos,
            "Egresos": egresos,
            "Flujo Neto": flujo_neto,
            "Flujo Acumulado": flujo_acumulado,
            "Rentabilidad %": [
                (f / proyecto.inversion_inicial) * 100 for f in flujo_acumulado
            ],
        }
    )

    # Agregar fila de totales
    total_row = pd.DataFrame(
        {
            "Mes": ["TOTAL"],
            "Ingresos": [sum(ingresos)],
            "Egresos": [sum(egresos)],
            "Flujo Neto": [sum(flujo_neto)],
            "Flujo Acumulado": [flujo_acumulado[-1]],
            "Rentabilidad %": [
                (flujo_acumulado[-1] / proyecto.inversion_inicial) * 100
            ],
        }
    )

    df_completo = pd.concat([df_flujo, total_row], ignore_index=True)
    df_completo.to_excel(
        writer, sheet_name="Flujo de Efectivo", index=False, startrow=2
    )

    worksheet = writer.sheets["Flujo de Efectivo"]

    # Configurar formato
    worksheet.merge_range("A1:F1", "FLUJO DE EFECTIVO PROYECTADO", fmt_titulo)
    worksheet.set_column("A:A", 8)
    worksheet.set_column("B:E", 15)
    worksheet.set_column("F:F", 12)

    # Aplicar formatos a datos
    for row in range(3, len(df_completo) + 3):
        worksheet.write(row, 1, df_completo.iloc[row - 3]["Ingresos"], fmt_moneda)
        worksheet.write(row, 2, df_completo.iloc[row - 3]["Egresos"], fmt_moneda)
        worksheet.write(row, 3, df_completo.iloc[row - 3]["Flujo Neto"], fmt_moneda)
        worksheet.write(
            row, 4, df_completo.iloc[row - 3]["Flujo Acumulado"], fmt_moneda
        )
        worksheet.write(
            row,
            5,
            df_completo.iloc[row - 3]["Rentabilidad %"] / 100,
            fmt_titulo if row == len(df_completo) + 2 else None,
        )


def crear_hoja_sensibilidad(
    writer, proyecto, fmt_titulo, fmt_header, fmt_porcentaje, fmt_moneda
):
    """Crea hoja de análisis de sensibilidad"""

    # Simular análisis de sensibilidad básico
    variaciones = [-20, -10, -5, 0, 5, 10, 20]

    # Crear matrices de sensibilidad
    sensibilidad_data = []
    base_tir = getattr(proyecto, "indicadores", {}).get("tir", 0.15)
    base_vpn = getattr(proyecto, "indicadores", {}).get("vpn", 100000)

    for var_egr in variaciones:
        row_tir = []
        row_vpn = []
        for var_ing in variaciones:
            # Estimación simplificada del impacto
            factor_combinado = (1 + var_ing / 100) / (1 + var_egr / 100) - 1
            tir_ajustada = base_tir * (1 + factor_combinado * 0.5)
            vpn_ajustado = base_vpn * (1 + factor_combinado * 0.8)

            row_tir.append(tir_ajustada)
            row_vpn.append(vpn_ajustado)

        sensibilidad_data.append(
            {
                "Var_Egresos": f"{var_egr:+}%",
                **{
                    f"Ing_{var_ing:+}%": tir
                    for var_ing, tir in zip(variaciones, row_tir)
                },
            }
        )

    df_sens_tir = pd.DataFrame(sensibilidad_data)

    # Escribir análisis de sensibilidad TIR
    df_sens_tir.to_excel(
        writer, sheet_name="Análisis Sensibilidad", index=False, startrow=3
    )

    worksheet = writer.sheets["Análisis Sensibilidad"]
    worksheet.merge_range("A1:H1", "ANÁLISIS DE SENSIBILIDAD", fmt_titulo)
    worksheet.write("A2", "Análisis TIR - Variación Ingresos vs Egresos", fmt_header)

    # Aplicar formato porcentual a los valores TIR
    for row in range(4, 4 + len(variaciones)):
        for col in range(1, len(variaciones) + 1):
            worksheet.write(row, col, df_sens_tir.iloc[row - 4, col], fmt_porcentaje)


def crear_hoja_datos_entrada(
    writer, proyecto, fmt_titulo, fmt_header, fmt_moneda, fmt_porcentaje
):
    """
    Crea hoja con datos de entrada del proyecto"""

    # Datos de configuración
    config_ingresos = getattr(proyecto, "configuracion_ingresos", {})
    config_egresos = getattr(proyecto, "configuracion_egresos", {})

    datos_entrada = [
        ["PARÁMETROS DE INVERSIÓN", ""],
        ["Inversión Inicial", proyecto.inversion_inicial],
        ["Meses Preoperativos", getattr(proyecto, "meses_preoperativos", 0)],
        ["", ""],
        ["CONFIGURACIÓN DE INGRESOS", ""],
        ["Multas Diarias", config_ingresos.get("multas_diarias", 0)],
        ["Valor Multa con Descuento", config_ingresos.get("valor_multa_descuento", 0)],
        ["% Pago Voluntario", config_ingresos.get("pct_pago_voluntario", 0)],
        ["% Ingreso Operativo", config_ingresos.get("pct_ingreso_operativo", 0)],
        ["Tasa Variación Ingresos %", config_ingresos.get("tasa_variacion", 0)],
        ["", ""],
        ["CONFIGURACIÓN DE EGRESOS", ""],
        ["Total Egresos Base Mensual", config_egresos.get("total_base", 0)],
        ["Tasa Variación Egresos %", config_egresos.get("tasa_variacion", 0)],
        ["", ""],
        ["TASAS DE DESCUENTO", ""],
        ["Tasa Libre de Riesgo", config_ingresos.get("tasa_libre_riesgo", 0.05)],
        ["Tasa Riesgo País", config_ingresos.get("tasa_riesgo_pais", 0.03)],
        ["Tasa Riesgo Proyecto", config_ingresos.get("tasa_riesgo_proyecto", 0.05)],
        ["Tasa Descuento Total", config_ingresos.get("tasa_descuento_total", 0.13)],
    ]

    df_datos = pd.DataFrame(datos_entrada, columns=["Parámetro", "Valor"])
    df_datos.to_excel(writer, sheet_name="Datos de Entrada", index=False, startrow=2)

    worksheet = writer.sheets["Datos de Entrada"]
    worksheet.merge_range("A1:B1", "DATOS DE ENTRADA DEL PROYECTO", fmt_titulo)
    worksheet.set_column("A:A", 25)
    worksheet.set_column("B:B", 18)


def crear_hoja_graficos_datos(writer, proyecto, fmt_titulo, fmt_header):
    """Crea hoja con datos para gráficos"""

    if not hasattr(proyecto, "flujo_efectivo") or not proyecto.flujo_efectivo:
        return

    # Datos para gráficos
    meses = list(range(1, len(proyecto.flujo_efectivo) + 1))
    ingresos = getattr(
        proyecto, "ingresos_operativos", [0] * len(proyecto.flujo_efectivo)
    )
    egresos = getattr(
        proyecto, "egresos_operativos", [0] * len(proyecto.flujo_efectivo)
    )

    df_graficos = pd.DataFrame(
        {
            "Mes": meses,
            "Ingresos": ingresos,
            "Egresos": egresos,
            "Flujo_Neto": proyecto.flujo_efectivo,
            "Flujo_Acumulado": np.cumsum(proyecto.flujo_efectivo),
            "TIR_Acumulada": [
                0.15 + (i / len(meses)) * 0.05 for i in range(len(meses))
            ],  # Simulado
            "VPN_Acumulado": np.cumsum(
                [
                    f / (1.13 ** (i / 12))
                    for i, f in enumerate(proyecto.flujo_efectivo, 1)
                ]
            ),
        }
    )

    df_graficos.to_excel(writer, sheet_name="Datos Gráficos", index=False, startrow=2)

    worksheet = writer.sheets["Datos Gráficos"]
    worksheet.merge_range("A1:G1", "DATOS PARA GRÁFICOS", fmt_titulo)


def generar_reporte_ejecutivo_pdf(proyecto):
    """
    Genera reporte ejecutivo en PDF

    Args:
        proyecto: Instancia de ProyectoInversion

    Returns:
        BytesIO: Archivo PDF en memoria
    """
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1f4e79"),
        )

        subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            parent=styles["Heading2"],
            fontSize=14,
            spaceAfter=20,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#4472C4"),
        )

        normal_style = styles["Normal"]

        # Contenido del reporte
        story = []

        # Título
        story.append(Paragraph("SEMAVENCA", title_style))
        story.append(
            Paragraph("REPORTE EJECUTIVO - PROYECTO DE INVERSIÓN", subtitle_style)
        )
        story.append(Spacer(1, 20))

        # Información básica
        story.append(Paragraph("RESUMEN EJECUTIVO", subtitle_style))

        indicadores = getattr(proyecto, "indicadores", {})
        fecha_actual = datetime.now().strftime("%d de %B de %Y")

        resumen_text = f"""
       <b>Fecha de Análisis:</b> {fecha_actual}<br/>
       <b>Inversión Inicial:</b> ${proyecto.inversion_inicial:,.0f}<br/>
       <b>Período de Análisis:</b> {len(getattr(proyecto, 'flujo_efectivo', []))} meses<br/>
       <br/>
       <b>INDICADORES PRINCIPALES:</b><br/>
       • TIR: {indicadores.get('tir', 0):.2%}<br/>
       • VPN: ${indicadores.get('vpn', 0):,.0f}<br/>
       • ROI: {indicadores.get('roi', 0):.1f}%<br/>
       """

        story.append(Paragraph(resumen_text, normal_style))
        story.append(Spacer(1, 20))

        # Análisis de viabilidad
        story.append(Paragraph("ANÁLISIS DE VIABILIDAD", subtitle_style))

        tir = indicadores.get("tir", 0)
        vpn = indicadores.get("vpn", 0)

        if tir > 0.15 and vpn > 0:
            viabilidad = "PROYECTO VIABLE"
            color_viabilidad = colors.green
            recomendacion = "Se recomienda la ejecución del proyecto."
        elif tir > 0.10 or vpn > 0:
            viabilidad = "PROYECTO MARGINAL"
            color_viabilidad = colors.orange
            recomendacion = "Requiere análisis adicional y posibles ajustes."
        else:
            viabilidad = "PROYECTO NO VIABLE"
            color_viabilidad = colors.red
            recomendacion = "No se recomienda la ejecución en las condiciones actuales."

        viabilidad_style = ParagraphStyle(
            "Viabilidad",
            parent=normal_style,
            textColor=color_viabilidad,
            fontSize=12,
            alignment=TA_CENTER,
        )

        story.append(Paragraph(f"<b>{viabilidad}</b>", viabilidad_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(recomendacion, normal_style))
        story.append(Spacer(1, 20))

        # Tabla de indicadores detallados
        story.append(Paragraph("INDICADORES DETALLADOS", subtitle_style))

        tabla_datos = [
            ["Indicador", "Valor", "Interpretación"],
            ["TIR", f"{tir:.2%}", "Rentabilidad del proyecto"],
            ["VPN", f"${vpn:,.0f}", "Valor agregado en pesos"],
            ["ROI", f"{indicadores.get('roi', 0):.1f}%", "Retorno sobre inversión"],
            [
                "Payback",
                f"{len(getattr(proyecto, 'flujo_efectivo', []))//2} meses",
                "Tiempo de recuperación estimado",
            ],
        ]

        tabla = Table(tabla_datos, colWidths=[2 * inch, 1.5 * inch, 2.5 * inch])
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        story.append(tabla)
        story.append(Spacer(1, 20))

        # Recomendaciones
        story.append(Paragraph("RECOMENDACIONES", subtitle_style))

        recomendaciones = [
            "Monitorear regularmente los indicadores de desempeño",
            "Realizar análisis de sensibilidad periódicos",
            "Establecer controles de gestión de riesgos",
            "Evaluar escenarios alternativos según condiciones del mercado",
        ]

        for rec in recomendaciones:
            story.append(Paragraph(f"• {rec}", normal_style))

        story.append(Spacer(1, 30))

        # Pie de página
        pie_text = """
       <br/><br/>
       <i>Elaborado por: MSc Jesús Salazar Rojas<br/>
       Economista - Contador Público / +58(0414)2868869<br/>
       SEMAVENCA</i>
       """

        pie_style = ParagraphStyle(
            "Pie",
            parent=normal_style,
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey,
        )

        story.append(Paragraph(pie_text, pie_style))

        # Construir PDF
        doc.build(story)
        buffer.seek(0)
        return buffer

    except ImportError:
        st.error("📄 ReportLab no está instalado. Instale con: pip install reportlab")
        return None
    except Exception as e:
        st.error(f"❌ Error generando PDF: {str(e)}")
        return None


def crear_boton_descarga_excel(
    excel_buffer, nombre_archivo="proyecto_inversion_semavenca.xlsx"
):
    """
    Crea botón de descarga para archivo Excel

    Args:
        excel_buffer: Buffer con archivo Excel
        nombre_archivo: Nombre del archivo a descargar
    """
    excel_data = excel_buffer.getvalue()

    st.download_button(
        label="📊 Descargar Análisis Completo (Excel)",
        data=excel_data,
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Descarga el análisis completo en formato Excel",
    )


def crear_boton_descarga_pdf(
    pdf_buffer, nombre_archivo="reporte_ejecutivo_semavenca.pdf"
):
    """
    Crea botón de descarga para archivo PDF

    Args:
        pdf_buffer: Buffer con archivo PDF
        nombre_archivo: Nombre del archivo a descargar
    """
    if pdf_buffer:
        pdf_data = pdf_buffer.getvalue()

        st.download_button(
            label="📄 Descargar Reporte Ejecutivo (PDF)",
            data=pdf_data,
            file_name=nombre_archivo,
            mime="application/pdf",
            help="Descarga el reporte ejecutivo en formato PDF",
        )


def generar_resumen_hallazgos(proyecto):
    """
    Genera resumen automático de hallazgos clave

    Args:
        proyecto: Instancia de ProyectoInversion

    Returns:
        list: Lista de hallazgos y recomendaciones
    """
    hallazgos = []
    indicadores = getattr(proyecto, "indicadores", {})

    tir = indicadores.get("tir", 0)
    vpn = indicadores.get("vpn", 0)
    roi = indicadores.get("roi", 0)

    # Análisis TIR
    if tir > 0.25:
        hallazgos.append(
            {
                "tipo": "positivo",
                "titulo": "TIR Excelente",
                "descripcion": f"La TIR de {tir:.2%} indica una rentabilidad excepcional, muy superior al costo de capital.",
                "recomendacion": "Proyecto altamente recomendado para ejecución inmediata.",
            }
        )
    elif tir > 0.15:
        hallazgos.append(
            {
                "tipo": "positivo",
                "titulo": "TIR Satisfactoria",
                "descripcion": f"La TIR de {tir:.2%} supera el umbral mínimo requerido.",
                "recomendacion": "Proyecto viable, proceder con la implementación.",
            }
        )
    elif tir > 0.10:
        hallazgos.append(
            {
                "tipo": "neutro",
                "titulo": "TIR Marginal",
                "descripcion": f"La TIR de {tir:.2%} está en el límite de viabilidad.",
                "recomendacion": "Evaluar posibles mejoras antes de la ejecución.",
            }
        )
    else:
        hallazgos.append(
            {
                "tipo": "negativo",
                "titulo": "TIR Insuficiente",
                "descripcion": f"La TIR de {tir:.2%} no alcanza el mínimo requerido.",
                "recomendacion": "Replantear el modelo de negocio o rechazar el proyecto.",
            }
        )

    # Análisis VPN
    if vpn > proyecto.inversion_inicial * 0.5:
        hallazgos.append(
            {
                "tipo": "positivo",
                "titulo": "VPN Muy Atractivo",
                "descripcion": f"El VPN de ${vpn:,.0f} representa más del 50% de la inversión inicial.",
                "recomendacion": "Excelente creación de valor para la empresa.",
            }
        )
    elif vpn > 0:
        hallazgos.append(
            {
                "tipo": "positivo",
                "titulo": "VPN Positivo",
                "descripcion": f"El VPN de ${vpn:,.0f} indica creación de valor.",
                "recomendacion": "Proyecto genera valor económico agregado.",
            }
        )
    else:
        hallazgos.append(
            {
                "tipo": "negativo",
                "titulo": "VPN Negativo",
                "descripcion": f"El VPN de ${vpn:,.0f} indica destrucción de valor.",
                "recomendacion": "Proyecto no recomendado en las condiciones actuales.",
            }
        )

    # Análisis de flujo de efectivo
    if hasattr(proyecto, "flujo_efectivo") and proyecto.flujo_efectivo:
        flujos_positivos = sum(1 for f in proyecto.flujo_efectivo if f > 0)
        total_meses = len(proyecto.flujo_efectivo)

        if flujos_positivos / total_meses > 0.8:
            hallazgos.append(
                {
                    "tipo": "positivo",
                    "titulo": "Flujos Consistentes",
                    "descripcion": f"{flujos_positivos} de {total_meses} meses tienen flujo positivo.",
                    "recomendacion": "Excelente estabilidad de flujos de efectivo.",
                }
            )
        elif flujos_positivos / total_meses > 0.6:
            hallazgos.append(
                {
                    "tipo": "neutro",
                    "titulo": "Flujos Moderados",
                    "descripcion": f"{flujos_positivos} de {total_meses} meses tienen flujo positivo.",
                    "recomendacion": "Monitorear de cerca la generación de flujos.",
                }
            )
        else:
            hallazgos.append(
                {
                    "tipo": "negativo",
                    "titulo": "Flujos Irregulares",
                    "descripcion": f"Solo {flujos_positivos} de {total_meses} meses tienen flujo positivo.",
                    "recomendacion": "Revisar modelo operativo y estructura de costos.",
                }
            )

    return hallazgos
