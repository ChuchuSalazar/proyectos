"""
Módulo de Visualizaciones Interactivas - VERSIÓN CORREGIDA
Genera gráficos profesionales usando matplotlib para análisis financiero
CAMBIO: Usar matplotlib/pyplot en lugar de Plotly para compatibilidad con Streamlit
"""

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime


# Configurar estilo de matplotlib
plt.style.use("default")
sns.set_palette("husl")


def crear_dashboard_indicadores(proyecto):
    """
    Crea dashboard principal con indicadores clave

    Args:
        proyecto: Instancia de ProyectoInversion

    Returns:
        tuple: Figuras de matplotlib para dashboard
    """
    # Verificar datos disponibles
    if not hasattr(proyecto, "indicadores") or not proyecto.indicadores:
        st.warning("⚠️ No hay indicadores calculados para mostrar")
        return None, None, None

    indicadores = proyecto.indicadores

    # 1. Gráfico de gauge para TIR
    fig_tir, ax_tir = plt.subplots(1, 1, figsize=(8, 6))

    tir_valor = indicadores.get("tir", 0) * 100

    # Crear gráfico de gauge simulado con barras
    categorias = ["0-10%", "10-15%", "15-20%", "20%+"]
    valores = [10, 5, 5, max(0, tir_valor - 20)]
    colores = ["lightcoral", "yellow", "lightgreen", "green"]

    # Barra horizontal tipo gauge
    bars = ax_tir.barh(categorias, [10, 15, 20, 30], color=colores, alpha=0.3)

    # Indicador de TIR actual
    if tir_valor <= 10:
        pos = 0
    elif tir_valor <= 15:
        pos = 1
    elif tir_valor <= 20:
        pos = 2
    else:
        pos = 3

    ax_tir.barh(categorias[pos], tir_valor, color=colores[pos], alpha=0.8)
    ax_tir.axvline(x=15, color="red", linestyle="--", linewidth=2, label="Objetivo 15%")

    ax_tir.set_xlabel("TIR (%)")
    ax_tir.set_title(
        f"TIR del Proyecto: {tir_valor:.2f}%", fontsize=14, fontweight="bold"
    )
    ax_tir.legend()
    plt.tight_layout()

    # 2. Gráfico de barras para VPN scenarios
    fig_vpn, ax_vpn = plt.subplots(1, 1, figsize=(8, 6))

    vpn_base = indicadores.get("vpn", 0)

    escenarios = ["Pesimista\n(-20%)", "Base", "Optimista\n(+20%)"]
    vpn_valores = [vpn_base * 0.8, vpn_base, vpn_base * 1.2]
    colores_vpn = ["red" if v < 0 else "green" for v in vpn_valores]

    bars_vpn = ax_vpn.bar(escenarios, vpn_valores, color=colores_vpn, alpha=0.7)

    # Añadir valores en las barras
    for bar, valor in zip(bars_vpn, vpn_valores):
        height = bar.get_height()
        ax_vpn.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + (abs(height) * 0.01),
            f"${valor:,.0f}",
            ha="center",
            va="bottom" if height > 0 else "top",
        )

    ax_vpn.axhline(y=0, color="black", linestyle="-", linewidth=1)
    ax_vpn.set_ylabel("VPN ($)")
    ax_vpn.set_title("VPN por Escenarios", fontsize=14, fontweight="bold")
    plt.xticks(rotation=0)
    plt.tight_layout()

    # 3. Gráfico de recuperación de inversión
    fig_recuperacion = None
    if hasattr(proyecto, "flujo_efectivo") and proyecto.flujo_efectivo:
        fig_recuperacion, ax_recuperacion = plt.subplots(1, 1, figsize=(10, 6))

        flujos_acum = np.cumsum(
            [-proyecto.inversion_inicial] + list(proyecto.flujo_efectivo)
        )
        meses = list(range(len(flujos_acum)))

        # Línea de flujo acumulado
        ax_recuperacion.plot(
            meses, flujos_acum, "b-", linewidth=3, label="Flujo Acumulado"
        )
        ax_recuperacion.fill_between(meses, flujos_acum, alpha=0.3, color="lightblue")

        # Línea de equilibrio
        ax_recuperacion.axhline(
            y=0, color="red", linestyle="--", linewidth=2, label="Punto de Equilibrio"
        )

        # Punto de recuperación
        punto_recuperacion = next((i for i, x in enumerate(flujos_acum) if x > 0), None)
        if punto_recuperacion:
            ax_recuperacion.plot(
                punto_recuperacion,
                flujos_acum[punto_recuperacion],
                "go",
                markersize=15,
                label=f"Recuperación: Mes {punto_recuperacion}",
            )

        ax_recuperacion.set_xlabel("Mes")
        ax_recuperacion.set_ylabel("Flujo Acumulado ($)")
        ax_recuperacion.set_title(
            "Recuperación de Inversión", fontsize=14, fontweight="bold"
        )
        ax_recuperacion.legend()
        ax_recuperacion.grid(True, alpha=0.3)
        plt.tight_layout()

    return fig_tir, fig_vpn, fig_recuperacion


def crear_analisis_flujo_efectivo(proyecto):
    """
    Crea análisis detallado del flujo de efectivo

    Args:
        proyecto: Instancia de ProyectoInversion

    Returns:
        matplotlib.figure.Figure: Gráfico de flujo de efectivo
    """
    if not hasattr(proyecto, "flujo_efectivo") or not proyecto.flujo_efectivo:
        st.warning("⚠️ No hay datos de flujo de efectivo para visualizar")
        return None

    # Preparar datos
    meses = list(range(1, len(proyecto.flujo_efectivo) + 1))
    ingresos = getattr(
        proyecto, "ingresos_operativos", [0] * len(proyecto.flujo_efectivo)
    )
    egresos = getattr(
        proyecto, "egresos_operativos", [0] * len(proyecto.flujo_efectivo)
    )
    flujo_neto = proyecto.flujo_efectivo

    # Flujo acumulado iniciando con inversión negativa
    flujos_con_inversion = [-proyecto.inversion_inicial] + list(flujo_neto)
    flujo_acumulado = np.cumsum(flujos_con_inversion)[1:]  # Excluir inversión inicial

    # Crear figura con subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))

    # 1. Flujos mensuales
    width = 0.35
    x = np.array(meses)

    ax1.bar(
        x - width / 2, ingresos, width, label="Ingresos", color="lightgreen", alpha=0.8
    )
    ax1.bar(
        x + width / 2,
        [-e for e in egresos],
        width,
        label="Egresos",
        color="lightcoral",
        alpha=0.8,
    )
    ax1.plot(meses, flujo_neto, "b-", linewidth=3, marker="o", label="Flujo Neto")

    ax1.set_xlabel("Mes")
    ax1.set_ylabel("Monto ($)")
    ax1.set_title("Flujos Mensuales Operativos")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Flujo acumulado
    meses_con_inversion = list(range(len(flujos_con_inversion)))
    flujo_acum_real = np.cumsum(flujos_con_inversion)

    color_flujo = "darkgreen" if flujo_acum_real[-1] > 0 else "darkred"
    fill_color = "lightgreen" if flujo_acum_real[-1] > 0 else "lightcoral"

    ax2.plot(
        meses_con_inversion,
        flujo_acum_real,
        color=color_flujo,
        linewidth=3,
        label="Flujo Acumulado Real",
    )
    ax2.fill_between(meses_con_inversion, flujo_acum_real, alpha=0.3, color=fill_color)
    ax2.axhline(y=0, color="black", linestyle="--", label="Línea de Equilibrio")

    ax2.set_xlabel("Mes (0 = Inversión Inicial)")
    ax2.set_ylabel("Flujo Acumulado ($)")
    ax2.set_title("Flujo Acumulado (desde Inversión)")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. Distribución de totales (pie chart)
    totales = [sum(ingresos), sum(egresos)]
    labels = ["Ingresos Totales", "Egresos Totales"]
    colors = ["lightgreen", "lightcoral"]

    ax3.pie(totales, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
    ax3.set_title("Distribución de Ingresos vs Egresos")

    # 4. Volatilidad
    if len(ingresos) > 1:
        volatilidad_ingresos = [
            np.std(ingresos[: i + 1]) / np.mean(ingresos[: i + 1]) * 100
            for i in range(1, len(ingresos))
        ]
        volatilidad_egresos = [
            np.std(egresos[: i + 1]) / np.mean(egresos[: i + 1]) * 100
            for i in range(1, len(egresos))
        ]

        ax4.plot(meses[1:], volatilidad_ingresos, "g--", label="Vol. Ingresos (%)")
        ax4.plot(meses[1:], volatilidad_egresos, "r--", label="Vol. Egresos (%)")

        ax4.set_xlabel("Mes")
        ax4.set_ylabel("Coeficiente de Variación (%)")
        ax4.set_title("Volatilidad Mensual")
        ax4.legend()
        ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def crear_analisis_sensibilidad_visual(resultados_sensibilidad):
    """
    Crea visualización de análisis de sensibilidad

    Args:
        resultados_sensibilidad: Resultados del análisis de sensibilidad

    Returns:
        tuple: Figuras de mapas de calor para TIR y VPN
    """
    if not resultados_sensibilidad:
        return None, None

    var_ing = resultados_sensibilidad["variaciones_ing"]
    var_egr = resultados_sensibilidad["variaciones_egr"]
    matriz_tir = np.array(resultados_sensibilidad["tir_matriz"]) * 100
    matriz_vpn = np.array(resultados_sensibilidad["vpn_matriz"])

    # 1. Mapa de calor TIR
    fig_tir, ax_tir = plt.subplots(1, 1, figsize=(10, 8))

    im_tir = ax_tir.imshow(matriz_tir, cmap="RdYlGn", aspect="auto")

    # Configurar etiquetas
    ax_tir.set_xticks(range(len(var_ing)))
    ax_tir.set_yticks(range(len(var_egr)))
    ax_tir.set_xticklabels([f"{x:+.0f}%" for x in var_ing])
    ax_tir.set_yticklabels([f"{y:+.0f}%" for y in var_egr])

    # Añadir valores en las celdas
    for i in range(len(var_egr)):
        for j in range(len(var_ing)):
            ax_tir.text(
                j,
                i,
                f"{matriz_tir[i, j]:.1f}%",
                ha="center",
                va="center",
                color="black",
                fontsize=8,
            )

    ax_tir.set_xlabel("Variación en Ingresos")
    ax_tir.set_ylabel("Variación en Egresos")
    ax_tir.set_title(
        "Análisis de Sensibilidad - TIR (%)", fontsize=14, fontweight="bold"
    )

    # Colorbar
    cbar_tir = plt.colorbar(im_tir, ax=ax_tir)
    cbar_tir.set_label("TIR (%)", rotation=270, labelpad=20)

    plt.tight_layout()

    # 2. Mapa de calor VPN
    fig_vpn, ax_vpn = plt.subplots(1, 1, figsize=(10, 8))

    im_vpn = ax_vpn.imshow(matriz_vpn, cmap="RdBu", aspect="auto")

    # Configurar etiquetas
    ax_vpn.set_xticks(range(len(var_ing)))
    ax_vpn.set_yticks(range(len(var_egr)))
    ax_vpn.set_xticklabels([f"{x:+.0f}%" for x in var_ing])
    ax_vpn.set_yticklabels([f"{y:+.0f}%" for y in var_egr])

    # Añadir valores en las celdas
    for i in range(len(var_egr)):
        for j in range(len(var_ing)):
            ax_vpn.text(
                j,
                i,
                f"{matriz_vpn[i, j]:,.0f}",
                ha="center",
                va="center",
                color="white",
                fontsize=8,
            )

    ax_vpn.set_xlabel("Variación en Ingresos")
    ax_vpn.set_ylabel("Variación en Egresos")
    ax_vpn.set_title(
        "Análisis de Sensibilidad - VPN ($)", fontsize=14, fontweight="bold"
    )

    # Colorbar
    cbar_vpn = plt.colorbar(im_vpn, ax=ax_vpn)
    cbar_vpn.set_label("VPN ($)", rotation=270, labelpad=20)

    plt.tight_layout()

    return fig_tir, fig_vpn


def crear_comparacion_escenarios(proyecto):
    """
    Crea gráfico comparativo de escenarios

    Args:
        proyecto: Instancia de ProyectoInversion

    Returns:
        matplotlib.figure.Figure: Gráfico de escenarios
    """
    if not hasattr(proyecto, "flujo_efectivo") or not proyecto.flujo_efectivo:
        return None

    # Definir escenarios
    escenarios = {
        "Pesimista": {"factor_ing": 0.8, "factor_egr": 1.2, "color": "red"},
        "Base": {"factor_ing": 1.0, "factor_egr": 1.0, "color": "blue"},
        "Optimista": {"factor_ing": 1.2, "factor_egr": 0.9, "color": "green"},
    }

    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    ingresos_base = getattr(
        proyecto, "ingresos_operativos", [0] * len(proyecto.flujo_efectivo)
    )
    egresos_base = getattr(
        proyecto, "egresos_operativos", [0] * len(proyecto.flujo_efectivo)
    )
    meses = list(range(1, len(proyecto.flujo_efectivo) + 1))

    for nombre, config in escenarios.items():
        # Calcular flujos del escenario
        ingresos_escenario = [ing * config["factor_ing"] for ing in ingresos_base]
        egresos_escenario = [egr * config["factor_egr"] for egr in egresos_base]
        flujo_escenario = [
            ing - egr for ing, egr in zip(ingresos_escenario, egresos_escenario)
        ]
        flujo_acum_escenario = np.cumsum(
            [-proyecto.inversion_inicial] + flujo_escenario
        )

        # Agregar línea
        ax.plot(
            meses,
            flujo_acum_escenario[1:],  # Excluir inversión inicial
            color=config["color"],
            linewidth=3,
            marker="o",
            label=nombre,
            markersize=4,
        )

    # Línea de equilibrio
    ax.axhline(
        y=0, color="black", linestyle="--", linewidth=2, label="Punto de Equilibrio"
    )

    ax.set_xlabel("Mes")
    ax.set_ylabel("Flujo Acumulado ($)")
    ax.set_title(
        "Comparación de Escenarios - Flujo Acumulado", fontsize=14, fontweight="bold"
    )
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def crear_grafico_rentabilidad_temporal(proyecto):
    """
    Crea análisis de rentabilidad temporal

    Args:
        proyecto: Instancia de ProyectoInversion

    Returns:
        matplotlib.figure.Figure: Gráfico de rentabilidad
    """
    if not hasattr(proyecto, "flujo_efectivo") or not proyecto.flujo_efectivo:
        return None

    meses = list(range(1, len(proyecto.flujo_efectivo) + 1))
    flujos = [-proyecto.inversion_inicial] + list(proyecto.flujo_efectivo)

    # Calcular TIR acumulada mes a mes (simplificado)
    tir_acumulada = []
    vpn_acumulado = []
    tasa_descuento_mensual = 0.01  # 12% anual aproximadamente

    for i in range(1, len(flujos)):
        flujos_parciales = flujos[: i + 1]

        # TIR parcial (cálculo simplificado)
        try:
            beneficio_parcial = sum(flujos_parciales[1:])
            inversion_parcial = abs(flujos_parciales[0])
            if inversion_parcial > 0 and beneficio_parcial > 0:
                tir_aprox = (beneficio_parcial / inversion_parcial) ** (
                    1 / len(flujos_parciales[1:])
                ) - 1
                tir_acumulada.append(tir_aprox * 100)
            else:
                tir_acumulada.append(0)
        except:
            tir_acumulada.append(0)

        # VPN parcial
        vpn_mes = sum(
            f / ((1 + tasa_descuento_mensual) ** j)
            for j, f in enumerate(flujos_parciales)
        )
        vpn_acumulado.append(vpn_mes)

    # Crear subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # TIR acumulada
    ax1.plot(
        meses,
        tir_acumulada,
        "g-",
        linewidth=3,
        marker="o",
        markersize=4,
        label="TIR Acumulada (%)",
    )
    ax1.fill_between(meses, tir_acumulada, alpha=0.3, color="lightgreen")
    ax1.axhline(
        y=15, color="red", linestyle="--", linewidth=2, label="TIR Objetivo: 15%"
    )

    ax1.set_ylabel("TIR (%)")
    ax1.set_title("Evolución de TIR Acumulada (%)", fontsize=12, fontweight="bold")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # VPN acumulado
    ax2.plot(
        meses,
        vpn_acumulado,
        "b-",
        linewidth=3,
        marker="o",
        markersize=4,
        label="VPN Acumulado ($)",
    )
    ax2.fill_between(meses, vpn_acumulado, alpha=0.3, color="lightblue")
    ax2.axhline(y=0, color="red", linestyle="--", linewidth=2, label="VPN = 0")

    ax2.set_xlabel("Mes")
    ax2.set_ylabel("VPN ($)")
    ax2.set_title("Evolución de VPN Acumulado ($)", fontsize=12, fontweight="bold")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def crear_resumen_ejecutivo_visual(proyecto):
    """
    Crea dashboard ejecutivo con métricas clave y explicaciones
    """
    if not hasattr(proyecto, "indicadores") or not proyecto.indicadores:
        return None

    indicadores = proyecto.indicadores

    # Crear figura con diseño personalizado
    fig = plt.figure(figsize=(15, 12))

    # Crear grid de subplots con espacio para explicaciones
    gs = fig.add_gridspec(4, 3, height_ratios=[1, 1, 1.5, 0.5], width_ratios=[1, 1, 1])

    # Indicadores principales como gauges simulados
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    ax_tabla = fig.add_subplot(gs[1:3, :])
    ax_explicacion = fig.add_subplot(gs[3, :])

    # 1. TIR Gauge con zonas coloreadas
    tir_valor = indicadores.get("tir", 0) * 100 if indicadores.get("tir") else 0

    # Crear gauge circular simulado
    theta = np.linspace(0, np.pi, 100)
    r = 1

    ax1.plot(r * np.cos(theta), r * np.sin(theta), "k-", linewidth=3)

    # Sectores de colores con rangos específicos
    theta_red = np.linspace(0, np.pi / 3, 50)  # 0-15%: Zona Roja
    theta_yellow = np.linspace(np.pi / 3, 2 * np.pi / 3, 50)  # 15-25%: Zona Amarilla
    theta_green = np.linspace(2 * np.pi / 3, np.pi, 50)  # 25%+: Zona Verde

    ax1.fill_between(
        0.8 * np.cos(theta_red),
        0.8 * np.sin(theta_red),
        np.cos(theta_red),
        np.sin(theta_red),
        color="red",
        alpha=0.3,
        label="Zona Roja: TIR < 15%",
    )
    ax1.fill_between(
        0.8 * np.cos(theta_yellow),
        0.8 * np.sin(theta_yellow),
        np.cos(theta_yellow),
        np.sin(theta_yellow),
        color="yellow",
        alpha=0.3,
        label="Zona Amarilla: 15-25%",
    )
    ax1.fill_between(
        0.8 * np.cos(theta_green),
        0.8 * np.sin(theta_green),
        np.cos(theta_green),
        np.sin(theta_green),
        color="green",
        alpha=0.3,
        label="Zona Verde: TIR > 25%",
    )

    # Aguja indicadora
    if tir_valor <= 15:
        angle = np.pi * (1 - tir_valor / 30)  # 0-15% mapear a pi a 2pi/3
        zona_actual = "ROJA"
    elif tir_valor <= 25:
        angle = (
            np.pi * (2 / 3) * (1 - (tir_valor - 15) / 15)
        )  # 15-25% mapear a 2pi/3 a pi/3
        zona_actual = "AMARILLA"
    else:
        angle = np.pi / 6  # >25%
        zona_actual = "VERDE"

    ax1.arrow(
        0,
        0,
        0.7 * np.cos(angle),
        0.7 * np.sin(angle),
        head_width=0.05,
        head_length=0.05,
        fc="black",
        ec="black",
        linewidth=3,
    )

    ax1.text(
        0,
        -0.3,
        f"TIR\n{tir_valor:.1f}%",
        ha="center",
        va="center",
        fontsize=12,
        fontweight="bold",
    )
    ax1.text(
        0,
        -0.5,
        f"Zona {zona_actual}",
        ha="center",
        va="center",
        fontsize=10,
        color=(
            "red"
            if zona_actual == "ROJA"
            else "orange" if zona_actual == "AMARILLA" else "green"
        ),
        fontweight="bold",
    )
    ax1.set_xlim(-1.2, 1.2)
    ax1.set_ylim(-0.6, 1.2)
    ax1.set_aspect("equal")
    ax1.axis("off")

    # 2. VPN Indicador
    vpn_valor = indicadores.get("vpn", 0)
    color_vpn = "green" if vpn_valor > 0 else "red"

    ax2.bar(["VPN"], [vpn_valor], color=color_vpn, alpha=0.7)
    ax2.axhline(y=0, color="black", linewidth=2)
    ax2.text(
        0,
        vpn_valor + abs(vpn_valor) * 0.1,
        f"${vpn_valor:,.0f}",
        ha="center",
        va="bottom" if vpn_valor > 0 else "top",
        fontweight="bold",
    )
    ax2.set_ylabel("VPN ($)")
    ax2.set_title("VPN del Proyecto", fontweight="bold")

    # 3. ROI Indicador
    roi_valor = indicadores.get("roi", 0)
    color_roi = "green" if roi_valor > 0 else "red"

    ax3.bar(["ROI"], [roi_valor], color=color_roi, alpha=0.7)
    ax3.axhline(y=0, color="black", linewidth=2)
    ax3.text(
        0,
        roi_valor + abs(roi_valor) * 0.1,
        f"{roi_valor:.1f}%",
        ha="center",
        va="bottom" if roi_valor > 0 else "top",
        fontweight="bold",
    )
    ax3.set_ylabel("ROI (%)")
    ax3.set_title("ROI del Proyecto", fontweight="bold")

    # 4. Tabla resumen
    periodo_recup = indicadores.get("periodo_recuperacion", {})

    tabla_data = [
        ["Inversión Inicial", f"${proyecto.inversion_inicial:,.0f}"],
        ["TIR", f"{tir_valor:.2f}%" if tir_valor else "No calculable"],
        ["VPN", f"${vpn_valor:,.0f}"],
        ["ROI", f"{roi_valor:.1f}%"],
        ["Período Recuperación", f"{periodo_recup.get('meses', 0):.1f} meses"],
        ["Estado", "VIABLE" if tir_valor > 15 and vpn_valor > 0 else "REVISAR"],
    ]

    # Crear tabla
    ax_tabla.axis("tight")
    ax_tabla.axis("off")

    tabla = ax_tabla.table(
        cellText=tabla_data,
        colLabels=["Métrica", "Valor"],
        cellLoc="center",
        loc="center",
        colWidths=[0.4, 0.6],
    )

    tabla.auto_set_font_size(False)
    tabla.set_fontsize(12)
    tabla.scale(1, 2)

    # Colorear filas
    for i, row in enumerate(tabla_data):
        if row[0] == "Estado":
            color = "lightgreen" if row[1] == "VIABLE" else "lightcoral"
            tabla[(i + 1, 0)].set_facecolor(color)
            tabla[(i + 1, 1)].set_facecolor(color)

    # 5. NUEVA SECCIÓN: Explicación de zonas del velocímetro
    ax_explicacion.axis("off")

    explicacion_texto = f"""
INTERPRETACIÓN DEL VELOCÍMETRO TIR:

🔴 ZONA ROJA (0-15%): Proyecto de ALTO RIESGO
   • La TIR es inferior al costo de capital típico
   • Requiere reevaluación completa del proyecto
   • Considerar cambios estructurales o abandono

🟡 ZONA AMARILLA (15-25%): Proyecto MARGINAL  
   • TIR aceptable pero requiere análisis adicional
   • Revisar supuestos y realizar análisis de sensibilidad
   • Evaluar mejoras operativas

🟢 ZONA VERDE (>25%): Proyecto ATRACTIVO
   • TIR superior a expectativas del mercado
   • Proyecto financieramente viable
   • Recomendado para ejecución

RESULTADO ACTUAL: Su proyecto se encuentra en la ZONA {zona_actual}
"""

    ax_explicacion.text(
        0.05,
        0.95,
        explicacion_texto,
        transform=ax_explicacion.transAxes,
        fontsize=10,
        verticalalignment="top",
        fontfamily="monospace",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8),
    )

    plt.suptitle(
        "Dashboard Ejecutivo - Análisis Financiero", fontsize=16, fontweight="bold"
    )
    plt.tight_layout()

    return fig
