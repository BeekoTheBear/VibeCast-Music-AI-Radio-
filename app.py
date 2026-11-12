from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory store (Connects directly to Supabase PostgreSQL next)
users_db = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "VibeCast API is running live!",
        "app": "VibeCast: Music-AI-Radio",
        "auth_providers": ["google", "email", "username", "phone"]
    }), 200

@app.route('/api/user/sync', methods=['POST'])
def sync_user():
    data = request.get_json() or {}
    user_id = data.get('id')
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    users_db[user_id] = {
        **data,
        "last_synced": datetime.utcnow().isoformat()
    }
    return jsonify({"status": "synced", "user": users_db[user_id]}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
