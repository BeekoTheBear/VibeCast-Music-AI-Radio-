from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory storage (Ready to swap with Supabase PostgreSQL next)
stations = []
tracks = []

# 1. Serve the visual mobile frontend
@app.route('/')
def home():
    return render_template('index.html')

# 2. API Health Check
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "VibeCast API is running live!",
        "app": "VibeCast: Music-AI-Radio",
        "license": "Proprietary - All Rights Reserved"
    }), 200

# 3. Get all stations or create a new station
@app.route('/stations', methods=['GET', 'POST'])
def handle_stations():
    if request.method == 'GET':
        return jsonify({"stations": stations}), 200

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    genre = data.get('genre', 'AI Radio').strip()

    if not name:
        return jsonify({"error": "Station name is required"}), 400

    new_station = {
        "id": data.get('id', int(datetime.utcnow().timestamp() * 1000)),
        "name": name,
        "genre": genre,
        "created_at": datetime.utcnow().isoformat(),
        "tracks": []
    }
    stations.append(new_station)
    return jsonify({"message": "Station created", "station": new_station}), 201

# 4. Upload a track with mandatory AI disclosure compliance
@app.route('/tracks', methods=['POST'])
def upload_track():
    data = request.get_json() or {}
    station_id = data.get('station_id')
    title = data.get('title', '').strip()
    artist = data.get('artist', 'VibeCast Creator').strip()
    url = data.get('url', '').strip()
    disclosure = data.get('disclosure', {})

    if not station_id or not title:
        return jsonify({"error": "Station ID and track title are required"}), 400

    # Enforce AI-disclosure schema (Audio, Lyrics, Artwork)
    ai_compliance = {
        "ai_audio": bool(disclosure.get('audio', False)),
        "ai_lyrics": bool(disclosure.get('lyrics', False)),
        "ai_artwork": bool(disclosure.get('artwork', False))
    }

    new_track = {
        "id": int(datetime.utcnow().timestamp() * 1000),
        "station_id": station_id,
        "title": title,
        "artist": artist,
        "url": url,
        "ai_disclosure": ai_compliance,
        "uploaded_at": datetime.utcnow().isoformat()
    }
    tracks.append(new_track)

    # Attach track to matching station in memory
    for station in stations:
        if str(station["id"]) == str(station_id):
            station["tracks"].append(new_track)
            break

    return jsonify({"message": "Track queued with AI disclosures", "track": new_track}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
