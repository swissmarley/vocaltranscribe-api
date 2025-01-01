from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import jwt
from datetime import datetime
from functools import wraps
import speech_recognition as sr
from pydub import AudioSegment
import os
from config import Config
from models import db, User, APIKey, RequestLog
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)
db.init_app(app)
bcrypt = Bcrypt(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

SUBSCRIPTION_LIMITS = {
    'free': 50,
    'silver': 500,
    'gold': 2000
}

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "No API key provided"}), 401

        api_key_obj = APIKey.query.filter_by(key=api_key).first()
        if not api_key_obj:
            return jsonify({"error": "Invalid API key"}), 401

        user = db.session.get(User, api_key_obj.user_id)
        if not user:
            return jsonify({"error": "Invalid user"}), 401

        # Check rate limit
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        request_count = RequestLog.query.filter(
            RequestLog.api_key_id == api_key_obj.id,
            RequestLog.timestamp >= month_start
        ).count()

        if request_count >= SUBSCRIPTION_LIMITS[user.subscription_plan]:
            return jsonify({"error": "Monthly request limit exceeded"}), 429

        # Log request with user email
        log = RequestLog(
            api_key_id=api_key_obj.id,
            user_id=user.id,
            user_email=user.email,
            endpoint=request.endpoint
        )
        db.session.add(log)
        db.session.commit()

        return f(*args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or 'email' not in data or 'subscription_plan' not in data:
        return jsonify({"error": "Missing email or subscription plan"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email already registered"}), 400

    jwt_token = jwt.encode(
        {'email': data['email']},
        app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )

    user = User(email=data['email'], subscription_plan=data['subscription_plan'], jwt_token=jwt_token)
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully", "token": jwt_token})

@app.route('/generate-api-key', methods=['POST'])
def generate_api_key():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"error": "No token provided"}), 401

    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        user = User.query.filter_by(jwt_token=token).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        import string
        import random
        api_key = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
        new_key = APIKey(key=api_key, user_id=user.id)
        db.session.add(new_key)
        db.session.commit()

        return jsonify({"api_key": api_key})
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

# Dictionary of supported languages with their codes
SUPPORTED_LANGUAGES = {
    'english': 'en-US',
    'italian': 'it-IT',
    'german': 'de-DE',
    'french': 'fr-FR',
    'spanish': 'es-ES',
    'dutch': 'nl-NL',
    'macedonian': 'mk-MK',
    'portuguese': 'pt-PT',
    'russian': 'ru-RU',
    'chinese': 'zh-CN',
    'japanese': 'ja-JP',
    'korean': 'ko-KR',
    'arabic': 'ar-AE',
    'hindi': 'hi-IN',
    'turkish': 'tr-TR',
    'greek': 'el-GR',
    'polish': 'pl-PL',
    'romanian': 'ro-RO',
    'vietnamese': 'vi-VN',
    'thai': 'th-TH'
}

@app.route('/speech-to-text', methods=['POST'])
@require_api_key
def speech_to_text():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(audio_file.filename):
        return jsonify({"error": "Invalid file type"}), 400

    # Get language from request (default to English if not specified)
    language = request.form.get('language', 'english').lower()
    
    # Validate language
    if language not in SUPPORTED_LANGUAGES:
        return jsonify({
            "error": "Unsupported language",
            "message": f"Please choose from the following languages: {', '.join(SUPPORTED_LANGUAGES.keys())}"
        }), 400

    try:
        # Secure the filename
        filename = secure_filename(audio_file.filename)
        audio_path = os.path.join("uploads", filename)
        audio_file.save(audio_path)

        # Convert to WAV if necessary
        if filename.endswith('.mp3'):
            sound = AudioSegment.from_mp3(audio_path)
            wav_path = audio_path[:-4] + '.wav'
            sound.export(wav_path, format="wav")
            os.remove(audio_path)
            audio_path = wav_path
        elif filename.endswith('.ogg'):
            sound = AudioSegment.from_ogg(audio_path)
            wav_path = audio_path[:-4] + '.wav'
            sound.export(wav_path, format="wav")
            os.remove(audio_path)
            audio_path = wav_path
        elif filename.endswith('.flac'):
            sound = AudioSegment.from_file(audio_path, format="flac")
            wav_path = audio_path[:-5] + '.wav'
            sound.export(wav_path, format="wav")
            os.remove(audio_path)
            audio_path = wav_path

        # Perform speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)

        # Get the language code and perform recognition
        language_code = SUPPORTED_LANGUAGES[language]
        text = recognizer.recognize_google(audio, language=language_code)
        
        # Clean up the audio file
        os.remove(audio_path)
        
        return jsonify({
            "text": text,
            "language": language,
            "language_code": language_code
        })

    except sr.UnknownValueError:
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return jsonify({
            "error": "Speech recognition failed",
            "message": "Could not understand the audio content"
        }), 422

    except sr.RequestError as e:
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return jsonify({
            "error": "Service error",
            "message": f"Could not request results from speech recognition service; {str(e)}"
        }), 503

    except Exception as e:
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return jsonify({
            "error": "Processing error",
            "message": str(e)
        }), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['wav', 'mp3', 'ogg', 'flac']

if __name__ == '__main__':
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    # Check if SSL certificates exist
    ssl_context = None
    if os.path.exists('cert.pem') and os.path.exists('key.pem'):
        ssl_context = ('cert.pem', 'key.pem')
    
    # Run with or without SSL based on certificate availability
    if ssl_context:
        app.run(ssl_context=ssl_context, host='0.0.0.0', port=5003)
    else:
        app.run(host='0.0.0.0', port=5003)