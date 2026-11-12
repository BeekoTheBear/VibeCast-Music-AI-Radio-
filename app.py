from flask import Flask, render_template, request, jsonify
from datetime import datetime
import urllib.request
import urllib.parse
import re
import os

app = Flask(__name__, template_folder='templates')

# In-memory store (Ready for Supabase PostgreSQL integration)
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

@app.route('/api/resolve-video', methods=['GET'])
def resolve_video():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "Missing query"}), 400
    try:
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        req = urllib.request.Request(
            search_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
        )
        html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8', errors='ignore')
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        
        # Deduplicate while preserving top search relevance
        unique_ids = []
        for vid in video_ids:
            if vid not in unique_ids:
                unique_ids.append(vid)
                
        if unique_ids:
            return jsonify({
                "videoId": unique_ids[0],
                "alternatives": unique_ids[:5]
            }), 200
        return jsonify({"error": "No video ID found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
