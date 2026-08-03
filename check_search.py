"""Show the same search returning different results per user clearance."""

from db import get_session
from models import User
from search import get_record, search_records

with get_session() as session:
    for username in ("jsmith", "mbrown", "kwong"):
        user = session.query(User).filter_by(username=username).first()
        results = search_records(session, user)
        print(f"\n{user.username} ({user.role}, clearance {user.clearance_level}) "
              f"sees {len(results)} of 10 records")
        for rec in results:
            print(f"   {rec.patient_id}  {rec.full_name:16} class {rec.classification_level}")

    print("\n=== keyword search on an encrypted field ===")
    admin = session.query(User).filter_by(username="jsmith").first()
    hits = search_records(session, admin, keyword="cardiac", search_notes=True)
    for rec in hits:
        print(f"   {rec.patient_id}: {rec.medical_notes}")

    print("\n=== denied access is logged ===")
    kwong = session.query(User).filter_by(username="kwong").first()
    print("   kwong requesting record 5 (classification 4):",
          get_record(session, kwong, 5))