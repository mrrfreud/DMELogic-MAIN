"""
Rx PDF Parser
=============
Extracts structured prescription data from pharmacy Rx PDFs.

Handles the common e-Rx format your pharmacy system generates:
  - Pres: Name (Title)
  - Patient: Last, First
  - DOB: MM/DD/YYYY
  - Drug: DRUG NAME
  - Qty: N
  - Refills: N
  - ICD10 CODE
  - NPI# XXXXXXXXXX
  - Rx date

Supports multiple prescriptions in a single PDF.

Usage:
    from dmelogic.services.rx_parser import RxParser, ParsedRx

    parser = RxParser()
    results: list[ParsedRx] = parser.parse_pdf("/path/to/file.pdf")
    # or parse raw text:
    results = parser.parse_text(raw_text)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class ParsedRxItem:
    """Single item/drug extracted from an Rx block."""
    drug_name: str = ""
    quantity: float = 0
    refills: int = 0
    days_supply: int = 0
    directions: str = ""
    unit: str = "Each"


@dataclass
class ParsedPrescriber:
    """Prescriber info extracted from Rx."""
    full_name: str = ""          # e.g. "Kalpana Pethe"
    title: str = ""              # e.g. "MD"
    first_name: str = ""
    last_name: str = ""
    npi: str = ""
    phone: str = ""
    fax: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""
    practice_name: str = ""
    license_number: str = ""
    dea_number: str = ""


@dataclass
class ParsedPatient:
    """Patient info extracted from Rx."""
    full_name: str = ""          # e.g. "Bah, Mariama"
    first_name: str = ""
    last_name: str = ""
    dob: str = ""                # MM/DD/YYYY
    gender: str = ""
    phone: str = ""
    fax: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""


@dataclass
class ParsedRx:
    """Complete parsed prescription — one per Rx block in the PDF."""
    patient: ParsedPatient = field(default_factory=ParsedPatient)
    prescriber: ParsedPrescriber = field(default_factory=ParsedPrescriber)
    item: ParsedRxItem = field(default_factory=ParsedRxItem)
    icd_codes: List[str] = field(default_factory=list)
    rx_date: str = ""
    rx_number: str = ""
    source_text: str = ""        # raw text of this block for debugging


class RxParser:
    """
    Parses prescription PDF text into structured ParsedRx objects.
    
    The parser is designed to handle the common e-Rx format from
    pharmacy systems (SureScripts, etc.). It splits multi-Rx PDFs
    into individual blocks and extracts each one.
    """

    # Regex patterns for data extraction
    _PAT_PRESCRIBER = re.compile(
        r"Pres:\s*(.+?)(?:\s*\((\w+)\))?$", re.MULTILINE
    )
    _PAT_NPI = re.compile(r"NPI#?\s*(\d{10})")
    _PAT_PATIENT = re.compile(
        r"Patient:[ \t]*(.+?)$", re.MULTILINE
    )
    _PAT_DOB = re.compile(r"DOB:[ \t]*(\d{1,2}/\d{1,2}/\d{4})")
    _PAT_GENDER = re.compile(r"Gender:[ \t]*([MF])")
    _PAT_ADDRESS = re.compile(
        r"Address:[ \t]*(.+?)$", re.MULTILINE
    )
    _PAT_DRUG = re.compile(r"Drug:[ \t]*(.+?)$", re.MULTILINE)
    _PAT_QTY = re.compile(r"Qty:[ \t]*([\d,.]+)")
    _PAT_REFILLS = re.compile(r"Refills:[ \t]*(\d+)")
    _PAT_DAYS = re.compile(r"Days:[ \t]*(\d+)")
    _PAT_SIG = re.compile(r"Sig:[ \t]*(.+?)$", re.MULTILINE)
    _PAT_ICD = re.compile(r"ICD-?10[:\s]*([A-Z]\d{2,3}\.?\d{0,4})", re.IGNORECASE)
    _PAT_DIAG = re.compile(r"Diag:\s*([A-Z]\d{2,4}\.?\d{0,4})", re.IGNORECASE)
    _PAT_RX_DATE = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})\s*$", re.MULTILINE)
    _PAT_PHONE = re.compile(r"(?:Phone|Phn):\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
    _PAT_FAX = re.compile(r"Fax:\s*\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
    _PAT_PRESCRIBER_PHONE = re.compile(r"\((\d{3})\)(\d{3})-(\d{4})")
    _PAT_EFF_DATE = re.compile(r"Eff\.Date:\s*(\d{1,2}/\d{1,2}/\d{4})")
    _PAT_RX_NUM = re.compile(r"Rx#:\s*(\S+)")

    # Block splitter — each "Pres:" starts a new Rx block
    _PAT_BLOCK_SPLIT = re.compile(r"(?=Pres:\s)")

    def parse_pdf(self, pdf_path: str) -> List[ParsedRx]:
        """
        Extract text from a PDF file and parse all Rx blocks.
        
        Uses PyMuPDF (fitz) if available, falls back to pdfplumber,
        then basic pdfminer.
        """
        text = self._extract_pdf_text(pdf_path)
        if not text.strip():
            return []
        return self.parse_text(text)

    def parse_text(self, text: str) -> List[ParsedRx]:
        """
        Parse raw text containing one or more Rx blocks.
        Returns a list of ParsedRx objects.
        Supports both e-Rx (SureScripts) and pharmacy fax request formats.
        """
        # Try e-Rx format first: split on "Pres:" boundaries
        blocks = self._PAT_BLOCK_SPLIT.split(text)
        blocks = [b.strip() for b in blocks if b.strip() and "Pres:" in b]

        results: List[ParsedRx] = []
        for block in blocks:
            parsed = self._parse_block(block)
            if parsed and (parsed.item.drug_name or parsed.patient.last_name):
                results.append(parsed)

        if results:
            return results

        # Fallback: try pharmacy fax/request format
        results = self._parse_fax_format(text)
        return results

    def _parse_block(self, block: str) -> Optional[ParsedRx]:
        """Parse a single Rx block into a ParsedRx."""
        rx = ParsedRx(source_text=block)
        lines = block.split("\n")
        lines_stripped = [l.strip() for l in lines]

        # Build a lookup: for any label line, the value may be on the
        # PREVIOUS line (PDF column extraction) or on the SAME line.
        def _value_before_or_after(label: str) -> str:
            """Find the value for a label that may be on the line before or after."""
            for i, line in enumerate(lines_stripped):
                if line.startswith(label):
                    inline = line[len(label):].strip().strip(":")
                    if inline:
                        return inline
                    # Value on previous line
                    if i > 0 and lines_stripped[i - 1]:
                        return lines_stripped[i - 1]
                    # Value on next line
                    if i + 1 < len(lines_stripped) and lines_stripped[i + 1]:
                        return lines_stripped[i + 1]
            return ""

        # ---- Prescriber ----
        pres_match = self._PAT_PRESCRIBER.search(block)
        if pres_match:
            full_name = pres_match.group(1).strip()
            title = pres_match.group(2) or ""
            rx.prescriber.full_name = full_name
            rx.prescriber.title = title
            # Split name: "Kalpana Pethe" → first=Kalpana, last=Pethe
            parts = full_name.split()
            if len(parts) >= 2:
                rx.prescriber.first_name = parts[0]
                rx.prescriber.last_name = " ".join(parts[1:])
            elif parts:
                rx.prescriber.last_name = parts[0]

        # NPI
        npi_match = self._PAT_NPI.search(block)
        if npi_match:
            rx.prescriber.npi = npi_match.group(1)
        else:
            # Value-before-label fallback for NPI
            npi_val = _value_before_or_after("NPI#")
            if npi_val:
                npi_digits = re.search(r"\d{10}", npi_val)
                if npi_digits:
                    rx.prescriber.npi = npi_digits.group(0)

        # Prescriber phone/fax — grab first two phone patterns
        phones = self._PAT_PRESCRIBER_PHONE.findall(block)
        if phones:
            rx.prescriber.phone = f"({phones[0][0]}){phones[0][1]}-{phones[0][2]}"
            if len(phones) > 1:
                rx.prescriber.fax = f"({phones[1][0]}){phones[1][1]}-{phones[1][2]}"

        # Prescriber address — lines between Pres: and Patient:
        pres_idx = block.find("Pres:")
        pat_idx = block.find("Patient:")
        if pres_idx >= 0 and pat_idx > pres_idx:
            addr_lines = block[pres_idx:pat_idx].strip().split("\n")
            # Skip first line (Pres: name) and phone lines
            addr_parts = []
            for line in addr_lines[1:]:
                line = line.strip()
                if line and not line.startswith(("LIC", "Fax", "DEA", "Rx#", "(", "Phn")):
                    addr_parts.append(line)
            if addr_parts:
                # Try to parse "21 Audubon Ave, 2nd Fl\nNew York, NY 100322249"
                full_addr = " ".join(addr_parts)
                rx.prescriber.address = full_addr
                # Extract city/state/zip from last part
                csz = re.search(r"([A-Za-z\s]+),\s*([A-Z]{2})\s*(\d{5,9})", full_addr)
                if csz:
                    rx.prescriber.city = csz.group(1).strip()
                    rx.prescriber.state = csz.group(2)
                    rx.prescriber.zip_code = csz.group(3)

        # ---- Patient ----
        pat_match = self._PAT_PATIENT.search(block)
        if pat_match:
            name_raw = pat_match.group(1).strip()
            if not name_raw:
                # Value may be on the line before "Patient:"
                name_raw = _value_before_or_after("Patient:")
            rx.patient.full_name = name_raw
            if "," in name_raw:
                parts = [p.strip() for p in name_raw.split(",", 1)]
                rx.patient.last_name = parts[0]
                rx.patient.first_name = parts[1] if len(parts) > 1 else ""
            else:
                parts = name_raw.split()
                if len(parts) >= 2:
                    rx.patient.first_name = parts[0]
                    rx.patient.last_name = " ".join(parts[1:])
        else:
            # Try line-before-label fallback
            name_raw = _value_before_or_after("Patient:")
            if name_raw:
                rx.patient.full_name = name_raw
                if "," in name_raw:
                    parts = [p.strip() for p in name_raw.split(",", 1)]
                    rx.patient.last_name = parts[0]
                    rx.patient.first_name = parts[1] if len(parts) > 1 else ""

        dob_match = self._PAT_DOB.search(block)
        if dob_match:
            rx.patient.dob = dob_match.group(1)
        else:
            # DOB may be on line before "DOB:"
            dob_raw = _value_before_or_after("DOB:")
            dob_m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", dob_raw)
            if dob_m:
                rx.patient.dob = dob_m.group(1)

        gender_match = self._PAT_GENDER.search(block)
        if gender_match:
            rx.patient.gender = gender_match.group(1)
        else:
            # Gender may be on line before "Gender"
            g_raw = _value_before_or_after("Gender")
            gm = re.match(r"^([MF])$", g_raw.strip())
            if gm:
                rx.patient.gender = gm.group(1)

        # Patient address
        addr_match = self._PAT_ADDRESS.search(block)
        addr_raw = ""
        csz_line = ""
        if addr_match:
            addr_raw = addr_match.group(1).strip()
        if not addr_raw:
            # Value may be on line before "Address:" with city/state on next line
            street = ""
            csz_line = ""
            for i, line in enumerate(lines_stripped):
                if line.startswith("Address:"):
                    # Street on previous line
                    if i > 0 and lines_stripped[i - 1]:
                        street = lines_stripped[i - 1]
                    # City/state/zip on next line
                    if i + 1 < len(lines_stripped) and lines_stripped[i + 1]:
                        csz_line = lines_stripped[i + 1]
                    # Check if street actually looks like city/state/zip, swap
                    if street and re.search(r"[A-Z]{2}\s+\d{5}", street):
                        csz_line, street = street, csz_line
                    if street and csz_line:
                        addr_raw = street + ", " + csz_line
                    elif street:
                        addr_raw = street
                    elif csz_line:
                        addr_raw = csz_line
                    break
        if addr_raw:
            rx.patient.address = addr_raw
            # Try to extract city/state/zip from the csz_line directly
            csz = None
            if csz_line:
                csz = re.search(r"([A-Za-z][A-Za-z\s]+),\s*([A-Z]{2})\s*(\d{5,9})", csz_line)
            if not csz:
                # Fallback: try on full addr_raw but require city >= 2 chars
                csz = re.search(r"([A-Za-z]{2}[A-Za-z\s]*),\s*([A-Z]{2})\s*(\d{5,9})", addr_raw)
            if csz:
                rx.patient.city = csz.group(1).strip()
                rx.patient.state = csz.group(2)
                rx.patient.zip_code = csz.group(3)
                # Address is everything before city
                city_idx = addr_raw.find(csz.group(1))
                if city_idx > 0:
                    rx.patient.address = addr_raw[:city_idx].strip().rstrip(",")

        # Patient phone — look for phone near patient section
        # Look after "Patient:" block for phone patterns
        pat_section_start = block.find("Patient:")
        drug_start = block.find("Drug:")
        if pat_section_start >= 0:
            end = drug_start if drug_start > pat_section_start else len(block)
            pat_section = block[pat_section_start:end]
            phone_m = re.search(r"Phone:\s*\((\d{3})\)(\d{3})-(\d{4})", pat_section)
            if phone_m:
                rx.patient.phone = f"({phone_m.group(1)}){phone_m.group(2)}-{phone_m.group(3)}"

        # Pharmacy-section patient phone (bottom of block)
        bottom_phone = re.search(r"Phone:\s*\((\d{3})\)(\d{3})-(\d{4})\s*Fax:", block[max(0, len(block)-400):])
        if bottom_phone:
            rx.patient.phone = f"({bottom_phone.group(1)}){bottom_phone.group(2)}-{bottom_phone.group(3)}"

        # Value-before-label fallback for phone  
        if not rx.patient.phone:
            # Search bottom portion for "phone-number\nPhone" pattern
            phone_pattern = re.search(
                r"\((\d{3})\)(\d{3})-(\d{4})\s*\n\s*Phone\b",
                block[max(0, len(block) - 500):]
            )
            if phone_pattern:
                rx.patient.phone = f"({phone_pattern.group(1)}){phone_pattern.group(2)}-{phone_pattern.group(3)}"

        # ---- Drug/Item ----
        drug_match = self._PAT_DRUG.search(block)
        if drug_match:
            drug_raw = drug_match.group(1).strip()
            # Verify it's actually a drug name (not a phone number)
            if drug_raw and not re.match(r"^\(?\d{3}\)?[-.\s]?\d{3}", drug_raw):
                rx.item.drug_name = drug_raw
            else:
                # Value on previous line
                drug_raw = _value_before_or_after("Drug:")
                if drug_raw and not re.match(r"^\(?\d{3}\)?[-.\s]?\d{3}", drug_raw):
                    rx.item.drug_name = drug_raw
        else:
            drug_raw = _value_before_or_after("Drug:")
            if drug_raw and not re.match(r"^\(?\d{3}\)?[-.\s]?\d{3}", drug_raw):
                rx.item.drug_name = drug_raw

        qty_match = self._PAT_QTY.search(block)
        if qty_match:
            try:
                rx.item.quantity = float(qty_match.group(1).replace(",", ""))
            except ValueError:
                rx.item.quantity = 0
        else:
            # For Qty, try both before and after label, prefer larger value
            qty_val = 0
            for i, line in enumerate(lines_stripped):
                if line.startswith("Qty:"):
                    # Try before
                    if i > 0:
                        qm = re.search(r"([\d,.]+)", lines_stripped[i - 1])
                        if qm:
                            try:
                                qty_val = float(qm.group(1).replace(",", ""))
                            except ValueError:
                                pass
                    # Try after — prefer this if it's a meaningful number
                    if i + 1 < len(lines_stripped):
                        qm2 = re.search(r"([\d,.]+)", lines_stripped[i + 1])
                        if qm2:
                            try:
                                after_val = float(qm2.group(1).replace(",", ""))
                                if after_val > qty_val:
                                    qty_val = after_val
                            except ValueError:
                                pass
                    break
            if qty_val > 0:
                rx.item.quantity = qty_val

        refill_match = self._PAT_REFILLS.search(block)
        if refill_match:
            rx.item.refills = int(refill_match.group(1))
        else:
            # PDF text extraction often puts "Refills:" on its own line
            # with the value on the next (or previous) line.
            # Check AFTER first (more reliable), then BEFORE.
            # Limit to 1-2 digits to avoid capturing NPI/IDs.
            for i, line in enumerate(lines_stripped):
                if line.startswith("Refills:"):
                    # Inline value after colon on same line
                    rest = line[len("Refills:"):].strip()
                    if rest and re.match(r"^\d{1,2}$", rest):
                        rx.item.refills = int(rest)
                        break
                    # Try after first (value below label)
                    if i + 1 < len(lines_stripped):
                        rm = re.match(r"^(\d{1,2})$", lines_stripped[i + 1])
                        if rm:
                            rx.item.refills = int(rm.group(1))
                            break
                    # Try before (value above label)
                    if i > 0:
                        rm = re.match(r"^(\d{1,2})$", lines_stripped[i - 1])
                        if rm:
                            rx.item.refills = int(rm.group(1))
                    break

        days_match = self._PAT_DAYS.search(block)
        if days_match:
            try:
                rx.item.days_supply = int(days_match.group(1))
            except ValueError:
                pass
        else:
            # Value-before-or-after fallback for Days
            for i, line in enumerate(lines_stripped):
                if line.startswith("Days:"):
                    if i > 0:
                        dm = re.search(r"([\d,.]+)", lines_stripped[i - 1])
                        if dm:
                            try:
                                rx.item.days_supply = int(float(dm.group(1).replace(",", "")))
                            except ValueError:
                                pass
                    if not rx.item.days_supply and i + 1 < len(lines_stripped):
                        dm = re.search(r"([\d,.]+)", lines_stripped[i + 1])
                        if dm:
                            try:
                                rx.item.days_supply = int(float(dm.group(1).replace(",", "")))
                            except ValueError:
                                pass
                    break

        sig_match = self._PAT_SIG.search(block)
        if sig_match:
            rx.item.directions = sig_match.group(1).strip()
        if not rx.item.directions or rx.item.directions in ("Rx", "Sig"):
            # For Sig, prefer line AFTER label (directions are usually after)
            for i, line in enumerate(lines_stripped):
                if line.startswith("Sig:"):
                    # Check line after first (preferred for directions)
                    if i + 1 < len(lines_stripped) and lines_stripped[i + 1]:
                        candidate = lines_stripped[i + 1]
                        # Skip if it looks like boilerplate
                        if not candidate.startswith("This Prescription"):
                            rx.item.directions = candidate
                            break
                    # Fallback to line before
                    if i > 0 and lines_stripped[i - 1] and lines_stripped[i - 1] not in ("Rx", "Sig"):
                        rx.item.directions = lines_stripped[i - 1]
                    break

        # ---- ICD codes ----
        icd_codes = set()
        for m in self._PAT_ICD.finditer(block):
            code = m.group(1).upper()
            # Normalize: ensure dot format (N3941 → N39.41)
            if "." not in code and len(code) > 3:
                code = code[:3] + "." + code[3:]
            icd_codes.add(code)
        for m in self._PAT_DIAG.finditer(block):
            code = m.group(1).upper()
            if "." not in code and len(code) > 3:
                code = code[:3] + "." + code[3:]
            icd_codes.add(code)
        # Also extract DX: codes from Sig line or anywhere in block
        for m in re.finditer(r"DX:\s*([A-Z]\d{2,3}\.?\d{0,4}(?:\s*,\s*[A-Z]\d{2,3}\.?\d{0,4})*)", block, re.IGNORECASE):
            for code_str in m.group(1).split(","):
                code = code_str.strip().upper()
                if code and re.match(r"[A-Z]\d{2,3}\.?\d{0,4}$", code):
                    if "." not in code and len(code) > 3:
                        code = code[:3] + "." + code[3:]
                    icd_codes.add(code)
        # Also try value-before-label for Diag:
        if not icd_codes:
            diag_val = _value_before_or_after("Diag:")
            if diag_val:
                code = diag_val.strip().upper()
                if re.match(r"[A-Z]\d{2,4}\.?\d{0,4}$", code):
                    if "." not in code and len(code) > 3:
                        code = code[:3] + "." + code[3:]
                    icd_codes.add(code)
        rx.icd_codes = sorted(icd_codes)

        # ---- Rx date ----
        eff_match = self._PAT_EFF_DATE.search(block)
        if eff_match:
            rx.rx_date = eff_match.group(1)
        else:
            # Look for Signature Date line with date
            sig_date = re.search(r"Signature\s+Date\s*\n?\s*.*?\n?\s*(\d{1,2}/\d{1,2}/\d{4})", block)
            if sig_date:
                rx.rx_date = sig_date.group(1)
            else:
                # Last resort: find date patterns near "02/16/2026"
                dates = re.findall(r"\d{1,2}/\d{1,2}/\d{4}", block)
                if dates:
                    rx.rx_date = dates[-1]  # Usually the Rx date is last

        # Rx number
        rxnum_match = self._PAT_RX_NUM.search(block)
        if rxnum_match:
            rx.rx_number = rxnum_match.group(1)

        # Practice name — look for it in bottom section
        practice = re.search(r"^([A-Z][A-Za-z\s]+(?:Practice|Clinic|Medical|Health|Associates).*?)$", block, re.MULTILINE)
        if practice:
            rx.prescriber.practice_name = practice.group(1).strip()

        return rx

    # ------------------------------------------------------------------ Fax format parser

    def _parse_fax_format(self, text: str) -> List[ParsedRx]:
        """
        Parse a pharmacy fax/request letter format.
        
        Format:
            TO:
            PRESCRIBER_NAME, TITLE
            ...
            Patient: LAST, FIRST
            DOB:
            MM/DD/YYYY
            Address: STREET
            CITY, STATE, ZIP
            Phone:
            PHONE_NUMBER
            ...
            REQUESTED ITEMS (Monthly Usage):
            • ITEM NAME
            Qty/Month: N
        """
        lines = text.split("\n")
        lines_stripped = [l.strip() for l in lines]

        rx_base = ParsedRx(source_text=text)

        # ---- Prescriber from "TO:" section ----
        for i, line in enumerate(lines_stripped):
            if line == "TO:" and i + 1 < len(lines_stripped):
                pres_line = lines_stripped[i + 1].strip()
                if pres_line:
                    rx_base.prescriber.full_name = pres_line
                    # Parse "KRATZ, NATHANIEL, MD" or "GABRIELA KREBS, NP"
                    # Try LAST, FIRST, TITLE
                    parts = [p.strip() for p in pres_line.split(",")]
                    if len(parts) >= 3:
                        rx_base.prescriber.last_name = parts[0]
                        rx_base.prescriber.first_name = parts[1]
                        rx_base.prescriber.title = parts[2]
                    elif len(parts) == 2:
                        # Could be "LAST, FIRST" or "FIRST LAST, TITLE"
                        maybe_title = parts[1].strip()
                        if maybe_title in ("MD", "DO", "NP", "PA", "DPM", "OD", "DDS", "PhD", "RN", "APRN", "PA-C"):
                            # "GABRIELA KREBS, NP" → first=GABRIELA, last=KREBS
                            name_parts = parts[0].split()
                            if len(name_parts) >= 2:
                                rx_base.prescriber.first_name = name_parts[0]
                                rx_base.prescriber.last_name = " ".join(name_parts[1:])
                            rx_base.prescriber.title = maybe_title
                        else:
                            rx_base.prescriber.last_name = parts[0]
                            rx_base.prescriber.first_name = parts[1]
                    else:
                        name_parts = pres_line.split()
                        if len(name_parts) >= 2:
                            rx_base.prescriber.first_name = name_parts[0]
                            rx_base.prescriber.last_name = " ".join(name_parts[1:])
                break

        # ---- Patient ----
        for i, line in enumerate(lines_stripped):
            if line.startswith("Patient:"):
                name_part = line[len("Patient:"):].strip()
                if name_part:
                    rx_base.patient.full_name = name_part
                    if "," in name_part:
                        parts = [p.strip() for p in name_part.split(",", 1)]
                        rx_base.patient.last_name = parts[0]
                        rx_base.patient.first_name = parts[1] if len(parts) > 1 else ""
                    else:
                        name_parts = name_part.split()
                        if len(name_parts) >= 2:
                            rx_base.patient.first_name = name_parts[0]
                            rx_base.patient.last_name = " ".join(name_parts[1:])
                break

        # DOB — may be on same line or next line
        for i, line in enumerate(lines_stripped):
            if line.startswith("DOB:"):
                dob_val = line[len("DOB:"):].strip()
                if not dob_val and i + 1 < len(lines_stripped):
                    dob_val = lines_stripped[i + 1].strip()
                dob_m = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", dob_val)
                if dob_m:
                    rx_base.patient.dob = dob_m.group(1)
                break

        # Gender — may be "Gender: M" or "Gender M" on same line or separate
        for i, line in enumerate(lines_stripped):
            gm = re.match(r"Gender[:\s]+([MF])", line)
            if gm:
                rx_base.patient.gender = gm.group(1)
                break

        # Address — value may be on same line or next lines
        for i, line in enumerate(lines_stripped):
            if line.startswith("Address:"):
                addr_val = line[len("Address:"):].strip()
                # Grab continuation lines (city/state/zip)
                addr_lines = [addr_val] if addr_val else []
                for j in range(i + 1, min(i + 4, len(lines_stripped))):
                    nxt = lines_stripped[j]
                    # Stop at next field label or empty context
                    if not nxt or nxt.startswith(("Phone", "DOB", "Patient", "The patient", "If you")):
                        break
                    addr_lines.append(nxt)
                full_addr = " ".join(addr_lines).strip()
                rx_base.patient.address = full_addr
                # Extract city/state/zip
                csz = re.search(r"([A-Za-z\s]+),\s*([A-Z]{2}),?\s*(\d{5,9})", full_addr)
                if csz:
                    rx_base.patient.city = csz.group(1).strip()
                    rx_base.patient.state = csz.group(2)
                    rx_base.patient.zip_code = csz.group(3)
                    city_idx = full_addr.find(csz.group(1))
                    if city_idx > 0:
                        rx_base.patient.address = full_addr[:city_idx].strip().rstrip(",")
                break

        # Phone — value may be on same line or next line
        for i, line in enumerate(lines_stripped):
            if line.startswith("Phone:") or line.startswith("Phone "):
                phone_val = re.sub(r"^Phone[:\s]*", "", line).strip()
                if not phone_val and i + 1 < len(lines_stripped):
                    phone_val = lines_stripped[i + 1].strip()
                # Clean up phone
                digits = re.sub(r"[^0-9]", "", phone_val)
                if len(digits) >= 10:
                    rx_base.patient.phone = f"({digits[:3]}){digits[3:6]}-{digits[6:10]}"
                elif digits:
                    rx_base.patient.phone = phone_val
                break

        # ---- ICD/Diagnosis codes ----
        icd_codes = set()
        # Common false positives to skip
        _ICD_SKIP = {"NY", "NP", "MD", "DO", "FL", "PA", "NJ", "CT", "VA", "OR", "IN", "OH", "OK"}
        for idx, line in enumerate(lines_stripped):
            # Check for "Current Diagnosis Codes on File:" header — grab codes from following lines
            if "diagnosis codes on file" in line.lower():
                for k in range(idx + 1, min(idx + 6, len(lines_stripped))):
                    nxt = lines_stripped[k]
                    if not nxt or nxt.startswith(("Thank", "DME", "****", "Please")):
                        break
                    for cm in re.finditer(r"\b([A-Z]\d{2,3}\.?\d{1,4})\b", nxt):
                        code = cm.group(1).upper()
                        if code not in _ICD_SKIP:
                            if "." not in code and len(code) > 3:
                                code = code[:3] + "." + code[3:]
                            icd_codes.add(code)
                continue
            # Look for standalone ICD codes like "R39.81" or after "ATTENTION:" or "Diag:"
            for m in re.finditer(r"\b([A-Z]\d{2,3}\.?\d{0,4})\b", line):
                code = m.group(1).upper()
                # Must look like a real ICD code (letter + 2-3 digits + optional decimal)
                if re.match(r"^[A-Z]\d{2,3}(\.\d{1,4})?$", code) and code not in _ICD_SKIP:
                    if "." not in code and len(code) > 3:
                        code = code[:3] + "." + code[3:]
                    icd_codes.add(code)
        rx_base.icd_codes = sorted(icd_codes)

        # ---- Rx date ----
        eff_match = re.search(r"Eff\.?\s*Date:\s*(\d{1,2}/\d{1,2}/\d{4})", text)
        if eff_match:
            rx_base.rx_date = eff_match.group(1)
        else:
            dates = re.findall(r"\d{1,2}/\d{1,2}/\d{4}", text)
            # Use the last date that isn't the DOB
            for d in reversed(dates):
                if d != rx_base.patient.dob:
                    rx_base.rx_date = d
                    break

        # ---- Items from bullet points ----
        # Look for "• ITEM NAME" followed by "Qty/Month: N" or "Qty: N (Refills: R)"
        items: List[ParsedRxItem] = []
        for i, line in enumerate(lines_stripped):
            if line.startswith("•") or line.startswith("·") or line.startswith("-  "):
                item_name = re.sub(r"^[•·\-]\s*", "", line).strip()
                if not item_name:
                    continue
                item = ParsedRxItem(drug_name=item_name)
                # Look ahead for Qty/Month or Qty: N (Refills: R)
                for j in range(i + 1, min(i + 3, len(lines_stripped))):
                    qty_m = re.match(r"Qty(?:/Month)?:\s*([\d,.]+)", lines_stripped[j])
                    if qty_m:
                        try:
                            item.quantity = float(qty_m.group(1).replace(",", ""))
                        except ValueError:
                            item.quantity = 0
                        # Extract refills from same line: (Refills: N)
                        refill_m = re.search(r"\(Refills:\s*(\d+)\)", lines_stripped[j])
                        if refill_m:
                            item.refills = int(refill_m.group(1))
                        elif "OUT OF REFILLS" in lines_stripped[j].upper():
                            item.refills = 0
                        break
                items.append(item)

        # Also try "Drug:" format as fallback within fax text
        if not items:
            for m in self._PAT_DRUG.finditer(text):
                item = ParsedRxItem(drug_name=m.group(1).strip())
                items.append(item)

        # Create one ParsedRx per item (all share same patient/prescriber)
        results: List[ParsedRx] = []
        if items:
            for item in items:
                rx = ParsedRx(
                    patient=rx_base.patient,
                    prescriber=rx_base.prescriber,
                    item=item,
                    icd_codes=rx_base.icd_codes,
                    rx_date=rx_base.rx_date,
                    source_text=text,
                )
                results.append(rx)
        elif rx_base.patient.last_name:
            # No items found but we have patient data — return what we have
            results.append(rx_base)

        return results

    # ------------------------------------------------------------------ PDF text extraction

    @staticmethod
    def _extract_pdf_text(pdf_path: str) -> str:
        """Extract text from PDF using available library."""
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Try PyMuPDF (fitz) first — fastest and most reliable
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(path))
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            if text.strip():
                return text
        except ImportError:
            pass

        # Try pdfplumber
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(str(path)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                return text
        except ImportError:
            pass

        # Try pdfminer
        try:
            from pdfminer.high_level import extract_text
            text = extract_text(str(path))
            if text.strip():
                return text
        except ImportError:
            pass

        # Try PyPDF2 as last resort
        try:
            import PyPDF2
            with open(str(path), "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except ImportError:
            pass

        raise ImportError(
            "No PDF library available. Install one of: "
            "PyMuPDF (pip install PyMuPDF), "
            "pdfplumber (pip install pdfplumber), "
            "pdfminer (pip install pdfminer.six), "
            "or PyPDF2 (pip install PyPDF2)"
        )


# ═══════════════════════════════════════════════════════════════════
# Convenience function
# ═══════════════════════════════════════════════════════════════════

def parse_rx_file(pdf_path: str) -> List[ParsedRx]:
    """Parse an Rx PDF and return structured data."""
    return RxParser().parse_pdf(pdf_path)
