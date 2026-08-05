"""Populate medical_notes with sample data.

Values are written through the model, so EncryptedText encrypts them
automatically on the way into MySQL.
"""

from backend.db import get_session
from backend.models import PatientRecord

NOTES = {
    "PT-00123": "Routine check-up. Blood pressure slightly elevated, monitor at next visit.",
    "PT-00456": "History of arrhythmia. Currently on beta blockers, responding well.",
    "PT-00789": "Stage II diagnosis confirmed. Chemotherapy cycle 3 of 6 completed.",
    "PT-00234": "Childhood asthma, well controlled with inhaler. No recent episodes.",
    "PT-00567": "Post-operative recovery following neurosurgery. Weekly review required.",
    "PT-00891": "No significant history. Annual screening completed, results normal.",
    "PT-00902": "Family history of cardiac disease. Statins prescribed as a precaution.",
    "PT-00913": "Ongoing treatment. Referred to specialist oncology unit for review.",
    "PT-00924": "Immunisations up to date. Mild seasonal allergies noted.",
    "PT-00935": "Early-stage cognitive decline observed. Six-month reassessment scheduled.",
}

with get_session() as session:
    for patient_id, note in NOTES.items():
        record = session.query(PatientRecord).filter_by(patient_id=patient_id).first()
        if record:
            record.medical_notes = note
            print(f"encrypted notes for {patient_id}")