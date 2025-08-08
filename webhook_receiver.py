from flask import Flask, request, abort
import json

# Crea una instancia de la aplicación Flask
app = Flask(__name__)

@app.route('/github-webhook', methods=['POST'])
def handle_github_webhook():
    # Verifica que la petición venga de GitHub y sea un evento 'push'
    if request.headers.get('X-GitHub-Event') == 'push':
        # Obtiene el payload (los datos JSON enviados por GitHub)
        data = request.json
        
        # Extrae la información que nos interesa
        repo_name = data['repository']['full_name']
        commit_sha = data['head_commit']['id']
        commit_message = data['head_commit']['message']
        
        # --- Aquí es donde ocurre la "magia" ---
        # Por ahora, simplemente lo imprimiremos en la consola para ver que funciona
        # y lo guardaremos en un archivo de texto.
        print(f"¡Nuevo commit recibido!")
        print(f"  Repositorio: {repo_name}")
        print(f"  Commit SHA: {commit_sha}")
        print(f"  Mensaje: {commit_message}")
        
        # Guardamos la info para que la app de Streamlit la pueda leer
        with open("latest_commit.txt", "w") as f:
            f.write(f"{repo_name},{commit_sha}")
            
        return 'Webhook recibido correctamente', 200
    else:
        # Si no es un evento push, o no es de GitHub, lo ignoramos
        return 'Evento no procesado', 202

if __name__ == '__main__':
    # Ejecuta el servidor en el puerto 5001 (para no chocar con Streamlit)
    app.run(host='0.0.0.0', port=5001, debug=True)