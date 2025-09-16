import numpy as np
import pandas as pd
import math
import warnings


class ProyectoInversion:
    """
    Clase principal para manejo de proyectos de inversión
    Implementa cálculos de TIR, VPN, ROI y análisis financiero según metodología Excel
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

    def calcular_saldos_preoperativos_con_costos(
        self, inversion, meses, distribucion, costos
    ):
        """
        Calcula saldos mensuales durante fase preoperativa:
        Inversión Inicial fraccionada - Costos Operativos = Disponible Neto.
        El saldo final acumulado es la suma de los disponibles netos.
        También calcula el % amortizado y el saldo a retornar.
        """
        saldos = []
        saldo_final_acumulado = 0

        # Distribuir costos uniformemente
        costo_mes = sum(costos.values()) / meses if costos else 0

        for mes in range(1, meses + 1):
            inversion_mes = distribucion.get(mes, 0)
            disponible_neto = inversion_mes - costo_mes
            saldo_final_acumulado += disponible_neto

            porcentaje_amortizado = (saldo_final_acumulado / inversion) * 100

            saldos.append(
                {
                    "mes": mes,
                    "inversion_inicial_mes": round(inversion_mes, 2),
                    "costos_operativos_mes": round(costo_mes, 2),
                    "disponible_neto_mes": round(disponible_neto, 2),
                    "saldo_final_acumulado": round(saldo_final_acumulado, 2),
                    "porcentaje_amortizado": round(porcentaje_amortizado, 2),
                }
            )

        return saldos, round(saldo_final_acumulado, 2)

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
        Calcula proyección de ingresos operativos mensuales - VERSIÓN CORREGIDA
        SIN variabilidad estocástica no autorizada
        """
        # Extraer parámetros
        multas_diarias = config_ingresos['multas_diarias']
        valor_multa_descuento = config_ingresos['valor_multa_descuento']
        pct_pago_voluntario = config_ingresos['pct_pago_voluntario']
        pct_ingreso_operativo = config_ingresos['pct_ingreso_operativo']
        tasa_variacion = config_ingresos.get('tasa_variacion', 0)  # RESPETA EL 0%
    
        # Cálculos base
        multas_mensuales = multas_diarias * 30
        ingresos_totales_teoricos = multas_mensuales * valor_multa_descuento
        pago_voluntario_teorico = ingresos_totales_teoricos * (pct_pago_voluntario / 100)
        ingreso_operativo_base = pago_voluntario_teorico * (pct_ingreso_operativo / 100)
    
        # Detalle de cálculo
        detalle = {
            'multas_mensuales': multas_mensuales,
            'ingresos_totales_teoricos': ingresos_totales_teoricos,
            'pago_voluntario_teorico': pago_voluntario_teorico,
            'ingreso_operativo_base': ingreso_operativo_base
        }
    
        # CORRECCIÓN: Proyección DETERMINÍSTICA según tasa de variación
        ingresos_mensuales = []
    
        for mes in range(meses_operativos):
            if tasa_variacion == 0:
                # CASO 1: Sin variación = ingresos constantes
                ingreso_mes = ingreso_operativo_base
            else:
                # CASO 2: Con variación = crecimiento/decrecimiento lineal por período
                factor_variacion = (1 + (tasa_variacion / 100)) ** mes
                ingreso_mes = ingreso_operativo_base * factor_variacion
        
            ingresos_mensuales.append(round(ingreso_mes, 2))
    
        return ingresos_mensuales, ingreso_operativo_base, detalle

    def calcular_egresos_operativos(self, egresos_base, meses_operativos, tasa_variacion):
        """
        Calcula proyección de egresos operativos mensuales - VERSIÓN CORREGIDA
        SIN variabilidad estocástica no autorizada
        """
        total_egresos_base = sum(egresos_base.values())
        egresos_mensuales = []
        detalle_conceptos = []
    
        for mes in range(meses_operativos):
            if tasa_variacion == 0:
                # CASO 1: Sin variación = egresos constantes
                total_mes = total_egresos_base
            
                # Detalle por concepto (proporcional)
                egresos_mes_detalle = {}
                for concepto, monto_base in egresos_base.items():
                    egresos_mes_detalle[concepto] = monto_base
            
            else:
                # CASO 2: Con variación = crecimiento/decrecimiento lineal por período
                factor_variacion = (1 + (tasa_variacion / 100)) ** mes
                total_mes = total_egresos_base * factor_variacion
            
                # Detalle por concepto (proporcional)
                egresos_mes_detalle = {}
                for concepto, monto_base in egresos_base.items():
                    monto_mes = monto_base * factor_variacion
                    egresos_mes_detalle[concepto] = round(monto_mes, 2)
        
            egresos_mensuales.append(round(total_mes, 2))
            detalle_conceptos.append(egresos_mes_detalle)
    
        return egresos_mensuales, total_egresos_base, detalle_conceptos

    def calcular_flujo_efectivo_completo(self, ingresos, egresos):
        """
        Calcula el flujo de efectivo neto mensual del proyecto.
        Retorna una lista con el flujo neto por cada mes.
        """
        if not ingresos or not egresos or len(ingresos) != len(egresos):
            return []

        flujo_neto = [ing - egr for ing, egr in zip(ingresos, egresos)]

        # Si hay saldo preoperativo final, ajustarlo en el primer mes
        saldo_preop = getattr(self, "saldo_preoperativo_final", 0)
        if flujo_neto:
            flujo_neto[0] += saldo_preop

        return flujo_neto

    # ---------------------------
    # TIR estilo Excel EXACTO
    # ---------------------------
    def _convertir_flujos_si_necesario(self, flujos_efectivo, input_tipo="auto"):
        """
        Convierte flujos acumulados a flujos por período si es necesario

        Args:
            flujos_efectivo: Lista de flujos
            input_tipo: "periodo", "acumulado", "auto"

        Returns:
            list: Flujos por período
        """
        if input_tipo == "periodo":
            return list(flujos_efectivo)
        elif input_tipo == "acumulado":
            # Convertir acumulados a diferencias (flujos por período)
            if len(flujos_efectivo) <= 1:
                return list(flujos_efectivo)

            flujos_periodo = [flujos_efectivo[0]]  # Primer valor
            for i in range(1, len(flujos_efectivo)):
                flujo_periodo = flujos_efectivo[i] - flujos_efectivo[i - 1]
                flujos_periodo.append(flujo_periodo)
            return flujos_periodo
        else:  # auto
            # Detectar automáticamente si son acumulados
            if len(flujos_efectivo) > 3:
                # Si la mayoría de diferencias entre elementos consecutivos son pequeñas
                # comparadas con los valores absolutos, probablemente son acumulados
                diffs = [
                    abs(flujos_efectivo[i] - flujos_efectivo[i - 1])
                    for i in range(1, len(flujos_efectivo))
                ]
                values = [abs(x) for x in flujos_efectivo[1:]]

                # Si las diferencias promedio son menos del 20% de los valores promedio, asumir acumulados
                if (
                    np.mean(diffs) < 0.2 * np.mean(values)
                    if np.mean(values) > 0
                    else False
                ):
                    return self._convertir_flujos_si_necesario(
                        flujos_efectivo, "acumulado"
                    )

            return list(flujos_efectivo)  # Asumir que son por período

    def _tir_excel_newton(self, valores, guess=0.10, tolerancia=1e-7, iter_max=20):
        """
        Replica EXACTAMENTE el algoritmo de Excel para IRR (TIR periódica):
          - Método: Newton-Raphson
          - guess por defecto: 10%
          - Convergencia: |r_nuevo - r| <= 1e-7 (0.00001%)
          - Iteraciones máximas: 20 (si no converge, Excel da #NUM!)

        Validación Excel: la serie debe contener al menos un flujo positivo y uno negativo.
        """
        # Validación estilo Excel
        if not any(v > 0 for v in valores) or not any(v < 0 for v in valores):
            return None

        r = float(guess)
        EPS = 1e-12

        for iteracion in range(int(iter_max)):
            if r <= -1 + 1e-12:
                r = -1 + 1e-12  # evita (1+r)<=0

            # NPV y derivada
            try:
                npv = 0.0
                dnpv = 0.0
                for t, cf in enumerate(valores):
                    if t == 0:
                        npv += cf
                        # La derivada en t=0 es 0
                    else:
                        denom = (1.0 + r) ** t
                        npv += cf / denom
                        dnpv += -t * cf / ((1.0 + r) ** (t + 1))
            except (OverflowError, ZeroDivisionError):
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
        devolver="periodo",  # CAMBIO: "periodo" por defecto como Excel
        periodos_por_anio=12,
        excel_compatible=True,
        input_tipo="auto",
        validacion_estricta=True,
    ):
        """
        TIR según metodología EXACTA de Excel con mejoras robustas

        CORREGIDO: Devuelve TIR por período (mensual) por defecto como Excel IRR

        IMPLEMENTA TODOS LOS ASPECTOS REQUERIDOS:
        - Newton-Raphson con 20 iteraciones máximas
        - Guess 10%, tolerancia 1e-7 (0.00001%)
        - Conversión inversión POSITIVA → flujo NEGATIVO t=0
        - Manejo de flujos acumulados vs período
        - TIR por período (mensual) como Excel IRR por defecto

        Args:
            flujos_efectivo: lista de flujos por período (t=1..n)
            inversion_inicial: monto POSITIVO (se convierte a flujo NEGATIVO en t=0)

        Keyword-only:
            guess: 0.10 (10%) como en Excel
            devolver: "periodo" (DEFAULT - como Excel) o "anual" (anualizada)
            periodos_por_anio: 12 para flujos mensuales
            excel_compatible: True para parámetros Excel exactos
            input_tipo: "periodo", "acumulado", "auto"
            validacion_estricta: validaciones adicionales

        Returns:
            - TIR por período (mensual) si devolver="periodo" (DEFAULT)
            - TIR anualizada si devolver="anual"
            - None si no converge (#NUM! en Excel)
        """
        # PASO 1: Validaciones previas
        if validacion_estricta:
            if not flujos_efectivo or len(flujos_efectivo) == 0:
                return None
            if inversion_inicial <= 0:
                return None
            if any(pd.isna(f) for f in flujos_efectivo if pd is not None):
                return None

        # PASO 2: Convertir flujos si es necesario (acumulados → período)
        flujos_procesados = self._convertir_flujos_si_necesario(
            flujos_efectivo, input_tipo
        )

        # PASO 3: Crear serie estilo Excel: [-inversión] + flujos
        valores = [-abs(inversion_inicial)] + list(flujos_procesados)

        # PASO 4: Configurar parámetros según Excel
        if excel_compatible:
            iter_max = 20
            tolerancia = 1e-7
            guess_final = 0.10
        else:
            iter_max = min(max_iteraciones, 100)
            tolerancia = 1e-10
            guess_final = guess

        # PASO 5: Validación Excel estricta
        es_valido, mensaje = self.validar_flujos_para_tir(
            flujos_procesados, inversion_inicial
        )
        if not es_valido and validacion_estricta:
            return None

        # PASO 6: Calcular TIR usando Newton-Raphson Excel-compatible
        r_periodo = self._tir_excel_newton(
            valores=valores, guess=guess_final, tolerancia=tolerancia, iter_max=iter_max
        )

        if r_periodo is None:
            return None

        # PASO 7: Validación final del resultado
        if validacion_estricta:
            if abs(r_periodo) > 10.0:
                return None
            if r_periodo < -0.99:
                return None

        # PASO 8: Devolver según formato solicitado
        if devolver == "periodo":
            return r_periodo  # TIR por período (mensual) - COMO EXCEL IRR
        else:
            # Anualizada: (1+r_período)^períodos_por_año - 1
            try:
                tir_anual = (1.0 + r_periodo) ** periodos_por_anio - 1.0
                if validacion_estricta and abs(tir_anual) > 50:
                    return None
                return tir_anual
            except (OverflowError, ValueError):
                return None

    # ---------------------------
    # VPN método Excel EXACTO
    # ---------------------------
    def calcular_vpn(self, flujos_efectivo, inversion_inicial, tasa_descuento_anual):
        """
        Calcula VPN según metodología EXACTA de Excel:
        VPN = Σ(Flujo_t / (1+r_mensual)^t) - Inversión_Inicial

        Args:
            flujos_efectivo: Lista de flujos mensuales
            inversion_inicial: Inversión inicial (valor positivo)
            tasa_descuento_anual: Tasa de descuento anual (decimal)

        Returns:
            float: VPN calculado
        """
        if not flujos_efectivo or inversion_inicial <= 0:
            return 0

        # Convertir tasa anual a mensual: (1+r_anual)^(1/12) - 1
        tasa_mensual = (1 + tasa_descuento_anual) ** (1 / 12) - 1

        # Calcular VPN: -Inversión_inicial + Σ(Flujo_t / (1+r)^t)
        vpn = -abs(inversion_inicial)  # Inversión inicial negativa

        for t, flujo in enumerate(flujos_efectivo, 1):  # t=1,2,3...
            try:
                valor_presente = flujo / ((1 + tasa_mensual) ** t)
                vpn += valor_presente
            except (ZeroDivisionError, OverflowError):
                break

        return vpn

    # ---------------------------
    # ROI método estándar
    # ---------------------------
    def calcular_roi(self, flujos_efectivo, inversion_inicial):
        """
        Calcula ROI según fórmula estándar:
        ROI = ((Beneficio_Total - Inversión_Inicial) / Inversión_Inicial) * 100

        Args:
            flujos_efectivo: Lista de flujos de efectivo
            inversion_inicial: Inversión inicial

        Returns:
            float: ROI en porcentaje
        """
        if not flujos_efectivo or inversion_inicial <= 0:
            return 0

        beneficio_total = sum(flujos_efectivo)
        roi = ((beneficio_total - inversion_inicial) / inversion_inicial) * 100
        return roi

    def calcular_periodo_recuperacion(self, flujos_efectivo, inversion_inicial):
        """
        Calcula período de recuperación de la inversión (Payback Period)
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
    # Análisis de sensibilidad CORREGIDO
    # ---------------------------
    def analisis_sensibilidad(
        self, variaciones_ingresos, variaciones_egresos, tasa_descuento
    ):
        """
        Realiza análisis de sensibilidad multivariable CORREGIDO

        Returns:
            dict: Matrices [len(variaciones_egresos) x len(variaciones_ingresos)] de TIR y VPN
        """
        resultados = {
            "tir_matriz": [],
            "vpn_matriz": [],
            "variaciones_ing": variaciones_ingresos,
            "variaciones_egr": variaciones_egresos,
        }

        ingresos_base = getattr(self, "ingresos_operativos", [])
        egresos_base = getattr(self, "egresos_operativos", [])

        if not ingresos_base or not egresos_base:
            return resultados

        # Iterar por egresos (filas) y luego ingresos (columnas)
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

                # Calcular TIR (anualizada)
                tir_ajustada = self.calcular_tir(
                    flujos_ajustados,
                    self.inversion_inicial,
                    devolver="anual",
                    excel_compatible=True,
                )

                # Calcular VPN
                vpn_ajustado = self.calcular_vpn(
                    flujos_ajustados, self.inversion_inicial, tasa_descuento
                )

                fila_tir.append(tir_ajustada if tir_ajustada is not None else 0)
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
        tir_anual = self.calcular_tir(
            flujos_efectivo, inversion_inicial, devolver="anual"
        )

        if tir_periodo is not None:
            print(f"TIR período (Excel-like): {tir_periodo:.4%}")
            print(f"TIR anualizada         : {tir_anual:.4%}")
        else:
            print("TIR: No calculable (#NUM!)")
        print(f"=================\n")
        return tir_periodo
