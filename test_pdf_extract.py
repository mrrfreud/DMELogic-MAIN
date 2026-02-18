import fitz
import glob

# Find the file
matches = glob.glob(r"C:\FaxManagerData\FaxManagerData\Faxes OCR'd\R\RIVERA-CRUZ*DIAPERS*.pdf")
if not matches:
    print("PDF not found!")
else:
    path = matches[0]
    print(f"File: {path}")
    doc = fitz.open(path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    print(f"Text length: {len(text)}")
    print("=== RAW TEXT ===")
    print(repr(text[:4000]))
    print()
    print("=== READABLE ===")
    print(text[:4000])

    # Now test the parser
    from dmelogic.services.rx_parser import RxParser
    parser = RxParser()
    results = parser.parse_pdf(path)
    print(f"\n=== PARSE RESULTS: {len(results)} blocks ===")
    for i, rx in enumerate(results):
        print(f"  Rx {i+1}:")
        print(f"    Patient: [{rx.patient.last_name}], [{rx.patient.first_name}]")
        print(f"    DOB: [{rx.patient.dob}]")
        print(f"    Gender: [{rx.patient.gender}]")
        print(f"    Address: [{rx.patient.address}]")
        print(f"    City/St/Zip: [{rx.patient.city}], [{rx.patient.state}], [{rx.patient.zip_code}]")
        print(f"    Phone: [{rx.patient.phone}]")
        print(f"    Prescriber: [{rx.prescriber.last_name}], [{rx.prescriber.first_name}] ({rx.prescriber.title})")
        print(f"    NPI: [{rx.prescriber.npi}]")
        print(f"    Drug: [{rx.item.drug_name}]")
        print(f"    Qty: [{rx.item.quantity}]")
        print(f"    Refills: [{rx.item.refills}]")
        print(f"    Days: [{rx.item.days_supply}]")
        print(f"    Sig: [{rx.item.directions}]")
        print(f"    ICD: {rx.icd_codes}")
        print(f"    Rx Date: [{rx.rx_date}]")
