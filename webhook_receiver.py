from flask import Flask, request, abort
import json

app = Flask(__name__)

@app.route('/github-webhook', methods=['POST'])
def handle_github_webhook():
    if request.headers.get('X-GitHub-Event') == 'push':
        data = request.json
        repo_name = data['repository']['full_name']
        commit_sha = data['head_commit']['id']
        commit_message = data['head_commit']['message']
        
        print(f"¡Nuevo commit recibido!")
        print(f"  Repositorio: {repo_name}")
        print(f"  Commit SHA: {commit_sha}")
        print(f"  Mensaje: {commit_message}")

        with open("latest_commit.txt", "w") as f:
            f.write(f"{repo_name},{commit_sha}")
            
        return 'Webhook recibido correctamente', 200
    else:

        return 'Evento no procesado', 202

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)