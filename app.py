from flask import Flask, request, jsonify
import random

app = Flask(__name__)

# Mock database storage (In production, replace with your Supabase PostgreSQL connection)
STATIONS_DB = []
TRACKS_DB = []

@app.route('/')
def home():
    return jsonify({"status": "StreamStation API is running live!"}), 200

# --- 1. STATION CREATION ROUTE ---
@app.route('/api/create-station', methods=['POST'])
def create_station():
    data = request.json
    station_name = data.get('station_name')
    seed_artists = data.get('seed_artists', []) # Supports unlimited artist picks
    is_randomized = data.get('is_randomized', True)
    
    if not station_name or not seed_artists:
        return jsonify({"error": "Station name and seed artists are required."}), 400

    # Simulated track queue builder based on artist seeds
    generated_queue = []
    for artist in seed_artists:
        # In production, query MusicBrainz/Last.fm API here for actual top tracks
        generated_queue.append({"title": f"Top Hit by {artist}", "artist": artist, "type": "catalog"})
    
    # If user selected random mixing, blend in random deep cuts or user-uploaded tracks
    if is_randomized and TRACKS_DB:
        random_indie_tracks = random.sample(TRACKS_DB, min(len(TRACKS_DB), 3))
        for t in random_indie_tracks:
            generated_queue.append(t)
        random.shuffle(generated_queue)

    station_data = {
        "station_name": station_name,
        "seed_artists": seed_artists,
        "queue": generated_queue
    }
    
    STATIONS_DB.append(station_data)
    return jsonify({"message": "Station created successfully!", "station": station_data}), 201

# --- 2. USER TRACK UPLOAD WITH AI DISCLOSURE ROUTE ---
@app.route('/api/upload-track', methods=['POST'])
def upload_track():
    data = request.json
    
    title = data.get('title')
    artist_name = data.get('artist_name')
    audio_url = data.get('audio_url') # Hosted file link
    
    # Mandatory AI Disclosure Metadata
    ai_audio = data.get('ai_audio_type')       # 'human', 'hybrid', or 'fully_ai'
    ai_lyrics = data.get('ai_lyrics_type')     # 'human' or 'ai_assisted'
    ai_artwork = data.get('ai_artwork_type')   # 'human' or 'ai_generated'
    certified_rights = data.get('certified_rights', False)

    # Validation guardrails
    if not certified_rights:
        return jsonify({"error": "You must certify that you hold commercial rights and are not cloning voices."}), 400
    
    if not all([ai_audio, ai_lyrics, ai_artwork]):
        return jsonify({"error": "All AI disclosure fields must be completed."}), 400

    track_record = {
        "title": title,
        "artist": artist_name,
        "audio_url": audio_url,
        "disclosures": {
            "audio": ai_audio,
            "lyrics": ai_lyrics,
            "artwork": ai_artwork
        }
    }
    
    TRACKS_DB.append(track_record)
    return jsonify({"message": "Track uploaded with AI disclosure tags!", "track": track_record}), 201

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
