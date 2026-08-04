from backend.db import get_session
from backend.models import AccessLog, PatientRecord, User

with get_session() as session:
    print(f"users:           {session.query(User).count()}")
    print(f"patient_records: {session.query(PatientRecord).count()}")
    print(f"access_logs:     {session.query(AccessLog).count()}")
    print()
    for user in session.query(User).order_by(User.clearance_level.desc()).all():
        print(f"  {user.username:10} {user.role:14} clearance {user.clearance_level}")
    print()
    for rec in session.query(PatientRecord).limit(3).all():
        print(f"  {rec.patient_id}  {rec.full_name:16} class {rec.classification_level}")