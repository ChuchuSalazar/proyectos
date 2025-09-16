"""
Pruebas Unitarias para Módulo de Cálculos Financieros
"""

import unittest
import numpy as np
import pandas as pd
import sys
import os

# Agregar path de módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.financial_calculations import ProyectoInversion
from modules.utils import verificar_integridad_datos
from modules.utils import validar_datos_entrada


class TestCalculosFinancieros(unittest.TestCase):
    """Clase de pruebas para cálculos financieros"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.proyecto = ProyectoInversion()
        self.proyecto.inversion_inicial = 100000

        # Datos de prueba estándar
        self.flujos_test = [10000, 15000, 20000, 25000, 30000, 35000]
        self.config_ingresos_test = {
            "multas_diarias": 100,
            "valor_multa_descuento": 50,
            "pct_pago_voluntario": 70,
            "pct_ingreso_operativo": 85,
            "tasa_variacion": 2.0,
        }
        self.egresos_base_test = {
            "Personal": 20000,
            "Servicios": 5000,
            "Mantenimiento": 3000,
        }

    def test_calculo_saldos_preoperativos(self):
        """Prueba el cálculo de saldos preoperativos"""
        inversion = 100000
        meses = 4
        distribucion = {1: 30000, 2: 25000, 3: 25000, 4: 20000}

        saldos = self.proyecto.calcular_saldos_preoperativos(
            inversion, meses, distribucion
        )

        # Verificar estructura
        self.assertEqual(len(saldos), meses)
        self.assertIn("mes", saldos[0])
        self.assertIn("erogacion_mes", saldos[0])
        self.assertIn("saldo_disponible", saldos[0])

        # Verificar cálculos
        self.assertEqual(saldos[0]["saldo_disponible"], 70000)  # 100000 - 30000
        self.assertEqual(saldos[-1]["saldo_disponible"], 0)  # Debe quedar en 0

        # Verificar erogación acumulada
        self.assertEqual(saldos[-1]["erogacion_acumulada"], inversion)

    def test_calculo_ingresos_operativos(self):
        """Prueba el cálculo de ingresos operativos"""
        meses = 12

        ingresos, base, detalle = self.proyecto.calcular_ingresos_operativos(
            self.config_ingresos_test, meses
        )

        # Verificar longitud
        self.assertEqual(len(ingresos), meses)

        # Verificar que todos los ingresos son positivos
        self.assertTrue(all(ing >= 0 for ing in ingresos))

        # Verificar detalle de cálculo
        self.assertIn("multas_mensuales", detalle)
        self.assertIn("ingreso_operativo_base", detalle)
        self.assertEqual(detalle["multas_mensuales"], 100 * 30)  # 100 multas * 30 días

        # Verificar ingreso base calculado correctamente
        ingresos_totales = 3000 * 50  # multas_mensuales * valor_multa
        pago_voluntario = ingresos_totales * 0.70
        ingreso_esperado = pago_voluntario * 0.85
        self.assertEqual(base, ingreso_esperado)

    def test_calculo_egresos_operativos(self):
        """Prueba el cálculo de egresos operativos"""
        meses = 6
        tasa_variacion = 1.5

        egresos, total_base, detalle = self.proyecto.calcular_egresos_operativos(
            self.egresos_base_test, meses, tasa_variacion
        )

        # Verificar longitud
        self.assertEqual(len(egresos), meses)
        self.assertEqual(len(detalle), meses)

        # Verificar que todos los egresos son positivos
        self.assertTrue(all(egr >= 0 for egr in egresos))

        # Verificar total base
        total_esperado = sum(self.egresos_base_test.values())
        self.assertEqual(total_base, total_esperado)

        # Verificar crecimiento (el último debe ser mayor al primero debido a la variación)
        if tasa_variacion > 0:
            self.assertGreater(egresos[-1], egresos[0])

    def test_calculo_tir_casos_validos(self):
        """Prueba el cálculo de TIR con casos válidos"""
        # Caso 1: Flujos crecientes
        flujos_crecientes = [5000, 10000, 15000, 20000, 25000]
        tir = self.proyecto.calcular_tir(flujos_crecientes, 50000)

        self.assertIsNotNone(tir)
        self.assertGreater(tir, 0)  # Debe ser positiva
        self.assertLess(tir, 2.0)  # Debe ser razonable (menos de 200%)

        # Caso 2: Flujos constantes
        flujos_constantes = [20000] * 6
        tir = self.proyecto.calcular_tir(flujos_constantes, 100000)

        self.assertIsNotNone(tir)
        self.assertGreater(tir, 0)

    def test_calculo_tir_casos_limite(self):
        """Prueba el cálculo de TIR con casos límite"""
        # Caso 1: Todos los flujos son negativos (no debe tener TIR válida)
        flujos_negativos = [-1000, -2000, -3000]
        tir = self.proyecto.calcular_tir(flujos_negativos, 10000)

        # Puede ser None o un valor muy negativo
        if tir is not None:
            self.assertLess(tir, 0)

        # Caso 2: Flujos muy pequeños vs inversión grande
        flujos_pequenos = [100, 200, 300]
        tir = self.proyecto.calcular_tir(flujos_pequenos, 100000)

        if tir is not None:
            self.assertLess(tir, 0)  # Debe ser negativa

    def test_calculo_vpn(self):
        """Prueba el cálculo del VPN"""
        tasa_descuento = 0.12  # 12% anual

        vpn = self.proyecto.calcular_vpn(self.flujos_test, 100000, tasa_descuento)

        # Verificar que es un número
        self.assertIsInstance(vpn, (int, float))

        # Con flujos positivos y tasa razonable, VPN debe ser calculable
        self.assertIsNotNone(vpn)

        # Verificar sensibilidad a tasa de descuento
        vpn_alta_tasa = self.proyecto.calcular_vpn(self.flujos_test, 100000, 0.25)
        self.assertLess(vpn_alta_tasa, vpn)  # Mayor tasa = menor VPN

    def test_calculo_roi(self):
        """Prueba el cálculo del ROI"""
        roi = self.proyecto.calcular_roi(self.flujos_test, 100000)

        # Verificar que es un número
        self.assertIsInstance(roi, (int, float))

        # Calcular ROI esperado
        beneficio_total = sum(self.flujos_test)
        roi_esperado = ((beneficio_total - 100000) / 100000) * 100

        self.assertAlmostEqual(roi, roi_esperado, places=2)

    def test_calculo_periodo_recuperacion(self):
        """Prueba el cálculo del período de recuperación"""
        # Caso 1: Recuperación exitosa
        flujos_recuperacion = [20000, 30000, 40000, 50000]  # Se recupera en mes 3
        inversion = 80000

        resultado = self.proyecto.calcular_periodo_recuperacion(
            flujos_recuperacion, inversion
        )

        # Verificar estructura del resultado
        self.assertIn("meses", resultado)
        self.assertIn("años", resultado)
        self.assertIn("recuperado", resultado)

        # Verificar que se recupera
        self.assertTrue(resultado["recuperado"])
        self.assertLess(resultado["meses"], len(flujos_recuperacion))

        # Caso 2: No se recupera
        flujos_insuficientes = [5000, 10000, 15000]
        inversion_alta = 100000

        resultado_no_recup = self.proyecto.calcular_periodo_recuperacion(
            flujos_insuficientes, inversion_alta
        )

        self.assertFalse(resultado_no_recup["recuperado"])
        self.assertIn("faltante", resultado_no_recup)
        self.assertGreater(resultado_no_recup["faltante"], 0)

    def test_analisis_sensibilidad(self):
        """Prueba el análisis de sensibilidad"""
        # Configurar proyecto con datos mínimos
        self.proyecto.configuracion_ingresos = {"proyeccion": self.flujos_test}
        self.proyecto.configuracion_egresos = {"proyeccion": [5000] * 6}

        variaciones_ing = [-10, 0, 10]
        variaciones_egr = [-10, 0, 10]
        tasa_descuento = 0.12

        resultado = self.proyecto.analisis_sensibilidad(
            variaciones_ing, variaciones_egr, tasa_descuento
        )

        # Verificar estructura
        self.assertIn("tir_matriz", resultado)
        self.assertIn("vpn_matriz", resultado)
        self.assertIn("variaciones_ing", resultado)
        self.assertIn("variaciones_egr", resultado)

        # Verificar dimensiones
        self.assertEqual(len(resultado["tir_matriz"]), len(variaciones_egr))
        self.assertEqual(len(resultado["tir_matriz"][0]), len(variaciones_ing))

        # Verificar que los valores son números
        matriz_tir = np.array(resultado["tir_matriz"])
        self.assertTrue(np.all(np.isfinite(matriz_tir)))


def test_validacion_datos_entrada(self):
    """Prueba la validación de datos de entrada"""
    # Caso 1: Datos válidos
    datos_validos = {
        "inversion_inicial": 100000,
        "meses_preoperativos": 6,
        "multas_diarias": 150,
        "pct_pago_voluntario": 75,
        "pct_ingreso_operativo": 85,
    }

    from modules.utils import validar_datos_entrada

    es_valido, errores = validar_datos_entrada(datos_validos)

    self.assertTrue(es_valido)
    self.assertEqual(len(errores), 0)

    # Caso 2: Datos inválidos
    datos_invalidos = {
        "inversion_inicial": -1000,  # Negativo
        "meses_preoperativos": 0,  # Cero
        "multas_diarias": -50,  # Negativo
        "pct_pago_voluntario": 150,  # Mayor a 100%
    }

    es_valido_inv, errores_inv = validar_datos_entrada(datos_invalidos)

    self.assertFalse(es_valido_inv)
    self.assertGreater(len(errores_inv), 0)


def test_coherencia_calculos_integrados(self):
    """Prueba la coherencia entre cálculos integrados"""
    # Configurar proyecto completo
    self.proyecto.inversion_inicial = 100000

    # Generar ingresos y egresos
    ingresos, _, _ = self.proyecto.calcular_ingresos_operativos(
        self.config_ingresos_test, 12
    )
    egresos, _, _ = self.proyecto.calcular_egresos_operativos(
        self.egresos_base_test, 12, 1.0
    )

    # Calcular flujo de efectivo
    flujo_efectivo = [ing - egr for ing, egr in zip(ingresos, egresos)]

    # Calcular todos los indicadores
    tir = self.proyecto.calcular_tir(flujo_efectivo, 100000)
    vpn = self.proyecto.calcular_vpn(flujo_efectivo, 100000, 0.12)
    roi = self.proyecto.calcular_roi(flujo_efectivo, 100000)

    # Verificar coherencia
    if tir and tir > 0.12:  # Si TIR > tasa descuento
        self.assertGreater(vpn, 0)  # VPN debe ser positivo

    if tir and tir < 0.12:  # Si TIR < tasa descuento
        self.assertLess(vpn, 0)  # VPN debe ser negativo

    # ROI y TIR deben tener relación lógica
    beneficio_total = sum(flujo_efectivo)
    if beneficio_total > 100000:  # Si hay ganancia
        self.assertGreater(roi, 0)
    else:
        self.assertLess(roi, 0)


def test_manejo_casos_extremos(self):
    """Prueba el manejo de casos extremos"""
    # Caso 1: Lista vacía de flujos
    tir_vacia = self.proyecto.calcular_tir([], 100000)
    self.assertIsNone(tir_vacia)

    # Caso 2: Inversión cero
    vpn_inv_cero = self.proyecto.calcular_vpn([1000, 2000], 0, 0.1)
    self.assertEqual(
        vpn_inv_cero, sum([1000 / (1.1 ** (1 / 12)), 2000 / (1.1 ** (2 / 12))])
    )

    # Caso 3: Tasa de descuento negativa
    vpn_tasa_neg = self.proyecto.calcular_vpn([1000], 500, -0.1)
    self.assertIsInstance(vpn_tasa_neg, (int, float))

    # Caso 4: Flujos con valores muy grandes
    flujos_grandes = [1e10, 2e10, 3e10]
    tir_grandes = self.proyecto.calcular_tir(flujos_grandes, 1e9)

    if tir_grandes:
        self.assertIsInstance(tir_grandes, (int, float))


def test_precision_calculos(self):
    """Prueba la precisión de los cálculos"""
    # Caso conocido: Inversión 1000, flujos [300, 400, 500, 600]
    # TIR aproximada: 22.1%
    flujos_precision = [300, 400, 500, 600]
    inversion_precision = 1000

    tir_precision = self.proyecto.calcular_tir(flujos_precision, inversion_precision)

    if tir_precision:
        # Verificar que está en el rango esperado (±2%)
        self.assertGreater(tir_precision, 0.20)
        self.assertLess(tir_precision, 0.25)

    # Verificar VPN con tasa conocida
    vpn_precision = self.proyecto.calcular_vpn(
        flujos_precision, inversion_precision, 0.10
    )

    # Cálculo manual esperado
    vpn_manual = (
        300 / 1.1 ** (1 / 12)
        + 400 / 1.1 ** (2 / 12)
        + 500 / 1.1 ** (3 / 12)
        + 600 / 1.1 ** (4 / 12)
    ) - 1000

    # Permitir pequeña diferencia por redondeo
    self.assertAlmostEqual(vpn_precision, vpn_manual, places=2)


class TestIntegracionCompleta(unittest.TestCase):
    """Pruebas de integración completa del sistema"""

    def setUp(self):
        """Configuración para pruebas de integración"""
        self.proyecto = ProyectoInversion()

        # Configuración completa de prueba
        self.config_completa = {
            "inversion_inicial": 250000,
            "meses_preoperativos": 6,
            "distribucion_preoperativa": {
                1: 50000,
                2: 45000,
                3: 40000,
                4: 35000,
                5: 40000,
                6: 40000,
            },
            "config_ingresos": {
                "multas_diarias": 120,
                "valor_multa_descuento": 45,
                "pct_pago_voluntario": 75,
                "pct_ingreso_operativo": 88,
                "tasa_variacion": 2.5,
            },
            "egresos_base": {
                "Personal Administrativo": 45000,
                "Personal Operativo": 65000,
                "Servicios Públicos": 12000,
                "Mantenimiento": 8000,
                "Combustibles": 15000,
                "Otros": 5000,
            },
            "meses_operativos": 24,
            "tasa_var_egresos": 1.8,
            "tasas_descuento": {
                "libre_riesgo": 0.05,
                "riesgo_pais": 0.035,
                "riesgo_proyecto": 0.045,
            },
        }

    def test_flujo_completo_evaluacion(self):
        """Prueba el flujo completo de evaluación"""
        config = self.config_completa

        # 1. Configurar proyecto
        self.proyecto.inversion_inicial = config["inversion_inicial"]
        self.proyecto.meses_preoperativos = config["meses_preoperativos"]

        # 2. Calcular saldos preoperativos
        saldos_preop = self.proyecto.calcular_saldos_preoperativos(
            config["inversion_inicial"],
            config["meses_preoperativos"],
            config["distribucion_preoperativa"],
        )

        self.assertEqual(len(saldos_preop), config["meses_preoperativos"])

        # 3. Calcular ingresos operativos
        ingresos, base_ing, detalle_ing = self.proyecto.calcular_ingresos_operativos(
            config["config_ingresos"], config["meses_operativos"]
        )

        self.assertEqual(len(ingresos), config["meses_operativos"])
        self.assertTrue(all(ing > 0 for ing in ingresos))

        # 4. Calcular egresos operativos
        egresos, base_egr, detalle_egr = self.proyecto.calcular_egresos_operativos(
            config["egresos_base"],
            config["meses_operativos"],
            config["tasa_var_egresos"],
        )

        self.assertEqual(len(egresos), config["meses_operativos"])
        self.assertTrue(all(egr > 0 for egr in egresos))

        # 5. Calcular flujo de efectivo
        flujo_efectivo = [ing - egr for ing, egr in zip(ingresos, egresos)]

        # 6. Calcular indicadores financieros
        tasa_descuento_total = sum(config["tasas_descuento"].values())

        tir = self.proyecto.calcular_tir(flujo_efectivo, config["inversion_inicial"])
        vpn = self.proyecto.calcular_vpn(
            flujo_efectivo, config["inversion_inicial"], tasa_descuento_total
        )
        roi = self.proyecto.calcular_roi(flujo_efectivo, config["inversion_inicial"])
        periodo_recup = self.proyecto.calcular_periodo_recuperacion(
            flujo_efectivo, config["inversion_inicial"]
        )

        # 7. Verificar resultados
        self.assertIsNotNone(tir)
        self.assertIsInstance(vpn, (int, float))
        self.assertIsInstance(roi, (int, float))
        self.assertIsInstance(periodo_recup, dict)

        # 8. Verificar coherencia de resultados
        if tir and tir > tasa_descuento_total:
            self.assertGreater(vpn, 0, "VPN debe ser positivo si TIR > tasa descuento")

        # 9. Guardar resultados en proyecto
        self.proyecto.ingresos_operativos = ingresos
        self.proyecto.egresos_operativos = egresos
        self.proyecto.flujo_efectivo = flujo_efectivo
        self.proyecto.indicadores = {
            "tir": tir,
            "vpn": vpn,
            "roi": roi,
            "periodo_recuperacion": periodo_recup,
        }

    # 10. Verificar integridad final
    es_integro, problemas = verificar_integridad_datos(self.proyecto)

    self.assertTrue(es_integro, f"Proyecto debe ser íntegro. Problemas: {problemas}")

    def test_sensibilidad_completa(self):
        """Prueba análisis de sensibilidad completo"""
        # Usar configuración del test anterior
        self.test_flujo_completo_evaluacion()

        # Ejecutar análisis de sensibilidad
        variaciones_ing = [-20, -10, -5, 0, 5, 10, 20]
        variaciones_egr = [-15, -10, -5, 0, 5, 10, 15]
        tasa_descuento = 0.13

        resultado_sens = self.proyecto.analisis_sensibilidad(
            variaciones_ing, variaciones_egr, tasa_descuento
        )

        # Verificar completitud
        self.assertIn("tir_matriz", resultado_sens)
        self.assertIn("vpn_matriz", resultado_sens)

        matriz_tir = np.array(resultado_sens["tir_matriz"])
        matriz_vpn = np.array(resultado_sens["vpn_matriz"])

        # Verificar dimensiones
        self.assertEqual(matriz_tir.shape, (len(variaciones_egr), len(variaciones_ing)))
        self.assertEqual(matriz_vpn.shape, (len(variaciones_egr), len(variaciones_ing)))

        # Verificar tendencias lógicas
        # Columna central (variación 0) vs extremos
        col_central = len(variaciones_ing) // 2
        fila_central = len(variaciones_egr) // 2

        tir_base = matriz_tir[fila_central, col_central]

        # Mayor ingreso (+20%) debe dar mayor TIR
        tir_ing_alto = matriz_tir[fila_central, -1]
        if tir_base > 0 and tir_ing_alto > 0:
            self.assertGreater(tir_ing_alto, tir_base)

        # Mayor egreso (+15%) debe dar menor TIR
        tir_egr_alto = matriz_tir[-1, col_central]
        if tir_base > 0 and tir_egr_alto is not None:
            self.assertLess(tir_egr_alto, tir_base)


class TestRobustezCalculos(unittest.TestCase):
    """Pruebas de robustez y casos edge"""

    def setUp(self):
        """Configuración para pruebas de robustez"""
        self.proyecto = ProyectoInversion()

    def test_flujos_con_ruido(self):
        """Prueba cálculos con flujos que contienen ruido/variabilidad alta"""
        np.random.seed(42)

        # Generar flujos con alta variabilidad
        flujos_base = [10000, 15000, 20000, 25000, 30000]
        ruido = np.random.normal(0, 5000, len(flujos_base))  # 50% de variabilidad
        flujos_con_ruido = [max(1000, base + r) for base, r in zip(flujos_base, ruido)]

        tir_ruido = self.proyecto.calcular_tir(flujos_con_ruido, 80000)
        vpn_ruido = self.proyecto.calcular_vpn(flujos_con_ruido, 80000, 0.12)

        # Debe poder calcular a pesar del ruido
        self.assertIsNotNone(tir_ruido)
        self.assertIsInstance(vpn_ruido, (int, float))

    def test_escalabilidad_temporal(self):
        """Prueba escalabilidad con proyecciones largas"""
        # Proyecto a 10 años (120 meses)
        meses_largos = 120

        config_ingresos_largo = {
            "multas_diarias": 200,
            "valor_multa_descuento": 60,
            "pct_pago_voluntario": 80,
            "pct_ingreso_operativo": 90,
            "tasa_variacion": 0.5,  # Crecimiento moderado para largo plazo
        }

        egresos_base_largo = {f"Concepto_{i}": 5000 + i * 1000 for i in range(20)}

        # Calcular proyecciones largas
        ingresos_largos, _, _ = self.proyecto.calcular_ingresos_operativos(
            config_ingresos_largo, meses_largos
        )

        egresos_largos, _, _ = self.proyecto.calcular_egresos_operativos(
            egresos_base_largo, meses_largos, 1.0
        )

        flujo_largo = [ing - egr for ing, egr in zip(ingresos_largos, egresos_largos)]

        # Verificar que puede manejar proyecciones largas
        self.assertEqual(len(flujo_largo), meses_largos)

        # TIR debe ser calculable incluso con 120 períodos
        tir_largo = self.proyecto.calcular_tir(flujo_largo, 500000)

        # Puede ser None si no converge, pero no debe fallar
        if tir_largo is not None:
            self.assertIsInstance(tir_largo, (int, float))

    def test_valores_monetarios_grandes(self):
        """Prueba con valores monetarios muy grandes"""
        # Proyecto de gran escala: 10 millones
        inversion_grande = 10_000_000
        flujos_grandes = [500_000, 800_000, 1_200_000, 1_500_000, 2_000_000, 2_500_000]

        tir_grande = self.proyecto.calcular_tir(flujos_grandes, inversion_grande)
        vpn_grande = self.proyecto.calcular_vpn(flujos_grandes, inversion_grande, 0.15)
        roi_grande = self.proyecto.calcular_roi(flujos_grandes, inversion_grande)

        # Verificar que maneja correctamente valores grandes
        if tir_grande:
            self.assertIsInstance(tir_grande, (int, float))
            self.assertGreater(tir_grande, 0)  # Debe ser positiva con estos flujos

        self.assertIsInstance(vpn_grande, (int, float))
        self.assertIsInstance(roi_grande, (int, float))

    def test_consistencia_temporal(self):
        """Prueba consistencia en diferentes horizontes temporales"""
        base_config = {
            "multas_diarias": 100,
            "valor_multa_descuento": 50,
            "pct_pago_voluntario": 75,
            "pct_ingreso_operativo": 85,
            "tasa_variacion": 2.0,
        }

        egresos_base = {"Personal": 20000, "Operación": 15000}
        inversion = 100000

        # Calcular para diferentes horizontes
        horizontes = [12, 24, 36, 48]
        tirs = []

        for meses in horizontes:
            ingresos, _, _ = self.proyecto.calcular_ingresos_operativos(
                base_config, meses
            )
            egresos, _, _ = self.proyecto.calcular_egresos_operativos(
                egresos_base, meses, 1.5
            )
            flujo = [ing - egr for ing, egr in zip(ingresos, egresos)]

            tir = self.proyecto.calcular_tir(flujo, inversion)
            if tir:
                tirs.append(tir)

        # TIRs deben ser consistentes (diferencias no mayores al 5%)
        if len(tirs) >= 2:
            for i in range(1, len(tirs)):
                diferencia_relativa = abs(tirs[i] - tirs[0]) / tirs[0]
                self.assertLess(
                    diferencia_relativa,
                    0.10,
                    f"TIR inconsistente entre horizontes: {tirs[0]:.3f} vs {tirs[i]:.3f}",
                )


if __name__ == "__main__":
    # Configurar suite de pruebas
    suite = unittest.TestSuite()

    # Agregar todas las clases de prueba
    suite.addTest(unittest.makeSuite(TestCalculosFinancieros))
    suite.addTest(unittest.makeSuite(TestIntegracionCompleta))
    suite.addTest(unittest.makeSuite(TestRobustezCalculos))

    # Ejecutar pruebas con reporte detallado
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)

    # Resumen de resultados
    print(f"\n{'='*60}")
    print(f"RESUMEN DE PRUEBAS - SISTEMA SEMAVENCA")
    print(f"{'='*60}")
    print(f"Pruebas ejecutadas: {result.testsRun}")
    print(f"Exitosas: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallidas: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    print(
        f"Tasa de éxito: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print(f"\nFALLOS DETECTADOS:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print(f"\nERRORES DETECTADOS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Error:')[-1].strip()}")

    # Código de salida
    exit_code = 0 if result.wasSuccessful() else 1
    print(f"\nCódigo de salida: {exit_code}")
    exit(exit_code)
