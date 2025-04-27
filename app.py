from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import requests
import uuid
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# -----------------------------------------
# MongoDB Atlas Connection
client = MongoClient("mongodb+srv://shresthkumarkarnani:HlIH94dBFhoopMc3@cluster0.nhohior.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['riseup']
users_collection = db['users']
history_collection = db['user_history']

# -----------------------------------------
# API Keys
GOOGLE_API_KEY = "AIzaSyCSd3g9AR_wqB5oMBekw2L2H-6Ht4mjkC8"
GEMINI_API_KEY = "AIzaSyCSd3g9AR_wqB5oMBekw2L2H-6Ht4mjkC8"

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro")  # Correct model name

# -----------------------------------------
# Routes

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "RiseUp AI Flask Server is running!"})

# -----------------------------------------
# 1. User Sign Up (new user registration)
@app.route('/signup', methods=['POST'])
def signup_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not username or not password or not confirm_password:
        return jsonify({"error": "Username, Password, and Confirm Password are required."}), 403

    if password != confirm_password:
        return jsonify({"error": "Passwords do not match."}), 400

    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        return jsonify({"error": "Username already exists. Please choose another."}), 409

    user_id = str(uuid.uuid4())
    users_collection.insert_one({
        "_id": user_id,
        "username": username,
        "password": password  # (Note: plaintext, hash it in real projects)
    })

    return jsonify({"message": "Account created successfully!", "user_id": user_id}), 201

# -----------------------------------------
# 2. User Login (sign in existing user)
@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and Password are required."}), 400

    user = users_collection.find_one({"username": username})
    if not user:
        return jsonify({"error": "User not found. Please sign up first."}), 404

    if user['password'] != password:
        return jsonify({"error": "Incorrect password. Please try again."}), 401

    return jsonify({"message": "Login successful!", "user_id": str(user['_id'])}), 200

# -----------------------------------------
# 3. Find Shelters Nearby (Google Places)
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
# 4. Medical Assistance Chatbot (Gemini AI)
@app.route('/medical_assistance', methods=['POST'])
def medical_assistance():
    data = request.get_json()
    question = data.get('question')

    if not question:
        return jsonify({"error": "Question is required"}), 400

    response = gemini_model.generate_content(question)
    ai_response = response.text.strip()

    # Log interaction
    history_collection.insert_one({
        "action": "medical_assistance",
        "question": question,
        "response": ai_response
    })

    return jsonify({"response": ai_response})

# -----------------------------------------
# 5. Career Help (Dynamic Form Submission to Gemini AI)
@app.route('/career_help', methods=['POST'])
def career_help():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Form data is required"}), 400

    prompt = f"""
    Based on the following user profile, suggest 5 strong career options along with brief reasoning for each:

    User Profile:
    {data}

    Please give detailed options in simple, user-friendly language.
    """

    response = gemini_model.generate_content(prompt)
    ai_response = response.text.strip()

    # Log interaction
    history_collection.insert_one({
        "action": "career_help",
        "form_data": data,
        "response": ai_response
    })

    return jsonify({"response": ai_response})

# -----------------------------------------
# 6. View User History
@app.route('/user_history', methods=['GET'])
def get_user_history():
    user_actions = list(history_collection.find({}, {'_id': 0}))
    return jsonify(user_actions)

# -----------------------------------------
# 7. Search Any Place (Google Places text search)
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
