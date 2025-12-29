import sqlite3
import shutil
from pathlib import Path

DB_PATH = r'C:\FaxManagerData\Data\patients.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Check counts
cur.execute("SELECT COUNT(*) FROM patients WHERE primary_insurance = 'EPACES MANUAL BILLIN DME'")
primary_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM patients WHERE secondary_insurance = 'EPACES MANUAL BILLIN DME'")
secondary_count = cur.fetchone()[0]

print(f"\nFound {primary_count} primary + {secondary_count} secondary = {primary_count + secondary_count} total records")

if primary_count + secondary_count > 0:
    # Backup
    backup = Path(DB_PATH).with_suffix('.db.backup4')
    shutil.copy2(DB_PATH, backup)
    print(f"Backup created: {backup}")
    
    # Update
    cur.execute("UPDATE patients SET primary_insurance = 'EPACES' WHERE primary_insurance = 'EPACES MANUAL BILLIN DME'")
    p_updated = cur.rowcount
    
    cur.execute("UPDATE patients SET secondary_insurance = 'EPACES' WHERE secondary_insurance = 'EPACES MANUAL BILLIN DME'")
    s_updated = cur.rowcount
    
    conn.commit()
    
    print(f"\n✅ Updated {p_updated} primary + {s_updated} secondary = {p_updated + s_updated} total records")
    print("✅ All 'EPACES MANUAL BILLIN DME' entries changed to 'EPACES'")
else:
    print("✅ No records to update")

conn.close()
