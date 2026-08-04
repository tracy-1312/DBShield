from flask import Flask, request, jsonify, session
from mock_data import mock_users, mock_patients

app = Flask(__name__)
app.secret_key = "super_secret_key_for_now" # Replace with .env later

# --- THE BRAIN: Permission Checker ---
def can_user_access_record(user_role, user_clearance, record_level):
    """
    Logic based on A3 Requirements:
    Admin: Everything
    Data Manager: Only if record level <= their clearance
    Viewer: Only if record level is 1
    """
    if user_role == 'admin':
        return True
    elif user_role == 'data_manager':
        return record_level <= user_clearance
    elif user_role == 'viewer':
        return record_level == 1
    return False

# --- ROUTE 1: Login ---
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # For now, we just check if the username exists in our mock_users
    if username in mock_users and password == "password123": # Hardcoded for now
        user_data = mock_users[username]
        session['user_id'] = username
        session['role'] = user_data['role']
        session['clearance_level'] = user_data['clearance_level']
        return jsonify({"status": "success", "message": f"Welcome {user_data['full_name']}"}), 200
    else:
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

# --- ROUTE 2: Search & Filter (The Core Requirement) ---
@app.route('/search', methods=['GET'])
def search_records():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Please login first"}), 401

    query = request.args.get('q', '').lower()
    user_role = session['role']
    user_clearance = session['clearance_level']
    
    results = []

    # Filter the mock_patients based on search query AND permissions
    for p in mock_patients:
        # 1. Check if it matches the search keyword
        if query in p['full_name'].lower() or query in p['patient_id'].lower():
            
            # 2. Check if the user is allowed to see it
            if can_user_access_record(user_role, user_clearance, p['classification_level']):
                results.append(p)
            else:
                # Log as a 'denied' attempt for audit log
                print(f"Access Denied: User {session['user_id']} tried to see Record {p['id']}")

    return jsonify({
        "status": "success",
        "count": len(results),
        "data": results
    })

# --- ROUTE 3: Logout ---
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"status": "success", "message": "Logged out"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
