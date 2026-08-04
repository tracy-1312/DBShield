from flask import Flask, request, jsonify, session
from backend.db import get_session
from backend.models import User
from backend.search import search_records
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # Use the User model from models.py
    with get_session() as session:
        user = session.query(User).filter_by(username=username).first()
        
        # Simple check for now (Hardie will handle the bcrypt part)
        if user and password == "password123": 
            session['user_id'] = user.user_id
            session['role'] = user.role
            session['clearance_level'] = user.clearance_level
            return jsonify({"status": "success", "message": f"Welcome {user.full_name}"}), 200
    
    return jsonify({"status": "error", "message": "Invalid credentials"}), 401

@app.route('/search', methods=['GET'])
def search_records():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Please login first"}), 401

    # Get the user object from the session
    with get_session() as session:
        user = session.query(User).filter_by(user_id=session['user_id']).first()
        
        # Call the search function from search.py
        # This handles RBAC, SQL filtering, and Decryption 
        results = search_records(
            session, 
            user, 
            keyword=request.args.get('q'),
            search_notes=True
        )
        
        # Convert SQLAlchemy objects to JSON-friendly dictionaries
        # (might need a small helper here, but this is the goal)
        return jsonify({
            "status": "success",
            "count": len(results),
            "data": [r.to_dict() if hasattr(r, 'to_dict') else vars(r) for r in results]
        })

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success", "message": "Logged out"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
