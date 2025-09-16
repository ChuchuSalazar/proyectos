"""
Módulo de Cálculos Financieros para Evaluación de Proyectos - ACTUALIZADO
Implementa cálculos según mejores prácticas financieras.

CAMBIOS CLAVE:
- TIR (IRR) con metodología de Excel:
  * Método: Newton–Raphson
  * guess por defecto: 10%
  * Convergencia: |Δr| <= 1e-7 (~0,00001%)
  * Máximo: 20 iteraciones (#NUM! si no converge -> aquí None)
  * La inversión inicial se pasa en POSITIVO desde la app y aquí se convierte a flujo NEGATIVO (t=0)
- Se mantiene la MISMA firma del método público calcular_tir(self, flujos_efectivo, inversion_inicial, max_iteraciones=1000)
  con parámetros keyword-only opcionales para controlar salida por "periodo" (Excel puro) o "anual" ((1+r)^m - 1).
- Corrección en analisis_sensibilidad (armado correcto de matrices).
- Validación de flujos para TIR al estilo Excel (al menos un flujo + y uno -).

Referencias:
- Microsoft IRR: método iterativo, 20 intentos, precisión 0,00001%, guess=10%.
- Apache POI IRR: Newton–Raphson, 20 iteraciones, 0,00001%.
"""

import numpy as np
import pandas as pd
import math
import warnings


class ProyectoInversion:
    """
    Clase principal para manejo de proyectos de inversión
    Implementa cálculos de TIR, VPN, ROI y análisis financiero
    """

    def __init__(self):
        """Inicializar proyecto con valores por defecto"""
        self.inversion_inicial = 0
        self.meses_preoperativos = 0
        self.distribucion_preoperativa = {}
        self.saldos_preoperativos = []
        self.configuracion_ingresos = {}
        self.configuracion_egresos = {}
        self.flujo_efectivo = []
        self.ingresos_operativos = []
        self.egresos_operativos = []
        self.indicadores = {}

    # ---------------------------
    # Fase preoperativa / proyecciones
    # ---------------------------
    def calcular_saldos_preoperativos(self, inversion, meses, distribucion):
        """
        Calcula saldos mensuales durante fase preoperativa
        """
        saldo_acumulado = inversion
        saldos = []
        for mes in range(1, meses + 1):
            erogacion = distribucion.get(mes, 0)
            saldo_acumulado -= erogacion
            saldos.append(
                {
                    "mes": mes,
                    "erogacion_mes": erogacion,
                    "erogacion_acumulada": inversion - saldo_acumulado,
                    "saldo_disponible": saldo_acumulado,
                    "porcentaje_ejecutado": (
                        ((inversion - saldo_acumulado) / inversion) * 100
                        if inversion > 0
                        else 0
                    ),
                }
            )
        return saldos

    def calcular_ingresos_operativos(self, config_ingresos, meses_operativos):
        """
        Calcula proyección de ingresos operativos mensuales
        """
        # Extraer parámetros
        multas_diarias = config_ingresos["multas_diarias"]
        valor_multa_descuento = config_ingresos["valor_multa_descuento"]
        pct_pago_voluntario = config_ingresos["pct_pago_voluntario"]
        pct_ingreso_operativo = config_ingresos["pct_ingreso_operativo"]
        tasa_variacion = config_ingresos.get("tasa_variacion", 0)

        # Cálculos base
        multas_mensuales = multas_diarias * 30
        ingresos_totales_teoricos = multas_mensuales * valor_multa_descuento
        pago_voluntario_teorico = ingresos_totales_teoricos * (
            pct_pago_voluntario / 100
        )
        ingreso_operativo_base = pago_voluntario_teorico * (pct_ingreso_operativo / 100)

        # Detalle de cálculo
        detalle = {
            "multas_mensuales": multas_mensuales,
            "ingresos_totales_teoricos": ingresos_totales_teoricos,
            "pago_voluntario_teorico": pago_voluntario_teorico,
            "ingreso_operativo_base": ingreso_operativo_base,
        }

        # Proyección mensual con variabilidad
        ingresos_mensuales = []
        np.random.seed(42)  # reproducibilidad
        for mes in range(meses_operativos):
            # Factor de crecimiento/decrecimiento
            factor_variacion = (1 + (tasa_variacion / 100)) ** mes
            # Ruido estocástico pequeño (±2%)
            factor_estocastico = np.random.normal(1, 0.02)
            ingreso_mes = ingreso_operativo_base * factor_variacion * factor_estocastico
            ingresos_mensuales.append(max(1000, ingreso_mes))  # mínimo $1,000

        return ingresos_mensuales, ingreso_operativo_base, detalle

    def calcular_egresos_operativos(
        self, egresos_base, meses_operativos, tasa_variacion
    ):
        """
        Calcula proyección de egresos operativos mensuales
        """
        total_egresos_base = sum(egresos_base.values())
        egresos_mensuales = []
        detalle_conceptos = []
        np.random.seed(42)  # reproducibilidad

        for mes in range(meses_operativos):
            factor_variacion = (1 + (tasa_variacion / 100)) ** mes
            egresos_mes_detalle = {}
            total_mes = 0
            for concepto, monto_base in egresos_base.items():
                if "personal" in concepto.lower() or "sueldo" in concepto.lower():
                    factor_estocastico = np.random.normal(1, 0.01)
                else:
                    factor_estocastico = np.random.normal(1, 0.03)
                monto_mes = monto_base * factor_variacion * factor_estocastico
                egresos_mes_detalle[concepto] = max(0, monto_mes)
                total_mes += monto_mes

            egresos_mensuales.append(max(1000, total_mes))  # mínimo $1,000
            detalle_conceptos.append(egresos_mes_detalle)

        return egresos_mensuales, total_egresos_base, detalle_conceptos

    # ---------------------------
    # TIR estilo Excel
    # ---------------------------
    def _tir_excel_newton(self, valores, guess=0.10, tolerancia=1e-7, iter_max=20):
        """
        Replica el algoritmo de Excel para IRR (TIR periódica):
          - Método: Newton–Raphson
          - guess por defecto: 10%
          - Convergencia: |r_nuevo - r| <= 1e-7 (~0,00001%)
          - Iteraciones máximas: 20 (si no converge, Excel da #NUM!; aquí devolvemos None)

        Reglas de Excel: la serie debe contener al menos un flujo positivo y uno negativo.
        Referencias:
          * Microsoft IRR: iterativa, 20 intentos, precisión 0,00001%, guess 10%.
          * Apache POI IRR (compatibilidad Excel) usa los mismos parámetros.
        """
        # Validación estilo Excel
        if not any(v > 0 for v in valores) or not any(v < 0 for v in valores):
            return None

        r = float(guess)
        EPS = 1e-12

        for _ in range(int(iter_max)):
            if r <= -1 + 1e-12:
                r = -1 + 1e-12  # evita (1+r)<=0

            # NPV y derivada
            try:
                npv = 0.0
                dnpv = 0.0
                for t, cf in enumerate(valores):
                    denom = (1.0 + r) ** t
                    npv += cf / denom
                    if t > 0:
                        dnpv += -t * cf / ((1.0 + r) ** (t + 1))
            except OverflowError:
                return None

            if abs(dnpv) < EPS:
                return None  # #NUM! en Excel

            r_nuevo = r - npv / dnpv

            # Convergencia "Excel-like"
            if abs(r_nuevo - r) <= tolerancia:
                return r_nuevo  # TIR por período (como IRR en Excel)

            r = r_nuevo

        # No convergió en iter_max -> #NUM!
        return None

    def calcular_tir(
        self,
        flujos_efectivo,
        inversion_inicial,
        max_iteraciones=1000,
        *,
        guess=0.10,
        devolver="anual",  # "periodo" (Excel puro) o "anual" ((1+r)^m - 1). Por defecto ANUAL para no romper reportes previos
        periodos_por_anio=12,
        excel_compatible=True,  # fuerza 20 iteraciones y tolerancia 1e-7
    ):
        """
        TIR al estilo Excel manteniendo la firma usada por main_app.

        Posicionales (compatibilidad):
          - flujos_efectivo: lista de flujos por período (t=1..n)
          - inversion_inicial: monto POSITIVO (se convierte a flujo NEGATIVO en t=0)
          - max_iteraciones: aceptado por compatibilidad; si excel_compatible=True, se limita a 20

        Keyword-only:
          - guess: 0.10 como en Excel
          - devolver: "periodo" (igual Excel) o "anual" (anualizada)
          - periodos_por_anio: 12 si flujos mensuales
          - excel_compatible: True para (iter_max=20, tolerancia=1e-7)

        Devuelve:
          - r_periodo si devolver="periodo"
          - (1+r_periodo)^(periodos_por_anio) - 1 si devolver="anual"
          - None si no converge (#NUM! en Excel)
        """
        # Serie al estilo Excel: [-inversión] + flujos
        valores = [-abs(inversion_inicial)] + list(flujos_efectivo)

        # Parámetros de iteración "Excel"
        if excel_compatible:
            iter_max = min(20, int(max_iteraciones))  # Excel usa 20 intentos
            tolerancia = 1e-7  # 0,00001%
        else:
            iter_max = int(max_iteraciones)
            tolerancia = 1e-10

        r_periodo = self._tir_excel_newton(
            valores=valores, guess=guess, tolerancia=tolerancia, iter_max=iter_max
        )

        if r_periodo is None:
            return None  # #NUM! en Excel

        if devolver == "periodo":
            return r_periodo  # igual que Excel: tasa por período
        else:
            # Mantener compatibilidad: devolver anualizado por defecto
            return (1.0 + r_periodo) ** periodos_por_anio - 1.0

    # ---------------------------
    # Otros indicadores
    # ---------------------------
    def calcular_vpn(self, flujos_efectivo, inversion_inicial, tasa_descuento_anual):
        """
        Calcula Valor Presente Neto (VPN)
        Nota: Se asume tasa_descuento_anual y flujos Mensuales -> se convierte a tasa mensual.
        """
        if not flujos_efectivo or inversion_inicial <= 0:
            return 0

        # Convertir tasa anual a mensual
        tasa_mensual = (1 + tasa_descuento_anual) ** (1 / 12) - 1

        # Inversión inicial negativa
        vpn = -abs(inversion_inicial)
        for i, flujo in enumerate(flujos_efectivo, 1):
            try:
                valor_presente = flujo / ((1 + tasa_mensual) ** i)
                vpn += valor_presente
            except (ZeroDivisionError, OverflowError):
                break
        return vpn

    def calcular_roi(self, flujos_efectivo, inversion_inicial):
        """
        Calcula Return on Investment
        """
        if not flujos_efectivo or inversion_inicial <= 0:
            return 0
        beneficio_total = sum(flujos_efectivo)
        roi = ((beneficio_total - inversion_inicial) / inversion_inicial) * 100
        return roi

    def calcular_periodo_recuperacion(self, flujos_efectivo, inversion_inicial):
        """
        Calcula período de recuperación de la inversión
        """
        if not flujos_efectivo or inversion_inicial <= 0:
            return {"recuperado": False, "meses": 0, "faltante": inversion_inicial}

        flujo_acumulado = 0
        for i, flujo in enumerate(flujos_efectivo, 1):
            flujo_acumulado += flujo
            if flujo_acumulado >= inversion_inicial:
                # Interpolación para precisión
                mes_anterior = i - 1
                flujo_anterior = flujo_acumulado - flujo
                diferencia = inversion_inicial - flujo_anterior
                fraccion_mes = diferencia / flujo if flujo > 0 else 0
                periodo_exacto = mes_anterior + fraccion_mes
                return {
                    "meses": max(0, periodo_exacto),
                    "años": max(0, periodo_exacto / 12),
                    "recuperado": True,
                    "flujo_acumulado_final": flujo_acumulado,
                }

        return {
            "meses": len(flujos_efectivo),
            "años": len(flujos_efectivo) / 12,
            "recuperado": False,
            "flujo_acumulado_final": flujo_acumulado,
            "faltante": inversion_inicial - flujo_acumulado,
        }

    # ---------------------------
    # Sensibilidad
    # ---------------------------
    def analisis_sensibilidad(
        self, variaciones_ingresos, variaciones_egresos, tasa_descuento
    ):
        """
        Realiza análisis de sensibilidad multivariable
        Devuelve matrices [len(variaciones_egresos) x len(variaciones_ingresos)] de TIR y VPN
        """
        resultados = {
            "tir_matriz": [],
            "vpn_matriz": [],
            "variaciones_ing": variaciones_ingresos,
            "variaciones_egr": variaciones_egresos,
        }

        ingresos_base = self.ingresos_operativos or []
        egresos_base = self.egresos_operativos or []
        if not ingresos_base or not egresos_base:
            return resultados

        for var_egr in variaciones_egresos:
            fila_tir = []
            fila_vpn = []
            for var_ing in variaciones_ingresos:
                # Aplicar variaciones
                ingresos_ajustados = [
                    ing * (1 + var_ing / 100) for ing in ingresos_base
                ]
                egresos_ajustados = [egr * (1 + var_egr / 100) for egr in egresos_base]
                flujos_ajustados = [
                    ing - egr for ing, egr in zip(ingresos_ajustados, egresos_ajustados)
                ]

                # Calcular indicadores (TIR estilo Excel y VPN)
                tir_ajustada = self.calcular_tir(
                    flujos_ajustados, self.inversion_inicial, devolver="periodo"
                )
                vpn_ajustado = self.calcular_vpn(
                    flujos_ajustados, self.inversion_inicial, tasa_descuento
                )

                fila_tir.append(tir_ajustada or 0)
                fila_vpn.append(vpn_ajustado)

            resultados["tir_matriz"].append(fila_tir)
            resultados["vpn_matriz"].append(fila_vpn)

        return resultados

    # ---------------------------
    # Utilidades / debug
    # ---------------------------
    def validar_flujos_para_tir(self, flujos_efectivo, inversion_inicial):
        """
        Valida que los flujos sean apropiados para calcular TIR al estilo Excel:
        - Debe haber al menos un flujo positivo y uno negativo en la serie completa.
        """
        if not flujos_efectivo:
            return False, "No hay flujos de efectivo"
        if inversion_inicial <= 0:
            return False, "Inversión inicial debe ser positiva"

        flujos_completos = [-abs(inversion_inicial)] + list(flujos_efectivo)
        if not any(f > 0 for f in flujos_completos) or not any(
            f < 0 for f in flujos_completos
        ):
            return False, "Debe haber al menos un flujo positivo y uno negativo"

        return True, "Flujos válidos para TIR"

    def debug_tir(self, flujos_efectivo, inversion_inicial, *, periodos_por_anio=12):
        """
        Función de debug para analizar TIR
        """
        print(f"\n=== DEBUG TIR ===")
        print(f"Inversión inicial: ${inversion_inicial:,.2f}")
        print(f"Número de flujos: {len(flujos_efectivo)}")
        print(f"Primeros 5 flujos: {[f'{f:,.0f}' for f in flujos_efectivo[:5]]}")
        print(f"Suma de flujos: ${sum(flujos_efectivo):,.2f}")

        flujos_tir = [-abs(inversion_inicial)] + list(flujos_efectivo)
        print(f"Flujo para TIR: [{flujos_tir[0]:,.0f}, {flujos_tir[1]:,.0f}, ...]")

        es_valido, mensaje = self.validar_flujos_para_tir(
            flujos_efectivo, inversion_inicial
        )
        print(f"Validación: {es_valido} - {mensaje}")

        tir_periodo = self.calcular_tir(
            flujos_efectivo, inversion_inicial, devolver="periodo"
        )
        tir_anual = (
            (1 + tir_periodo) ** periodos_por_anio - 1
            if tir_periodo is not None
            else None
        )

        if tir_periodo is not None:
            print(f"TIR período (Excel-like): {tir_periodo:.4%}")
            print(f"TIR anualizada         : {tir_anual:.4%}")
        else:
            print("TIR: No calculable (#NUM!)")
        print(f"=================\n")
        return tir_periodo
