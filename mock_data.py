# mock_data.py
# This mimics what Hardie's database will eventually provide
mock_patients = [
    {"id": 1, "name": "John Smith", "notes": "Encrypted_Note_A", "level": 2},
    {"id": 2, "name": "Sarah Johnson", "notes": "Encrypted_Note_B", "level": 1},
    {"id": 3, "name": "Michael Brown", "notes": "Encrypted_Note_C", "level": 4},
]

# This mimics the user table
mock_users = {
    "jsmith": {"role": "admin", "clearance": 4},
    "sjohnson": {"role": "data_manager", "clearance": 2},
    "kwong": {"role": "viewer", "clearance": 1}
}
