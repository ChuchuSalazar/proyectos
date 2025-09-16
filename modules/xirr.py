from datetime import datetime


def calcular_xirr_excel(self, valores, fechas, guess=0.10):
    """
    Replica el Excel XIRR:
    - valores: lista de flujos (al menos un + y un -)
    - fechas: lista de datetime.date/datetime.datetime del MISMO largo que valores
    - guess: 10% por defecto
    - 100 iteraciones, tolerancia 1e-8 (~0,000001%)
    Devuelve la TIR anual (como Excel XIRR).
    """
    if len(valores) != len(fechas) or len(valores) == 0:
        return None
    if not any(v > 0 for v in valores) or not any(v < 0 for v in valores):
        return None

    # Normaliza a datetime.date
    base = fechas[0]

    def years(d):
        return (d - base).days / 365.0

    def xnpv(rate):
        try:
            return sum(v / ((1.0 + rate) ** years(d)) for v, d in zip(valores, fechas))
        except OverflowError:
            return float("inf")

    def dxnpv(rate):
        try:
            return sum(
                -(years(d)) * v / ((1.0 + rate) ** (years(d) + 1.0))
                for v, d in zip(valores, fechas)
                if years(d) != 0
            )
        except OverflowError:
            return float("inf")

    r = guess
    tol = 1e-8  # 0,000001%
    for _ in range(100):
        if r <= -1 + 1e-12:
            r = -1 + 1e-12
        f = xnpv(r)
        df = dxnpv(r)
        if abs(df) < 1e-12:
            return None
        r_new = r - f / df
        if abs(r_new - r) <= tol:
            return r_new  # XIRR devuelve tasa ANUAL
        r = r_new
    return None  # #NUM! si no converge
