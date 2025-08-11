import streamlit as st
import google.generativeai as genai
import markdown
import weasyprint
import os
from io import BytesIO
import tempfile
from github import Github, GithubException

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    layout="wide",
    page_title="Herramienta de Código IA",
    page_icon="🤖"
)

# --- 2. CONFIGURACIÓN DE APIS Y SECRETS ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    if "GITHUB_TOKEN" not in st.secrets:
        raise KeyError("GITHUB_TOKEN no encontrado")
except (KeyError, AttributeError):
    st.error("🔑 ¡Error de configuración! Asegúrate de que GEMINI_API_KEY y GITHUB_TOKEN están en tu archivo .streamlit/secrets.toml y reinicia la aplicación.")
    st.stop()

# --- 3. FUNCIONES CORE DE LA APLICACIÓN ---
def load_prompt_template(filename):
    """Carga una plantilla de prompt desde un archivo de texto."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"🚨 El archivo de plantilla '{filename}' no se encuentra. Revisa la ruta y la estructura de carpetas.")
        return None

def generate_content(prompt_filename, summary, code_before=None, code_after=None, uploaded_file_before=None, uploaded_file_after=None):
    """Genera contenido usando Gemini. Puede operar en modo texto o en modo archivo."""
    prompt_template = load_prompt_template(prompt_filename)
    if not prompt_template: return "Error: No se pudo cargar la plantilla."
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    # Modo Texto (sin cambios)
    if code_after is not None:
        st.info("🔄 Usando el modo de entrada de texto.")
        code_section = f"## Código ANTES:\n```\n{code_before}\n```\n\n## Código DESPUÉS:\n```\n{code_after}\n```" if code_before else f"## Código a Revisar:\n```\n{code_after}\n```"
        full_prompt = prompt_template.format(resumen_dev=summary, seccion_de_codigo=code_section)
        response = model.generate_content(full_prompt)
        return response.text

    # Modo Archivo 
    elif uploaded_file_after is not None:
        st.info("📂 Usando el modo de subida de archivos (ahorro de tokens).")
        prompt_parts = [prompt_template.format(resumen_dev=summary)]
        
        def upload_to_gemini(uploaded_file, display_name):
            if uploaded_file is None: 
                return None
            
            temp_file_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as temp_file:
                    temp_file.write(uploaded_file.getvalue())
                    temp_file_path = temp_file.name # Guardamos la ruta

                gemini_file = genai.upload_file(path=temp_file_path, display_name=display_name)
                return gemini_file

            finally:
                if temp_file_path and os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        gemini_file_after = upload_to_gemini(uploaded_file_after, "código_después")
        if gemini_file_after: 
            prompt_parts.append(gemini_file_after)
        else: 
            return "Error: Fallo al subir el archivo 'después'."

        if uploaded_file_before:
            gemini_file_before = upload_to_gemini(uploaded_file_before, "código_antes")
            if gemini_file_before: 
                prompt_parts.append(gemini_file_before)
        
        response = model.generate_content(prompt_parts)
        return response.text
    
    else:
        return "Error: Se necesita proporcionar el 'Código DESPUÉS' para generar una respuesta."

def get_commit_changes(repo_full_name, commit_sha):
    """Obtiene los archivos modificados de un commit específico comparándolo con su padre."""
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        repo = g.get_repo(repo_full_name)
        commit = repo.get_commit(sha=commit_sha)
        if not commit.parents:
            st.error("Este es el primer commit del repositorio y no se puede comparar.")
            return None
        parent_commit = commit.parents[0]
        changed_files_content = []
        for file in commit.files:
            content_after, content_before = "", ""
            if file.status != 'removed':
                try: content_after = repo.get_contents(file.filename, ref=commit.sha).decoded_content.decode('utf-8')
                except Exception: content_after = f"Error al obtener contenido de {file.filename}."
            if file.status != 'added':
                try: content_before = repo.get_contents(file.filename, ref=parent_commit.sha).decoded_content.decode('utf-8')
                except Exception: content_before = ""
            changed_files_content.append({"filename": file.filename, "status": file.status, "before": content_before, "after": content_after})
        return changed_files_content
    except GithubException as e:
        if e.status == 404:
            st.error(f"Repositorio no encontrado. Asegúrate de que la URL es correcta y que el repositorio es público.")
        else:
            st.error(f"Error de GitHub: {e}")
        return None
    except Exception as e:
        st.error(f"Error al conectar con GitHub: {e}")
        return None

def convert_to_pdf(markdown_text):
    """Convierte Markdown a PDF. (Sin cambios)"""

    try:
        html_content = markdown.markdown(markdown_text, extensions=['tables', 'fenced_code', 'codehilite', 'toc'])
        css_styles = """<style>body{font-family:Arial,sans-serif;line-height:1.6;margin:40px;color:#333}h1{color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:10px}h2{color:#34495e;margin-top:30px;border-left:4px solid #3498db;padding-left:15px}h3{color:#7f8c8d;margin-top:25px}code{background-color:#f8f9fa;padding:2px 4px;border-radius:3px;font-family:'Courier New',monospace}pre{background-color:#f8f9fa;padding:15px;border-radius:5px;border-left:4px solid #3498db;overflow-x:auto}table{border-collapse:collapse;width:100%;margin:20px 0}th,td{border:1px solid #ddd;padding:12px;text-align:left}th{background-color:#f2f2f2;font-weight:bold}</style>"""
        full_html = f"<!DOCTYPE html><html><head><meta charset=\"UTF-8\"><title>Documento Generado</title>{css_styles}</head><body>{html_content}</body></html>"
        return weasyprint.HTML(string=full_html).write_pdf()
    except Exception as e:
        st.error(f"Error al generar el PDF: {e}")
        return None

# --- 4. INTERFAZ DE USUARIO DE STREAMLIT ---
def main():
    st.title("🤖 Generador de Infografias con IA")
    st.markdown("Una herramienta para generar documentación y revisiones de código.")

    st.header("1. Proporciona el Contexto y el Código")

    with st.container(border=True):
        developer_summary = st.text_input(
            "Resumen de tu tarea (requerido para todos los métodos):", 
            placeholder="Ej: Se refactorizó la clase User para usar inyección de dependencias."
        )

        input_tab_text, input_tab_file, input_tab_github = st.tabs([
            "✍️ Pegar Código", 
            "📂 Subir Archivos", 
            "🔗 Analizar desde GitHub"
        ])

        with input_tab_text:
            st.markdown("Pega el contenido de tu código directamente.")
            col1_text, col2_text = st.columns(2)
            with col1_text: code_before_text = st.text_area("Código ANTES (Opcional)", height=300, key="text_before")
            with col2_text: code_after_text = st.text_area("Código DESPUÉS (Requerido)", height=300, key="text_after")
            if st.button("🚀 Generar Informe desde Texto", type="primary"):
                result = generate_content("Markdwon_Prompts/prompt_informe.txt", developer_summary, code_before=code_before_text, code_after=code_after_text)
                if result: st.session_state.informe_markdown = result

        with input_tab_file:
            st.markdown("Sube los archivos de código. Este método es más eficiente.")
            col1_file, col2_file = st.columns(2)
            with col1_file: uploaded_file_before = st.file_uploader("Sube el archivo ANTES (Opcional)", key="file_before")
            with col2_file: uploaded_file_after = st.file_uploader("Sube el archivo DESPUÉS (Requerido)", key="file_after")
            if st.button("🚀 Generar Informe desde Archivos", type="primary", key="btn_informe_file"):
                result = generate_content("Archivos_Prompts/prompt_informe_archivo.txt", developer_summary, uploaded_file_before=uploaded_file_before, uploaded_file_after=uploaded_file_after)
                if result: st.session_state.informe_markdown = result
        
        with input_tab_github:
            st.header("Analizar el Último Commit de un Repositorio")
            repo_url = st.text_input(
                "URL del Repositorio de GitHub:",
                placeholder="https://github.com/usuario/nombre-del-repositorio"
            )

            if st.button("🛰️ Comparar último commit", type="primary"):
                if not repo_url:
                    st.warning("Por favor, introduce la URL de un repositorio de GitHub.")
                else:
                    try:
                        # Extraer 'usuario/repo' de la URL
                        repo_full_name = '/'.join(repo_url.strip().split('/')[-2:])
                        g = Github(st.secrets["GITHUB_TOKEN"])
                        repo = g.get_repo(repo_full_name)
                        
                        # Obtener el último commit de la rama por defecto
                        latest_commit = repo.get_commits()[0]
                        st.session_state.commit_sha = latest_commit.sha

                        with st.spinner(f"Comparando el commit `{latest_commit.sha[:7]}` con su anterior..."):
                            changed_files = get_commit_changes(repo_full_name, latest_commit.sha)
                            if changed_files is not None:
                                st.session_state.changed_files = changed_files
                                st.success(f"Comparación completa. Se encontraron {len(changed_files)} archivos modificados.")
                    
                    except GithubException as e:
                        if e.status == 404:
                            st.error(f"Repositorio no encontrado. Asegúrate de que la URL '{repo_url}' es correcta y el repo es público.")
                        else:
                            st.error(f"Error de GitHub: {e}. ¿La URL es correcta?")
                    except Exception as e:
                        st.error(f"Ocurrió un error. Asegúrate de que la URL sea válida. Error: {e}")

            if 'changed_files' in st.session_state and st.session_state.changed_files:
                filenames = [f['filename'] for f in st.session_state.changed_files]
                selected_filename = st.selectbox("Selecciona un archivo del commit para analizar:", filenames, key="github_file_selector")

                if selected_filename:
                    selected_file_data = next((item for item in st.session_state.changed_files if item["filename"] == selected_filename), None)
                    if selected_file_data:
                        st.subheader(f"Análisis para: `{selected_filename}`")
                        
                        col1_git, col2_git = st.columns(2)
                        with col1_git:
                            if st.button("📄 Generar Informe (GitHub)"):
                                with st.spinner(f"Generando informe para {selected_filename}..."):
                                    result = generate_content("Markdwon_Prompts/prompt_informe.txt", developer_summary, code_before=selected_file_data.get('before', ''), code_after=selected_file_data.get('after', ''))
                                    if result: st.session_state.informe_markdown = result
                        with col2_git:
                            if st.button("🧐 Generar Revisión (GitHub)"):
                                with st.spinner(f"Generando revisión para {selected_filename}..."):
                                     result = generate_content("Markdwon_Prompts/prompt_revision.txt", developer_summary, code_before=selected_file_data.get('before', ''), code_after=selected_file_data.get('after', ''))
                                     if result: st.session_state.revision_markdown = result

    # --- Sección de Resultados ---
    st.header("2. Revisa, Edita y Descarga el Resultado")
    output_informe, output_revision = st.tabs(["Resultado del Informe", "Resultado de la Revisión"])
    with output_informe:
        if 'informe_markdown' not in st.session_state: st.session_state.informe_markdown = ""
        if st.session_state.informe_markdown:
            edited_report = st.text_area("**Edita el borrador del informe aquí:**", value=st.session_state.informe_markdown, height=400, key="editor_informe")
            pdf_data = convert_to_pdf(edited_report)
            if pdf_data: st.download_button("⬇️ Descargar Informe como PDF", pdf_data, "informe_tecnico.pdf")

    with output_revision:
        if 'revision_markdown' not in st.session_state: st.session_state.revision_markdown = ""
        if st.session_state.revision_markdown:
            edited_review = st.text_area("**Edita la revisión aquí:**", value=st.session_state.revision_markdown, height=400, key="editor_revision")
            pdf_review_data = convert_to_pdf(edited_review)
            if pdf_review_data: st.download_button("⬇️ Descargar Revisión como PDF", pdf_review_data, "revision_codigo.pdf")

if __name__ == "__main__":
    main()