from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS
import requests
import uuid

app = Flask(__name__)
CORS(app)
# MongoDB Atlas Connection
client = MongoClient("mongodb+srv://shresthkumarkarnani:HlIH94dBFhoopMc3@cluster0.nhohior.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['riseup']
users_collection = db['users']
history_collection = db['user_history']

# Google Places API Key
GOOGLE_API_KEY = "AIzaSyCSd3g9AR_wqB5oMBekw2L2H-6Ht4mjkC8"

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "RiseUp AI Flask Server is running!"})

# -----------------------------------------
# 1. User Login/Signup
@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('name'):
        return jsonify({"error": "Name and Email are required"}), 400
    
    user = users_collection.find_one({"email": data['email']})
    if user:
        return jsonify({"message": "User already exists", "user_id": str(user['_id'])})
    
    user_id = str(uuid.uuid4())
    users_collection.insert_one({
        "_id": user_id,
        "name": data['name'],
        "email": data['email']
    })
    return jsonify({"message": "User registered successfully", "user_id": user_id}), 201

# -----------------------------------------
# 2. Find Shelters Nearby (using text search for better accuracy)
@app.route('/find_shelters', methods=['POST'])
def find_shelters():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if not latitude or not longitude:
        return jsonify({"error": "Latitude and Longitude are required"}), 400

    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=homeless+shelters+near+{latitude},{longitude}&key={GOOGLE_API_KEY}"
    response = requests.get(url)
    shelters = response.json()

    return jsonify(shelters)

# -----------------------------------------
# 3. Medical Assistance Questions (for Gemini AI)
@app.route('/medical_assistance', methods=['POST'])
def medical_assistance():
    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({"error": "Question is required"}), 400

    # SPACE FOR GEMINI AI INTEGRATION
    ai_response = "AI response placeholder (medical assistance)"

    # Log to user history
    history_collection.insert_one({
        "action": "medical_assistance",
        "question": question,
        "response": ai_response
    })

    return jsonify({"response": ai_response})

# -----------------------------------------
# 4. Career Help Form Submission (for Gemini AI)
@app.route('/career_help', methods=['POST'])
def career_help():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Form data is required"}), 400

    # SPACE FOR GEMINI AI INTEGRATION
    ai_response = "AI response placeholder (career guidance)"

    # Log to user history
    history_collection.insert_one({
        "action": "career_help",
        "form_data": data,
        "response": ai_response
    })

    return jsonify({"response": ai_response})

# -----------------------------------------
# 5. View User History
@app.route('/user_history', methods=['GET'])
def get_user_history():
    user_actions = list(history_collection.find({}, {'_id': 0}))
    return jsonify(user_actions)

# -----------------------------------------
# 6. Search Any Place (new test route for Google Places API)
@app.route('/search_place', methods=['POST'])
def search_place():
    data = request.get_json()
    place_query = data.get('query')

    if not place_query:
        return jsonify({"error": "Place query is required"}), 400

    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": place_query,
        "key": GOOGLE_API_KEY
    }
    response = requests.get(url, params=params)
    result = response.json()

    return jsonify(result)

# -----------------------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
