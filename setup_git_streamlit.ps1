
# Inicializar Git si no existe
if (!(Test-Path ".git")) {
    git init
    Write-Host "✅ Git inicializado"
}

# Crear .gitignore
@"
venv/
__pycache__/
*.pyc
*.log
.vscode/
.env
.DS_Store
Thumbs.db
"@ | Out-File -Encoding UTF8 .gitignore
Write-Host "✅ Archivo .gitignore creado"

# Crear LICENSE (MIT)
@"
MIT License

Copyright (c) 2025 Jesus Salazar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"@ | Out-File -Encoding UTF8 LICENSE
Write-Host "✅ Archivo LICENSE creado"

# Crear requirements.txt
"""
pandas
numpy
streamlit
chardet
""" | Out-File -Encoding UTF8 requirements.txt
Write-Host "✅ Archivo requirements.txt creado"

# Crear README.md
@"
# Proyecto Streamlit - Evaluación Financiera

Aplicación desarrollada en Python 2026 usando Streamlit para evaluar proyectos de inversión.

## Funcionalidades
- Cálculo de TIR, VPN, ROI
- Visualización de flujos de efectivo
- Generación de reportes en Excel y PDF

## Autor
MSc Jesús Salazar Rojas
"@ | Out-File -Encoding UTF8 README.md
Write-Host "✅ Archivo README.md creado"


Write-Host "🔧 Creando entorno virtual 'entorno'..."
python -m venv entorno

Write-Host "✅ Entorno virtual creado. Activando..."
.\entorno\Scripts\Activate.ps1

Write-Host "📦 Instalando dependencias necesarias..."
pip install streamlit>=1.28.0 pandas>=2.0.0 numpy>=1.24.0 scipy>=1.11.0 `
plotly>=5.15.0 matplotlib>=3.7.0 seaborn>=0.12.0 `
openpyxl>=3.1.0 xlsxwriter>=3.1.0 xlrd>=2.0.1 `
pillow>=9.5.0 reportlab>=4.0.0 `
python-dateutil>=2.8.0 pytz>=2023.3 `
validators>=0.20.0 scikit-learn>=1.3.0 `
black>=23.0.0 pytest>=7.4.0 `
setuptools>=68.0.0 wheel>=0.41.0

#Write-Host "🚀 Lanzando aplicación Streamlit..."
#streamlit run main_app.py



# Hacer commit inicial
git add .
git commit -m "🚀 Proyecto inicial configurado con Streamlit y Git"
Write-Host "✅ Commit inicial realizado"

Write-Host "🎯 Proyecto listo para subir a GitHub. Usa 'git remote add origin <URL>' y 'git push -u origin main'"
