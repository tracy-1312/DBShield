# mock_data.py

# This mimics the 'users' table
# Roles: admin, data_manager, viewer
mock_users = {
    "jsmith": {
        "full_name": "John Smith",
        "role": "admin",
        "clearance_level": 4,
        "password_hash": "dummy_hash" 
    },
    "sjohnson": {
        "full_name": "Sarah Johnson",
        "role": "data_manager",
        "clearance_level": 2,
        "password_hash": "dummy_hash"
    },
    "kwong": {
        "full_name": "Karen Wong",
        "role": "viewer",
        "clearance_level": 1,
        "password_hash": "dummy_hash"
    }
}

# This mimics the 'patient_records' table
# classification_level: 1 (Low), 2 (Standard), 3 (Elevated), 4 (Restricted)
mock_patients = [
    {"id": 1, "patient_id": "PT-001", "full_name": "John Smith", "classification_level": 2, "medical_notes": "Note A"},
    {"id": 2, "patient_id": "PT-002", "full_name": "Sarah Johnson", "classification_level": 1, "medical_notes": "Note B"},
    {"id": 3, "patient_id": "PT-003", "full_name": "Michael Brown", "classification_level": 4, "medical_notes": "Note C"},
    {"id": 4, "patient_id": "PT-004", "full_name": "Aisha Patel", "classification_level": 3, "medical_notes": "Note D"},
]