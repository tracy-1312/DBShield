"""SQLAlchemy models mapped to Tracy's dbshield schema.

Three tables: users, patient_records, access_logs.
Column names and types match dbshield_schema.sql exactly.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from encryption import EncryptedText
from db import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    clearance_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    access_logs: Mapped[list["AccessLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.username} role={self.role} clearance={self.clearance_level}>"


class PatientRecord(Base):
    __tablename__ = "patient_records"

    record_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    category: Mapped[Optional[str]] = mapped_column(String(50))
    classification_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    contact_number: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(100))

    # Encrypted at rest in step 2 — stays Text, but holds a Fernet token
    # rather than readable notes.
    
    medical_notes: Mapped[Optional[str]] = mapped_column(EncryptedText)
    assigned_doctor: Mapped[Optional[str]] = mapped_column(String(100))
    last_modified: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<PatientRecord {self.patient_id} {self.full_name} class={self.classification_level}>"


class AccessLog(Base):
    __tablename__ = "access_logs"

    log_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    # Nullable because a search is not tied to a single record.
    record_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("patient_records.record_id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="access_logs")

    def __repr__(self) -> str:
        return f"<AccessLog user={self.user_id} {self.action}/{self.status}>"