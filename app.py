from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import requests
import uuid
import google.generativeai as genai

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://localhost:5176"]}})

# -----------------------------------------
# MongoDB Atlas Connection
client = MongoClient("mongodb+srv://shresthkumarkarnani:HlIH94dBFhoopMc3@cluster0.nhohior.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['riseup']
history_collection = db['user_history']
businesses_collection = db['business_list']

# -----------------------------------------
# API Keys
GOOGLE_API_KEY = "AIzaSyCSd3g9AR_wqB5oMBekw2L2H-6Ht4mjkC8"
GEMINI_API_KEY = "AIzaSyCSd3g9AR_wqB5oMBekw2L2H-6Ht4mjkC8"

# -----------------------------------------
# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY, transport="rest")
gemini_model = genai.GenerativeModel(model_name="gemini-1.5-pro")

# -----------------------------------------
# Routes

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "RiseUp AI Flask Server is running!"})

# -----------------------------------------
@app.route('/find_shelters', methods=['POST'])
def find_shelters():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    if not latitude or not longitude:
        return jsonify({"error": "Latitude and Longitude are required"}), 400
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {"location": f"{latitude},{longitude}", "radius": 20000, "keyword": "homeless shelter", "key": GOOGLE_API_KEY}
    response = requests.get(url, params=params)
    results = response.json()
    return jsonify({"results": results.get('results', [])[:5], "status": results.get('status', 'UNKNOWN')})

# -----------------------------------------
@app.route('/find_medicare', methods=['POST'])
def find_medicare():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    if not latitude or not longitude:
        return jsonify({"error": "Latitude and Longitude are required"}), 400
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {"location": f"{latitude},{longitude}", "radius": 20000, "keyword": "government health facility", "key": GOOGLE_API_KEY}
    response = requests.get(url, params=params)
    results = response.json()
    return jsonify({"results": results.get('results', [])[:5], "status": results.get('status', 'UNKNOWN')})

# -----------------------------------------
@app.route('/find_food_donation', methods=['POST'])
def find_food_donation():
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    if not latitude or not longitude:
        return jsonify({"error": "Latitude and Longitude are required"}), 400
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {"location": f"{latitude},{longitude}", "radius": 20000, "keyword": "food donation center", "key": GOOGLE_API_KEY}
    response = requests.get(url, params=params)
    results = response.json()
    return jsonify({"results": results.get('results', [])[:5], "status": results.get('status', 'UNKNOWN')})

# -----------------------------------------
@app.route('/career_help', methods=['POST'])
def career_help():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Form data is required"}), 400
    
    prompt = f"""
    You are assisting someone to build a strong future.

    Based on the following user profile, suggest exactly 5 career paths that best fit their strengths and interests.

    For each career path:
    - Briefly explain the path.
    - Provide a clear step-by-step action plan to succeed.
    - End each suggestion with a short motivating note.

    Be warm, clear, realistic, and use positive, simple English.

    User Profile:
    {data}
    """

    try:
        response = gemini_model.generate_content(prompt)
        ai_response = response.text.strip()
        history_collection.insert_one({
            "action": "career_help",
            "form_data": data,
            "response": ai_response
        })
        return jsonify({"response": ai_response}), 200
    except Exception as e:
        print("Gemini API Error:", str(e))
        return jsonify({"error": "AI service error", "details": str(e)}), 500

# -----------------------------------------
@app.route('/awareness_bulletin', methods=['POST'])
def awareness_bulletin():
    data = request.get_json()
    city = data.get('city')
    if not city:
        return jsonify({"error": "City is required"}), 400
    
    prompt = f"""
    Create a welcoming, respectful community guide for individuals experiencing housing challenges in {city}.

    The bulletin should:
    - List important support programs, assistance centers, and helpful organizations.
    - Mention special rights, services, and opportunities available.
    - Give a simple guide on how to access help easily and with dignity.

    Use warm, hopeful, and positive English.
    Avoid terms like "homeless" — instead use "those navigating housing challenges".

    Keep the tone supportive and inspiring.
    """

    try:
        response = gemini_model.generate_content(prompt)
        ai_response = response.text.strip()
        history_collection.insert_one({
            "action": "awareness_bulletin",
            "city": city,
            "response": ai_response
        })
        return jsonify({"response": ai_response}), 200
    except Exception as e:
        print("Gemini API Error:", str(e))
        return jsonify({"error": "AI service error", "details": str(e)}), 500

# -----------------------------------------
@app.route('/user_history', methods=['GET'])
def get_user_history():
    user_actions = list(history_collection.find({}, {'_id': 0}))
    return jsonify(user_actions)

# -----------------------------------------
@app.route('/search_jobs', methods=['POST'])
def search_jobs():
    data = request.get_json()
    keyword = data.get('keyword')
    if keyword:
        query = {"position_description": {"$regex": keyword, "$options": "i"}}
    else:
        query = {}
    matches = list(businesses_collection.find(query, {'_id': 0}))
    return jsonify(matches)

# -----------------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)