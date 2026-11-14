from flask import Flask, render_template, request, jsonify
from datetime import datetime
import urllib.request
import urllib.parse
import re
import os

app = Flask(__name__, template_folder='templates')

# Server-side persistent user and community store
users_db = {}
comments_db = {} # station_id -> list of comments
collab_requests_db = {} # creator_id -> list of requests

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

@app.route('/api/user/register', methods=['POST'])
def register_user():
    data = request.get_json() or {}
    identifier = data.get('identifier', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not identifier or not password:
        return jsonify({"error": "Identifier and password are required"}), 400
    
    if identifier in users_db:
        return jsonify({"error": "Account already exists with this identifier. Please sign in."}), 400
    
    user_obj = {
        "id": identifier,
        "password": password,
        "displayName": data.get('displayName', identifier.split('@')[0]),
        "handle": data.get('handle', f"@{identifier.split('@')[0].replace(' ', '')}"),
        "bio": data.get('bio', 'Music curator & VibeCast station creator. Available for collabs and live remote sessions.'),
        "availability": data.get('availability', '🟢 Online / Studio Active'),
        "contactPref": data.get('contactPref', 'email'),
        "allowComments": data.get('allowComments', True),
        "provider": data.get('provider', 'credentials'),
        "paymentMethod": data.get('paymentMethod'),
        "prefs": data.get('prefs', {"autoplay": True, "aiBadges": True, "fullSongMode": True, "backgroundPlay": True}),
        "stations": data.get('stations', []),
        "last_synced": datetime.utcnow().isoformat()
    }
    users_db[identifier] = user_obj
    return jsonify({"status": "registered", "user": user_obj}), 200

@app.route('/api/user/login', methods=['POST'])
def login_user():
    data = request.get_json() or {}
    identifier = data.get('identifier', '').strip().lower()
    password = data.get('password', '').strip()
    
    if not identifier or not password:
        return jsonify({"error": "Identifier and password are required"}), 400
        
    user = users_db.get(identifier)
    if not user:
        for u_id, u_data in users_db.items():
            if u_id == identifier or u_data.get('handle', '').lower() == identifier:
                user = u_data
                break
                
    if not user:
        return jsonify({"error": "Account not found. Please register first."}), 404
        
    if user.get('password') != password:
        return jsonify({"error": "Incorrect password."}), 401
        
    return jsonify({"status": "success", "user": user}), 200

@app.route('/api/user/sync', methods=['POST'])
def sync_user():
    data = request.get_json() or {}
    user_id = data.get('id', '').strip().lower()
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    
    if user_id in users_db:
        pwd = users_db[user_id].get('password', '')
        users_db[user_id] = {
            **users_db[user_id],
            **data,
            "password": data.get('password', pwd),
            "last_synced": datetime.utcnow().isoformat()
        }
    else:
        users_db[user_id] = {
            **data,
            "password": data.get('password', 'secure_pass'),
            "last_synced": datetime.utcnow().isoformat()
        }
    return jsonify({"status": "synced", "user": users_db[user_id]}), 200

@app.route('/api/stations/search', methods=['GET'])
def search_stations():
    query = request.args.get('q', '').strip().lower()
    results = []
    
    for u_id, user in users_db.items():
        creator_name = user.get('displayName', 'Creator')
        handle = user.get('handle', '@creator')
        email = user.get('id', '')
        bio = user.get('bio', '')
        availability = user.get('availability', '🟢 Online')
        contact_pref = user.get('contactPref', 'email')
        allow_comments = user.get('allowComments', True)
        
        for station in user.get('stations', []):
            station_name = station.get('name', '').lower()
            genre = station.get('genre', '').lower()
            artists = [a.lower() for a in station.get('artists', [])]
            
            match = (
                not query or 
                query in station_name or 
                query in genre or 
                any(query in a for a in artists) or 
                query in handle.lower() or 
                query in email.lower()
            )
            
            if match:
                results.append({
                    **station,
                    "creator": creator_name,
                    "handle": handle,
                    "email": email,
                    "bio": bio,
                    "availability": availability,
                    "contactPref": contact_pref,
                    "allowComments": allow_comments
                })
                
    return jsonify({"stations": results}), 200

@app.route('/api/station/comments', methods=['GET', 'POST'])
def handle_comments():
    station_id = request.args.get('stationId') or (request.get_json() or {}).get('stationId')
    if not station_id:
        return jsonify({"error": "Station ID required"}), 400
        
    if request.method == 'GET':
        return jsonify({"comments": comments_db.get(str(station_id), [])}), 200
        
    data = request.get_json() or {}
    comment_text = data.get('text', '').strip()
    author = data.get('author', 'Listener')
    if not comment_text:
        return jsonify({"error": "Comment text required"}), 400
        
    if str(station_id) not in comments_db:
        comments_db[str(station_id)] = []
        
    new_comment = {"author": author, "text": comment_text, "timestamp": datetime.utcnow().strftime('%H:%M')}
    comments_db[str(station_id)].append(new_comment)
    return jsonify({"status": "success", "comments": comments_db[str(station_id)]}), 200

@app.route('/api/resolve-video', methods=['GET'])
def resolve_video():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"error": "Missing query"}), 400
    try:
        refined_query = f"{query} official music video -lyric -lyrics -visualizer"
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(refined_query)}"
        req = urllib.request.Request(
            search_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }
        )
        html = urllib.request.urlopen(req, timeout=8).read().decode('utf-8', errors='ignore')
        video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
