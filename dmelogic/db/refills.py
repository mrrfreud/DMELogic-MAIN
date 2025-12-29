"""
refills.py — Repository functions for refill tracking.

This module handles queries for order items that are due for refills,
computing next_refill_due dates and filtering by date ranges.
"""

from __future__ import annotations

import sqlite3
from typing import List, Optional, TypedDict

from .base import get_connection
from dmelogic.config import debug_log


class RefillRow(TypedDict):
    """Type definition for a refill-due row returned by fetch_refills_due."""
    order_item_id: int
    order_id: int
    order_date: str
    patient_name: str
    patient_dob: str
    patient_phone: str
    hcpcs_code: str
    description: str
    refills_remaining: int
    day_supply: int
    last_filled_date: str
    next_refill_due: str
    days_until_due: int
    prescriber_name: str


def fetch_refills_due(
    start_date: str,
    end_date: str,
    today: str,
    folder_path: Optional[str] = None,
) -> List[RefillRow]:
    """
    Return refillable order items whose next refill due falls between
    [start_date, end_date] inclusive.

    Args:
        start_date: 'YYYY-MM-DD' - beginning of date range
        end_date: 'YYYY-MM-DD' - end of date range
        today: 'YYYY-MM-DD' - current date for computing days_until_due
        folder_path: Optional database folder path

    Returns:
        List of RefillRow dicts with order, patient, item, and computed refill info.

    Business Rules:
        - Only includes items with last_filled_date set
        - Only includes items with refills > 0
        - Computes next_refill_due as last_filled_date + day_supply days
        - Filters for next_refill_due between start_date and end_date
        - Sorted by next_refill_due, then patient name
    """
    try:
        conn = get_connection("orders.db", folder_path=folder_path)
        conn.row_factory = sqlite3.Row
        try:
            cur = conn.cursor()

            # Expression for next refill due: last_filled_date + day_supply days
            # We must repeat in WHERE; SQLite doesn't allow alias in WHERE
            next_due_expr = """
                date(
                    oi.last_filled_date,
                    printf('+%d days', CAST(oi.day_supply AS INTEGER))
                )
            """

            sql = f"""
            SELECT
                oi.rowid AS order_item_id,
                o.id      AS order_id,
                o.order_date,
                COALESCE(o.patient_name,
                         TRIM(o.patient_last_name || ', ' || o.patient_first_name)) AS patient_name,
                o.patient_dob,
                o.patient_phone,
                oi.hcpcs_code,
                oi.description,
                CAST(oi.refills AS INTEGER) AS refills_remaining,
                CAST(oi.day_supply AS INTEGER) AS day_supply,
                oi.last_filled_date,
                {next_due_expr} AS next_refill_due,
                CAST(julianday({next_due_expr}) - julianday(?) AS INTEGER) AS days_until_due,
                o.prescriber_name
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE
                oi.last_filled_date IS NOT NULL
                AND oi.last_filled_date != ''
                AND CAST(oi.refills AS INTEGER) > 0
                AND {next_due_expr} BETWEEN ? AND ?
            ORDER BY
                next_refill_due ASC,
                o.patient_last_name COLLATE NOCASE ASC,
                o.patient_first_name COLLATE NOCASE ASC
            """

            cur.execute(sql, (today, start_date, end_date))
            rows = cur.fetchall()

            result: List[RefillRow] = []
            for r in rows:
                result.append(
                    RefillRow(
                        order_item_id=r["order_item_id"],
                        order_id=r["order_id"],
                        order_date=r["order_date"] or "",
                        patient_name=r["patient_name"] or "",
                        patient_dob=r["patient_dob"] or "",
                        patient_phone=r["patient_phone"] or "",
                        hcpcs_code=r["hcpcs_code"] or "",
                        description=r["description"] or "",
                        refills_remaining=int(r["refills_remaining"] or 0),
                        day_supply=int(r["day_supply"] or 0),
                        last_filled_date=r["last_filled_date"] or "",
                        next_refill_due=r["next_refill_due"] or "",
                        days_until_due=int(r["days_until_due"] or 0),
                        prescriber_name=r["prescriber_name"] or "",
                    )
                )
            return result
        finally:
            conn.close()
    except Exception as e:
        debug_log(f"DB Error in fetch_refills_due: {e}")
        return []
