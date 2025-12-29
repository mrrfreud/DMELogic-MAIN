from __future__ import annotations

import sqlite3
from typing import List, Optional

from .base import get_connection
from .models import Patient, PatientInsurance
from .converters import row_to_patient
from dmelogic.config import debug_log


def fetch_all_patients(folder_path: Optional[str] = None) -> List[sqlite3.Row]:
    """
    Return all patients ordered by last_name, first_name.
    Returns sqlite3.Row objects (dict-like, subscriptable).
    """
    try:
        conn = get_connection("patients.db", folder_path=folder_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT *
                FROM patients
                ORDER BY last_name COLLATE NOCASE ASC,
                         first_name COLLATE NOCASE ASC,
                         dob ASC
                """
            )
            rows = cur.fetchall()
            return rows
        finally:
            conn.close()
    except Exception as e:
        debug_log(f"DB Error in fetch_all_patients: {e}")
        return []


def fetch_patient_by_id(patient_id: int, folder_path: Optional[str] = None) -> Optional[sqlite3.Row]:
    """
    Fetch a single patient by primary-key id.
    Returns sqlite3.Row object (dict-like, subscriptable).
    """
    try:
        conn = get_connection("patients.db", folder_path=folder_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
            row = cur.fetchone()
            return row
        finally:
            conn.close()
    except Exception as e:
        debug_log(f"DB Error in fetch_patient_by_id({patient_id}): {e}")
        return None


def find_patient_by_name_and_dob(
    last_name: str,
    first_name: str,
    dob: Optional[str] = None,
    folder_path: Optional[str] = None
) -> Optional[sqlite3.Row]:
    """
    Find a patient by name and optional DOB.
    Returns sqlite3.Row object (dict-like, subscriptable) or None if not found.
    
    Args:
        last_name: Patient's last name (case-insensitive)
        first_name: Patient's first name (case-insensitive)
        dob: Optional date of birth for disambiguation
        folder_path: Optional database folder path
    
    Returns:
        sqlite3.Row with full patient record or None
    """
    try:
        conn = get_connection("patients.db", folder_path=folder_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            if dob:
                cur.execute(
                    """
                    SELECT * FROM patients
                    WHERE UPPER(last_name) = UPPER(?)
                      AND UPPER(first_name) = UPPER(?)
                      AND dob = ?
                    LIMIT 1
                    """,
                    (last_name, first_name, dob)
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM patients
                    WHERE UPPER(last_name) = UPPER(?)
                      AND UPPER(first_name) = UPPER(?)
                    LIMIT 1
                    """,
                    (last_name, first_name)
                )
            return cur.fetchone()
        finally:
            conn.close()
    except Exception as e:
        debug_log(f"DB Error in find_patient_by_name_and_dob({last_name}, {first_name}): {e}")
        return None


def fetch_patient_insurance(
    last_name: str,
    first_name: str,
    dob: Optional[str] = None,
    folder_path: Optional[str] = None
) -> Optional[PatientInsurance]:
    """
    Fetch patient insurance information by name and optional DOB.
    Returns typed PatientInsurance model with all insurance fields.
    """
    conn = get_connection("patients.db", folder_path=folder_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        if dob:
            cur.execute(
                """
                SELECT
                    primary_insurance,
                    policy_number,
                    group_number,
                    secondary_insurance,
                    secondary_insurance_id,
                    primary_insurance_id,
                    address,
                    city,
                    state,
                    zip_code
                FROM patients
                WHERE UPPER(last_name) = UPPER(?)
                  AND UPPER(first_name) = UPPER(?)
                  AND dob = ?
                LIMIT 1
                """,
                (last_name, first_name, dob)
            )
        else:
            cur.execute(
                """
                SELECT
                    primary_insurance,
                    policy_number,
                    group_number,
                    secondary_insurance,
                    secondary_insurance_id,
                    primary_insurance_id,
                    address,
                    city,
                    state,
                    zip_code
                FROM patients
                WHERE UPPER(last_name) = UPPER(?)
                  AND UPPER(first_name) = UPPER(?)
                LIMIT 1
                """,
                (last_name, first_name)
            )
        row = cur.fetchone()
        if not row:
            return None
        
        # Return as PatientInsurance dataclass
        return PatientInsurance(
            primary_insurance=row["primary_insurance"],
            policy_number=row["policy_number"],
            group_number=row["group_number"],
            secondary_insurance=row["secondary_insurance"],
            secondary_insurance_id=row["secondary_insurance_id"],
            primary_insurance_id=row["primary_insurance_id"],
            address=row["address"],
            city=row["city"],
            state=row["state"],
            zip_code=row["zip_code"],
        )
    finally:
        conn.close()


def search_patients(search_term: str, folder_path: Optional[str] = None) -> List[dict]:
    """
    Search patients by name (first or last).
    Returns list of dicts with patient info.
    """
    try:
        conn = get_connection("patients.db", folder_path=folder_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()
            like = f"%{search_term}%"
            cur.execute(
                """
                SELECT id, first_name, last_name, dob, phone, address
                FROM patients
                WHERE first_name LIKE ? OR last_name LIKE ?
                   OR (first_name || ' ' || last_name) LIKE ?
                ORDER BY last_name, first_name
                LIMIT 50
                """,
                (like, like, like)
            )
            return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
    except Exception as e:
        debug_log(f"DB Error in search_patients: {e}")
        return []


def get_patient(patient_id: int, folder_path: Optional[str] = None) -> Optional[dict]:
    """Get patient by ID as dict."""
    row = fetch_patient_by_id(patient_id, folder_path)
    return dict(row) if row else None
