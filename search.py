"""Filtered search and retrieval for DBShield.

Two-stage search. Stage one runs in SQL and applies the RBAC clearance
filter plus any structured filters, so records the user may not see are
never fetched. Stage two decrypts the survivors and matches keywords
against encrypted fields, which SQL cannot do.
"""

from typing import Optional

from sqlalchemy import or_

from db import get_session
from models import AccessLog, PatientRecord, User


def _scope_to_clearance(query, user: User):
    """Narrow a query to records the user's clearance permits.

    Admins see everything. Everyone else sees records classified at or
    below their own clearance level.
    """
    if user.role == "admin":
        return query
    return query.filter(PatientRecord.classification_level <= user.clearance_level)


def search_records(
    session,
    user: User,
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    max_classification: Optional[int] = None,
    search_notes: bool = False,
) -> list[PatientRecord]:
    """Return records matching the search, scoped to the user's clearance.

    keyword            matches patient_id, full_name or assigned_doctor
    category           exact match on category
    max_classification optional extra ceiling on top of the user's own
    search_notes       also match against decrypted medical_notes
    """
    query = session.query(PatientRecord)

    # RBAC first, so denied records never leave the database.
    query = _scope_to_clearance(query, user)

    if category:
        query = query.filter(PatientRecord.category == category)

    if max_classification is not None:
        query = query.filter(PatientRecord.classification_level <= max_classification)

    if keyword:
        pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                PatientRecord.patient_id.like(pattern),
                PatientRecord.full_name.like(pattern),
                PatientRecord.assigned_doctor.like(pattern),
            )
        )

    results = query.order_by(PatientRecord.patient_id).all()

    # Stage two: encrypted columns cannot be matched in SQL, so if the
    # keyword found nothing and notes were requested, re-run without the
    # keyword and match against decrypted text in Python.
    if keyword and search_notes and not results:
        candidates = _scope_to_clearance(session.query(PatientRecord), user)
        if category:
            candidates = candidates.filter(PatientRecord.category == category)
        needle = keyword.lower()
        results = [
            rec for rec in candidates.all()
            if rec.medical_notes and needle in rec.medical_notes.lower()
        ]

    log_action(session, user, "search", None, "success")
    return results


def get_record(session, user: User, record_id: int) -> Optional[PatientRecord]:
    """Fetch one record, or None if the user's clearance forbids it.

    A denied attempt is written to the audit log.
    """
    record = session.query(PatientRecord).filter_by(record_id=record_id).first()
    if record is None:
        return None

    if user.role != "admin" and record.classification_level > user.clearance_level:
        log_action(session, user, "denied", record_id, "denied")
        return None

    log_action(session, user, "view", record_id, "success")
    return record


def log_action(session, user: User, action: str, record_id, status: str) -> None:
    """Write an audit trail entry."""
    session.add(
        AccessLog(
            user_id=user.user_id,
            record_id=record_id,
            action=action,
            status=status,
        )
    )