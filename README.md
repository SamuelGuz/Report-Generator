Generador de Informes de Código
Utiliza Modelos de Lenguaje Grandes (LLMs) para automatizar la generación de documentación técnica y revisiones de código formales. Analiza código pegando texto, subiendo archivos o comparando directamente el último commit de cualquier repositorio público de GitHub.

Características Principales
Análisis Multifacético: Acepta código mediante entrada de texto directa, subida de archivos (.py, .js, etc.) o extrayendo los cambios del último commit desde una URL de un repositorio de GitHub.
Doble Modo de Generación:

Informe Técnico: Crea documentación profesional que detalla la lógica de implementación, las decisiones de arquitectura y consideraciones futuras.
Revisión de Código: Simula a un líder técnico senior, proporcionando feedback sobre la calidad del código, buenas prácticas y posibles mejoras.
Resultados Interactivos: Todo el contenido generado por la IA se presenta como Markdown editable, permitiendo un refinamiento inmediato (Si es requerido) y su exportación a formatos .md y .pdf.

Stack Tecnológico
Backend y Frontend: Streamlit
LLM: Google Gemini API
Integración VCS: PyGithub
Renderizado de PDF: WeasyPrint

Prerrequisitos
Python 3.9+ y Git
Una Clave de API de Google Gemini.
Un Token de Acceso Personal (PAT) de GitHub con el permiso (scope) de repo.

Instalación
code
Bash
# Clona el repositorio
git clone https://github.com/SamuelGuz/Report-Generator
cd Report-Generator

# Configura un entorno virtual
python -m venv venv
source venv/bin/activate  - # En Windows, usa `.\venv\Scripts\activate`

# Instala las dependencias
pip install -r requirements.txt
```*(Necesitarás crear un archivo `requirements.txt` con las dependencias del proyecto).*

# Configuración de Claves de API

Crea un archivo en la ruta `.streamlit/secrets.toml` y añade tus claves de API:

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "TU_CLAVE_DE_API_DE_GEMINI_AQUI"
GITHUB_TOKEN = "ghp_TU_TOKEN_DE_GITHUB_AQUI"

Ejecutar la Aplicación
Lanza la aplicacion con un unico comando Streamlt
Streamlit run app.py
