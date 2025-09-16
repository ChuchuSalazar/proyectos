import os
import ast
from pathlib import Path
import pandas as pd
from html import escape


# Función para analizar un archivo Python y extraer clases y métodos
def analizar_archivo(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=str(filepath))

    clases = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            metodos = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            clases.append((node.name, metodos))
    return clases


# Función para recorrer el proyecto y generar el mapeo
def generar_mapeo(ruta):
    mapeo = {}
    for root, _, files in os.walk(ruta):
        for file in files:
            if file.endswith(".py"):
                filepath = Path(root) / file
                clases = analizar_archivo(filepath)
                mapeo[str(filepath)] = clases
    return mapeo


# Función principal del script
if __name__ == "__main__":
    ruta_proyecto = "."
    mapeo = generar_mapeo(ruta_proyecto)

    # Exportar a HTML
    html_content = "<html><body><h1>Mapa de Clases y Métodos</h1><ul>"
    for archivo, clases in mapeo.items():
        html_content += f"<li><strong>{escape(archivo)}</strong><ul>"
        for clase, metodos in clases:
            html_content += f"<li>Clase: {escape(clase)}<ul>"
            for metodo in metodos:
                html_content += f"<li>Método: {escape(metodo)}</li>"
            html_content += "</ul></li>"
        html_content += "</ul></li>"
    html_content += "</ul></body></html>"

    with open("estructura.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    # Exportar a Excel
    filas = []
    for archivo, clases in mapeo.items():
        for clase, metodos in clases:
            for metodo in metodos:
                filas.append({"Archivo": archivo, "Clase": clase, "Método": metodo})

    df = pd.DataFrame(filas)
    df.to_excel("estructura.xlsx", index=False, engine="openpyxl")

    print(
        "Se han generado los archivos 'estructura.html' y 'estructura.xlsx' con el mapeo del proyecto."
    )
