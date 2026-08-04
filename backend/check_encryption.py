"""Show that notes are ciphertext in MySQL but plaintext through the model."""

from sqlalchemy import text

from backend.db import get_session
from backend.models import PatientRecord

with get_session() as session:
    print("=== RAW SQL — what is actually stored on disk ===")
    rows = session.execute(
        text("SELECT patient_id, medical_notes FROM patient_records LIMIT 3")
    ).fetchall()
    for patient_id, notes in rows:
        print(f"{patient_id}: {str(notes)[:70]}...")

    print("\n=== THROUGH THE MODEL — decrypted automatically ===")
    for rec in session.query(PatientRecord).limit(3).all():
        print(f"{rec.patient_id}: {rec.medical_notes}")